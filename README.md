# Log Management Demo

ระบบจัดการ Log แบบ Full-stack: รับหลายแหล่งข้อมูล → normalize → OpenSearch → dashboard/alerts พร้อม RBAC Admin/Viewer และแพ็กเกจ Docker สำหรับโหมด Appliance และ SaaS (HTTPS)

## สแต็ก

- **Backend:** FastAPI (HTTP ingest, syslog UDP, retention, alerts)
- **Store:** OpenSearch 2.x
- **Frontend:** React + Vite + Recharts
- **Edge:** Nginx TLS reverse proxy

## เริ่มต้นเร็ว (Appliance)

```powershell
# Windows
.\run.ps1

# Linux/macOS/WSL
./run.sh
```

เปิด **https://localhost** (ยอมรับคำเตือน self-signed หากใช้ใบรับรองเดโม)

| ผู้ใช้ | รหัสผ่าน | ขอบเขต |
|--------|----------|--------|
| `admin` | `admin123` | ทุก tenant |
| `viewer` | `viewer123` | เฉพาะ `demoA` |

### เมื่อเชื่อมต่อไม่ได้ (Connection refused)

ตรวจสอบว่าบริการที่เกี่ยวข้องทำงานอยู่:

1. `docker compose ps` — OpenSearch ควรเป็นสถานะ `Up`
2. โหมดเต็มชุด: `.\run.ps1` หรือ `./run.sh`
3. โหมดพัฒนา: ดูขั้นตอนใน [docs/setup_appliance.md](docs/setup_appliance.md)

โหลดข้อมูลตัวอย่าง (รันจากโฟลเดอร์รากของโปรเจกต์ หลัง API พร้อมใช้งาน):

```powershell
backend\venv\Scripts\python.exe sample\post_logs.py
backend\venv\Scripts\python.exe sample\seed_alerts.py
backend\venv\Scripts\python.exe sample\send_syslog.py
```

## โครงสร้างโปรเจกต์

```text
backend/          FastAPI
client/           React UI
sample/           ไฟล์ตัวอย่างและสคริปต์ส่งข้อมูล
deploy/nginx/     พร็อกซี TLS
docs/             สถาปัตยกรรมและคู่มือติดตั้ง
tests/            ชุดทดสอบ pytest
postman/          API collection
docker-compose.yml
Makefile  run.sh  run.ps1  .env.example
```

## เอกสาร

- [สถาปัตยกรรมและ tenant model](docs/architecture.md)
- [ติดตั้งโหมด Appliance](docs/setup_appliance.md)
- [ติดตั้งโหมด SaaS / คลาวด์](docs/setup_saas.md)

## API (สรุป)

| Method | Path | รายละเอียด |
|--------|------|------------|
| POST | `/api/auth/login` | ออกโทเคนสำหรับเดโม |
| POST | `/api/ingest` | admin — รับ JSON รายการเดียว |
| POST | `/api/ingest/batch` | admin — อัปโหลดไฟล์ |
| GET | `/api/logs` | ค้นหาและกรอง |
| GET | `/api/dashboard` | Top IP/User/EventType และ timeline |
| GET | `/api/alerts` | กฎ login ล้มเหลวซ้ำจาก IP เดียวกัน |
| POST | `/api/admin/retention/purge` | ลบข้อมูลเก่ากว่าช่วง retention |

OpenAPI: http://127.0.0.1:8000/docs (หรือ https://localhost/docs เมื่อใช้ Nginx)

## การทดสอบ

```bash
docker compose up -d opensearch
cd backend && pip install -r requirements.txt
pytest ../tests -q
```

ชุดทดสอบครอบคลุม:

- Unit: normalize ทุกแหล่ง + sample fixtures, auth/RBAC helpers
- API: login, health, 401/403, viewer ห้าม ingest
- Integration (ต้องมี OpenSearch): ingest → search → dashboard, batch upload, alert rule, retention, tenant isolation

รายละเอียดดู `tests/README.md`

## ความสามารถหลัก

- รองรับหลายแหล่ง: syslog, HTTP API, file batch และสคริปต์ตัวอย่าง
- Normalize เป็น schema กลาง
- จัดเก็บและค้นหาด้วย OpenSearch
- Dashboard Top-N, timeline และฟิลเตอร์
- Alert ใน UI (webhook เป็นตัวเลือก)
- บทบาท Admin / Viewer และการแยก tenant
- Docker Compose สำหรับ Appliance
- เส้นทาง deploy SaaS พร้อม HTTPS
- Retention 7 วัน
- เอกสาร, `.env.example`, Makefile, samples, tests และ Postman collection

## License

ใช้สำหรับสาธิตและประเมินระบบ
