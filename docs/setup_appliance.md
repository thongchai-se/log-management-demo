# ติดตั้งโหมด Appliance (เครื่องเดียว / VM)

ข้อกำหนดแนะนำ: Ubuntu 22.04+ หรือ Windows พร้อม Docker Desktop, 4 vCPU / 8 GB RAM / 40 GB disk

## สิ่งที่ต้องมี

- Docker Engine + Docker Compose v2
- (ทางเลือก) Python 3.12+ สำหรับสคริปต์ seed และชุดทดสอบ
- พอร์ต: **80, 443, 5514/udp** (และ 8000/9200 เมื่อใช้โหมดพัฒนา)

## เริ่มต้นด้วยคำสั่งเดียว

### Linux / macOS / WSL / Git Bash

```bash
chmod +x run.sh deploy/nginx/generate-certs.sh sample/send_syslog.sh
./run.sh
```

### Windows PowerShell

```powershell
cd <repo-root>
.\run.ps1
```

คำสั่งเทียบเท่า:

```bash
docker compose up -d --build
```

ครั้งแรกของระบบจะสร้างใบรับรอง **self-signed** ที่ `deploy/nginx/certs/`

## ตรวจสอบสถานะ

| รายการ | URL / คำสั่ง |
|--------|----------------|
| UI | https://localhost (เลือก Proceed หากเบราว์เซอร์เตือนใบรับรอง) |
| Health | https://localhost/health |
| API docs | https://localhost/docs |
| OpenSearch | http://127.0.0.1:9200 |

บัญชีเดโม:

- Admin: `admin` / `admin123`
- Viewer: `viewer` / `viewer123` (จำกัด tenant `demoA`)

## โหลดข้อมูลตัวอย่าง (Seed)

API ต้องพร้อมใช้งานที่พอร์ต `8000` หรือผ่าน HTTPS ของ Nginx ก่อนรันสคริปต์

จากโฟลเดอร์รากของโปรเจกต์:

```powershell
cd <repo-root>
backend\venv\Scripts\python.exe sample\post_logs.py
backend\venv\Scripts\python.exe sample\seed_alerts.py
backend\venv\Scripts\python.exe sample\send_syslog.py
```

หรืออัปโหลดไฟล์จาก `sample/` ผ่าน UI (บทบาท admin → แท็บ **Ingest**)

หลังจากนั้นหน้า Overview / Logs / Alerts จะแสดงข้อมูลภายในเวลาไม่กี่วินาทีถึงหนึ่งนาที

## Smoke test

1. สตาร์ทระบบด้วย `.\run.ps1` หรือ `./run.sh` (หรือโหมดพัฒนาด้านล่าง)
2. ส่ง syslog แล้วตรวจอีเวนต์ firewall ใน Logs
3. เรียก `POST /api/ingest` หรือวาง JSON ใน UI แล้วค้นหาได้
4. อัปโหลด sample AWS / M365 / AD แล้วตรวจฟิลด์หลัง normalize
5. ตรวจ Dashboard: Top IP / User / EventType / Timeline และฟิลเตอร์
6. รัน `seed_alerts.py` แล้วตรวจแท็บ Alerts สำหรับกฎ `login_failed_same_ip`
7. ล็อกอินด้วย viewer แล้วตรวจว่าเห็นเฉพาะ `demoA`

## โหมดพัฒนาท้องถิ่น

ใช้สามเทอร์มินัลเมื่อยังไม่ต้องการ build compose ทั้งชุด:

```powershell
# เทอร์มินัล 1 — OpenSearch
cd <repo-root>
docker compose up -d opensearch

# เทอร์มินัล 2 — API
cd <repo-root>\backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# เทอร์มินัล 3 — UI
cd <repo-root>\client
copy .env.example .env
npm install
npm run dev
```

- UI: http://localhost:5173
- API docs: http://127.0.0.1:8000/docs

### การแก้ปัญหาเบื้องต้น

| อาการ | สาเหตุที่เป็นไปได้ | วิธีแก้ |
|--------|---------------------|---------|
| `ERR_CONNECTION_REFUSED` / WinError 10061 ที่พอร์ต 8000 | backend ยังไม่ทำงาน | สตาร์ท `uvicorn` หรือรัน `.\run.ps1` |
| ส่ง syslog สำเร็จแต่ไม่เห็นใน UI | ไม่มี listener หรือ backend ไม่ทำงาน | ตรวจสถานะ uvicorn / container backend |
| สคริปต์ path `backend\venv\...` ล้มเหลว | รันจากโฟลเดอร์ย่อย | กลับไปที่รากโปรเจกต์ก่อนรัน |
| OpenSearch สถานะ `Exited` | คอนเทนเนอร์หยุดหลังรีบูต | `docker compose up -d opensearch` |

## หยุดและรีเซ็ต

```powershell
docker compose down
# ล้างข้อมูลค้นหา:
docker compose down -v
curl -X DELETE http://127.0.0.1:9200/logs
```

## หมายเหตุเพิ่มเติม

- หาก aggregation ว่างหรือ mapping ไม่ตรงกับเวอร์ชันก่อนหน้า ให้ลบ index `logs` แล้วรีสตาร์ท backend
- หากพอร์ต 443 ถูกใช้งานอยู่ ให้ปรับพอร์ตใน `docker-compose.yml`
- หาก syslog ไม่เข้า ให้ตรวจ UDP `5514` และกฎไฟร์วอลล์ของโฮสต์
