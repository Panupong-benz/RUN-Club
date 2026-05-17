# 🏃 GEO RUN CLUB

> AI-powered circular running route planner for Bangkok runners

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Claude](https://img.shields.io/badge/Claude_Haiku-Anthropic-D97706?style=for-the-badge)](https://anthropic.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

> ⚠️ **Class Project — Prototype Stage**  
> โปรเจคนี้เป็นส่วนหนึ่งของรายวิชา ENGINEERING APPLICATIONS OF ARTIFICIAL INTELLIGENCE 
> อยู่ในระดับ Prototype ยังไม่พร้อมสำหรับการใช้งานจริงในเชิงพาณิชย์  
> แต่สามารถนำ Architecture และ Codebase นี้ไปพัฒนาต่อได้

---

## 📌 ปัญหาที่แก้

นักวิ่งในกรุงเทพฯ มักวิ่งแค่สวนสาธารณะเดิมๆ เพราะไม่รู้ว่าจะวางแผนเส้นทางวิ่งวงกลมรอบบ้านยังไง — GEO RUN CLUB ใช้ AI วางแผนเส้นทางวงกลมให้อัตโนมัติ แค่บอกว่าอยู่ที่ไหนและอยากวิ่งกี่ km

---

## ✨ Features

| Feature | รายละเอียด |
|---|---|
| 🗺️ **AI Route Planner** | Claude Haiku วางแผนเส้นทางวิ่งวงกลมด้วย Agentic Tool Use |
| 📡 **GPS Detection** | ดึงตำแหน่ง GPS จริงจากเบราว์เซอร์ |
| 🌤️ **Weather + PM2.5** | แสดงสภาพอากาศและค่าฝุ่นก่อนออกวิ่ง |
| 🌙 **Night Running Mode** | AI เลือกถนนมีไฟ ใกล้ BTS และร้านสะดวกซื้อ 24 ชม. |
| 🔥 **Streak & Leaderboard** | ระบบ Streak รายวัน + จัดอันดับระยะทางรายสัปดาห์/ตลอดกาล |
| ❤️ **Saved Routes + QR Share** | บันทึกเส้นทางโปรด แชร์ให้เพื่อนผ่าน QR Code |
| 📅 **AI Training Plan** | วางแผนโปรแกรมฝึกวิ่งรายสัปดาห์ตามเป้าหมาย |
| 👥 **Group Meetup** | นัดวิ่งกลุ่ม ดูจุดนัดพร้อมแผนที่ |
| 🍽️ **Post-run Nutrition** | แนะนำโปรตีน/คาร์บหลังวิ่งตามแคลอรี่ที่เผาไป |
| ⚡ **Route Cache** | จำเส้นทางเดิมไว้ 6 ชม. โหลดซ้ำได้ทันที |

---

## 🏗️ Architecture

```
User (Browser)
    │
    ▼
Streamlit Frontend
    │
    ├── Claude Haiku Agent (Anthropic API)
    │       ├── Tool: generate_waypoints   → Ellipse algorithm (Python)
    │       ├── Tool: compute_route        → OSRM Public API
    │       ├── Tool: adjust_waypoints     → Scale correction loop
    │       ├── Tool: calculate_calories   → MET formula
    │       └── Tool: finalize_route       → Return result
    │
    ├── Overpass API (OpenStreetMap)  → ดึงข้อมูลสวน/ทางเท้าใกล้เคียง
    ├── Open-Meteo API                → สภาพอากาศ + PM2.5
    └── SQLite Database               → Profiles, Runs, Routes, Meetups
```

### Circular Route Algorithm

OSRM ทำได้แค่ A→B — แก้ด้วย **Waypoint Injection + Python Correction Loop**

```
1. คำนวณ radius = target_km / (2π)
2. วาง waypoints เป็นวงรีรอบจุดเริ่มต้น (พร้อม snap หาสวนสาธารณะใกล้เคียง)
3. เรียก OSRM: Start → W1 → W2 → W3 → W4 → Start
4. ตรวจสอบระยะทางจริง vs เป้าหมาย
5. Python loop ปรับ scale สูงสุด 5 รอบ จนได้ ±tolerance%
```

---

## 🛠️ Tech Stack

| Layer | เทคโนโลยี | เหตุผล |
|---|---|---|
| Frontend | Streamlit | Deploy ได้ฟรีบน Streamlit Cloud |
| AI Agent | Claude Haiku (`claude-haiku-4-5-20251001`) | ถูกกว่า Sonnet ~10x, เร็ว |
| Map | Folium + Leaflet.js | Open Source, OSM tiles ฟรี |
| Routing | OSRM Public API | ฟรี, ไม่ต้อง self-host |
| OSM Data | Overpass API | ฟรี, ข้อมูลสวน/ทางเท้า |
| Weather | Open-Meteo | ฟรี, ไม่ต้อง API Key |
| Database | SQLite | เพียงพอสำหรับ prototype |
| QR Code | qrcode[pil] | สร้าง QR แชร์เส้นทาง |

**ค่าใช้จ่าย API จริงต่อการสร้างเส้นทาง 1 ครั้ง ≈ $0.001–0.003 (~0.03–0.10 บาท)**

---

## 🚀 วิธีติดตั้งและรันในเครื่อง

### Prerequisites
- Python 3.12+
- Anthropic API Key ([สมัครได้ที่นี่](https://console.anthropic.com))

### Installation

```bash
# 1. Clone repo
git clone https://github.com/<your-username>/geo-run-club.git
cd geo-run-club

# 2. สร้าง virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

# 3. ติดตั้ง dependencies
pip install -r requirements.txt

# 4. ตั้งค่า API Key
# สร้างไฟล์ .env แล้วใส่:
# ANTHROPIC_API_KEY=sk-ant-...

# 5. รันแอพ
streamlit run streamlit_app.py
```

### Environment Variables

```bash
# .env (local) หรือ Streamlit Secrets (cloud)
ANTHROPIC_API_KEY=sk-ant-...        # จำเป็น
OSRM_URL=https://router.project-osrm.org  # default (public instance)
DAILY_ROUTE_LIMIT=10                # จำกัดเส้นทางต่อวันต่อคน
```

---

## 📁 โครงสร้างไฟล์

```
geo-run-club/
├── streamlit_app.py              ← Main app (UI + ทุก Tab)
├── requirements.txt
├── runtime.txt                   ← python-3.12
│
├── agent/
│   ├── orchestrator.py           ← Claude Haiku agentic loop (หัวใจหลัก)
│   └── tools/
│       ├── waypoint_gen.py       ← Ellipse waypoint + OSM snapping
│       ├── route_compute.py      ← OSRM HTTP client
│       ├── calorie_calc.py       ← MET formula
│       ├── weather.py            ← Open-Meteo integration
│       ├── air_quality.py        ← PM2.5 index
│       ├── nearby_places.py      ← Overpass API (ร้านอาหาร/น้ำ)
│       ├── nutrition.py          ← Post-run nutrition advice
│       └── training_plan.py      ← AI training plan generator
│
├── db/
│   └── stats.py                  ← SQLite CRUD (profiles, runs, routes, cache)
│
└── models/
    └── response.py               ← Pydantic RouteResponse model
```

---

## ⚠️ ข้อจำกัด (Prototype Stage)

โปรเจคนี้เป็น **Class Project** อยู่ในระดับ Prototype — มีข้อจำกัดหลายจุดก่อนนำไปใช้จริง

| จุดจำกัด | สาเหตุ | แนวทางแก้ใน Production |
|---|---|---|
| **Database** | ใช้ SQLite ไฟล์เดียว | เปลี่ยนเป็น PostgreSQL |
| **Authentication** | Login แค่ username ไม่มี password | เพิ่ม OAuth / JWT |
| **OSRM** | ใช้ public instance ที่ rate limit ต่ำ | Self-host Docker |
| **Route Quality** | บางพื้นที่ข้อมูล pedestrian ใน OSM ไม่ครบ | เพิ่ม road safety scoring |
| **Scalability** | Streamlit Cloud ฟรีมีข้อจำกัด resource | ย้ายไป FastAPI + React |

---

## 🔮 แนวทางพัฒนาต่อ

```
Prototype (ปัจจุบัน)
    │
    └── Production-Ready
            ├── SQLite → PostgreSQL + proper auth (OAuth/JWT)
            ├── Self-host OSRM Docker (Bangkok-specific data)
            ├── Redis Cache แทน SQLite route_cache
            ├── SSE Streaming — แสดง AI thinking แบบ real-time
            ├── Mobile App — React Native หรือ PWA
            ├── Road Safety Scoring — กรองถนนอันตราย/ไม่มีทางเท้า
            └── Freemium Model — ฟรี 5 เส้นทาง/วัน, Premium ไม่จำกัด
```

---

## 👨‍💻 ผู้พัฒนา

โปรเจคนี้จัดทำขึ้นเป็นส่วนหนึ่งของรายวิชา **ENGINEERING APPLICATIONS OF ARTIFICIAL INTELLIGENCE**

> *"จากไอเดียง่ายๆ ว่า นักวิ่งไม่รู้จะวิ่งเส้นทางไหน สู่ระบบ AI Agent ที่วางแผนเส้นทางวงกลมได้จริงในกรุงเทพฯ"*

---

## 📄 License

MIT License — ใช้และพัฒนาต่อได้อย่างอิสระ

---

<div align="center">
  <sub>Built with ❤️ using Claude AI + Streamlit + OpenStreetMap</sub>
</div>
