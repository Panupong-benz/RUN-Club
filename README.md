# GEO RUN CLUB 🏃

แอพวางแผนเส้นทางวิ่งวงกลมในกรุงเทพฯ ด้วย Agentic AI (Claude Haiku)

## วิธีติดตั้งและรัน

### สิ่งที่ต้องติดตั้งก่อน
- Python 3.12+
- Node.js 20+ → ดาวน์โหลดที่ https://nodejs.org/
- Anthropic API Key → สมัครที่ https://console.anthropic.com/

---

### 1. ตั้งค่า Backend

```bash
cd backend

# Copy ไฟล์ env แล้วใส่ API key
copy .env.example .env
# แก้ไข .env ใส่ ANTHROPIC_API_KEY=sk-ant-...

# ติดตั้ง dependencies
pip install -r requirements.txt

# รัน server
python -m uvicorn main:app --reload --port 8000
```

Backend จะรันที่ http://localhost:8000

---

### 2. ตั้งค่า Frontend

```bash
cd frontend

# ติดตั้ง dependencies (ต้องมี Node.js ก่อน)
npm install

# รัน dev server
npm run dev
```

Frontend จะรันที่ http://localhost:5173

---

## วิธีใช้งาน

1. เปิด http://localhost:5173
2. กด **📍 ใช้ GPS ปัจจุบัน** หรือกรอก Lat/Lon เอง
3. เลือก **ระยะทาง** หรือ **แคลอรี่** ที่ต้องการ
4. กด **🗺️ วางแผนเส้นทางวิ่ง**
5. รอ AI วางแผน (~10-20 วินาที)
6. เส้นทางจะปรากฏบนแผนที่พร้อม stats

---

## Architecture

```
React Frontend → FastAPI Backend → Claude Haiku Agent
                                        ↓
                               [generate_waypoints]  ← เปิดวงรีรอบจุดเริ่ม
                               [compute_route]       ← OSRM หาเส้นทางจริง
                               [adjust_waypoints]    ← ปรับถ้าระยะห่างจากเป้า
                               [calculate_calories]  ← คำนวณแคลอรี่ MET
                               [finalize_route]      ← สรุปผล
```

### ราคา API ต่อ 1 เส้นทาง
- Claude Haiku: ~$0.0003 (ประมาณ 1 สตางค์)
- OSRM public API: ฟรี
- Overpass API: ฟรี

---

## โครงสร้างไฟล์

```
GEO RUN CLUB/
├── backend/
│   ├── main.py                  ← FastAPI app
│   ├── requirements.txt
│   ├── agent/
│   │   ├── orchestrator.py      ← Claude Haiku agentic loop
│   │   └── tools/
│   │       ├── waypoint_gen.py  ← Ellipse algorithm
│   │       ├── route_compute.py ← OSRM client
│   │       └── calorie_calc.py  ← MET formula
│   └── models/
│       ├── request.py
│       └── response.py
└── frontend/
    └── src/
        ├── App.tsx
        ├── components/
        │   ├── RunMap.tsx        ← Leaflet map
        │   ├── RouteForm.tsx     ← Input form
        │   └── StatsPanel.tsx   ← Distance/calorie display
        └── hooks/
            └── useGeolocation.ts
```
