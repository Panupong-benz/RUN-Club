import streamlit as st
import folium
from streamlit_folium import st_folium
import os
from dotenv import load_dotenv

load_dotenv()

# รับ API key จาก Streamlit Cloud secrets หรือ .env (local)
if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
if "OSRM_URL" in st.secrets:
    os.environ["OSRM_URL"] = st.secrets["OSRM_URL"]

from backend.agent.orchestrator import plan_route
from backend.agent.tools.calorie_calc import calories_to_distance

st.set_page_config(
    page_title="GEO RUN CLUB",
    page_icon="🏃",
    layout="wide",
)

st.title("🏃 GEO RUN CLUB")
st.caption("วางแผนเส้นทางวิ่งวงกลมในกรุงเทพฯ ด้วย AI (Gemini 1.5 Flash)")

# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.header("ตั้งค่าเส้นทาง")

    st.subheader("📍 ตำแหน่งเริ่มต้น")
    lat = st.number_input("Latitude", value=13.7294, format="%.5f", step=0.0001)
    lon = st.number_input("Longitude", value=100.5418, format="%.5f", step=0.0001)
    st.caption("ค่าเริ่มต้น = สวนลุมพินี กรุงเทพฯ")

    st.divider()
    st.subheader("🎯 เป้าหมาย")
    mode = st.radio("เลือกโหมด", ["📏 ระยะทาง (km)", "🔥 แคลอรี่ (kcal)"], index=0)

    if "ระยะทาง" in mode:
        target_km = st.slider("ระยะทาง (km)", 1.0, 30.0, 5.0, 0.5)
        target_calories = None
    else:
        target_calories = st.slider("แคลอรี่ (kcal)", 100, 1000, 300, 50)
        target_km = None

    st.divider()
    st.subheader("⚙️ ข้อมูลผู้วิ่ง")
    weight_kg = st.number_input("น้ำหนัก (kg)", 30, 200, 65)
    pace = st.number_input("เพซ (นาที/km)", 3.0, 15.0, 7.0, 0.5)

    st.divider()
    run_btn = st.button("🗺️ วางแผนเส้นทางวิ่ง", type="primary", use_container_width=True)

# ── Layout ─────────────────────────────────────────────────────
col_map, col_stats = st.columns([2, 1])

def make_base_map(center_lat: float, center_lon: float) -> folium.Map:
    m = folium.Map(location=[center_lat, center_lon], zoom_start=14)
    folium.Marker(
        [center_lat, center_lon],
        popup="จุดเริ่มต้น",
        icon=folium.Icon(color="green", icon="play"),
    ).add_to(m)
    return m

with col_map:
    map_slot = st.empty()

with col_stats:
    stats_slot = st.empty()

# Default map
with map_slot:
    st_folium(make_base_map(lat, lon), width=None, height=520, key="map_default")

# ── Generate route ─────────────────────────────────────────────
if run_btn:
    if not os.getenv("GOOGLE_API_KEY"):
        st.error("❌ ไม่พบ GOOGLE_API_KEY — กรุณาตั้งค่าใน Streamlit Secrets หรือไฟล์ .env")
        st.stop()

    final_km = (
        calories_to_distance(target_calories, weight_kg, pace)
        if target_calories is not None
        else target_km
    )

    with st.spinner(f"⏳ Gemini AI กำลังวางแผนเส้นทาง {final_km:.1f} km... (~15 วินาที)"):
        try:
            result = plan_route(
                lat=lat,
                lon=lon,
                target_km=final_km,
                weight_kg=weight_kg,
                pace_min_per_km=pace,
            )
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาด: {e}")
            st.stop()

    # Draw route
    m = make_base_map(lat, lon)
    line_coords = [[pt[1], pt[0]] for pt in result.geometry]  # [lon,lat] → [lat,lon]

    folium.PolyLine(line_coords, color="#16a34a", weight=5, opacity=0.85, tooltip="เส้นทางวิ่ง").add_to(m)

    for i, wp in enumerate(result.waypoints):
        folium.CircleMarker(
            [wp.lat, wp.lon], radius=6,
            color="#15803d", fill=True, fill_color="#22c55e",
            tooltip=f"จุดที่ {i+1}",
        ).add_to(m)

    if line_coords:
        lats = [p[0] for p in line_coords]
        lons = [p[1] for p in line_coords]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])

    with map_slot:
        st_folium(m, width=None, height=520, key="map_route")

    with stats_slot:
        st.success("✅ วางแผนสำเร็จ!")
        st.metric("📏 ระยะทาง", f"{result.total_km} km")
        st.metric("🔥 แคลอรี่", f"{int(result.estimated_calories)} kcal")
        st.metric("⏱️ เวลา", f"{result.estimated_minutes} นาที")
        st.info(f"**AI แนะนำ:** {result.agent_summary}")
