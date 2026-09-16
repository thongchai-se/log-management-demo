# Log Management Demo

ระบบเก็บและค้นหา log ด้วย FastAPI + OpenSearch + React

## สิ่งที่ทำได้
- รับ log ผ่าน API (`POST /api/ingest`)
- ค้นหา / กรองตาม tenant
- Dashboard สรุปจำนวน
- Alerts ตาม severity
- Login แบบ demo token

## วิธีรัน

### 1) OpenSearch
```bash
docker compose up -d
```

### 2) Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
#### API docs: http://127.0.0.1:8000/docs

### 3) Frontend (client)
```bash
cd client
npm install
npm run dev
```
#### เปิด: http://localhost:5173

## Demo users
- admin / admin123
- analyst / analyst123
## โครงสร้างคร่าวๆ
- backend/app/routes = HTTP endpoints
- backend/app/services = logic คุย OpenSearch
- backend/app/schemas = ตรวจรูปแบบข้อมูล
- client/src = หน้าเว็บ

