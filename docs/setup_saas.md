# ติดตั้งโหมด SaaS / คลาวด์

เป้าหมาย: ให้บริการผ่าน URL HTTPS ที่เข้าถึงได้จากภายนอก

## รูปแบบที่แนะนำ

1. สร้าง VM คลาวด์ (Ubuntu 22.04+, 4 vCPU / 8 GB RAM) เช่น AWS Lightsail/EC2, Azure VM, GCP หรือ DigitalOcean
2. เปิดไฟร์วอลล์ / Security Group:
   - TCP **80**, **443**
   - UDP **5514** (รับ syslog)
3. ติดตั้ง Docker และ Docker Compose
4. Clone ที่เก็บโค้ดนี้
5. ใช้ใบรับรองจริง หรือ self-signed พร้อมระบุขั้นตอนยอมรับคำเตือนในเบราว์เซอร์

## Deploy

```bash
git clone <repository-url> log-management-demo
cd log-management-demo
cp .env.example .env
# ทางเลือก: ALERT_WEBHOOK_URL=https://example.com/hooks/alerts

chmod +x run.sh deploy/nginx/generate-certs.sh
./run.sh
```

ชี้เรคคอร์ด DNS ชนิด `A` (เช่น `logs.example.com`) ไปยัง IP สาธารณะของ VM

### TLS ด้วย Let's Encrypt (ทางเลือก)

1. ติดตั้ง certbot บนโฮสต์
2. ขอใบรับรองสำหรับโดเมน
3. วางไฟล์เป็น `deploy/nginx/certs/server.crt` และ `server.key` (หรือปรับ path ใน `deploy/nginx/nginx.conf`)
4. `docker compose restart nginx`

หากใช้ self-signed ชั่วคราว เบราว์เซอร์จะแสดงคำเตือน — เลือก Advanced → Proceed เพื่อเข้าใช้งาน

## การตั้งค่าฐาน API ของ Frontend

ใน Compose ฝั่ง frontend ถูก build ด้วย `VITE_API_URL=""` เพื่อให้เรียก `/api/...` บนโดเมนเดียวกันผ่าน Nginx

หากแยก hostname ของ API ให้ rebuild ดังนี้:

```bash
docker compose build --build-arg VITE_API_URL=https://api.example.com frontend
docker compose up -d
```

จากนั้นตั้งค่า `CORS_ORIGINS` ให้สอดคล้องกับโดเมน UI

## ทดสอบจากภายนอก

```bash
curl -sk https://<public-host>/health
curl -sk -X POST https://<public-host>/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}'
```

ส่ง syslog จากเครื่องลูกข่าย:

```bash
python sample/send_syslog.py   # ปรับ HOST เป็น IP หรือโดเมนเป้าหมาย
# หรือ
bash sample/send_syslog.sh <public-host> 5514
```

## ข้อมูลที่ควรเตรียมไว้สำหรับผู้ใช้งานภายนอก

1. URL สาธารณะ: `https://…`
2. บัญชีเดโม (admin และ viewer)
3. หมายเหตุประเภทใบรับรอง (self-signed หรือ Let's Encrypt)
4. ตัวอย่าง flow: ingest → search → dashboard → alert
5. ลิงก์ที่เก็บโค้ดและ Postman collection ใน `postman/`

## เช็กลิสต์ hardening

- [ ] เปลี่ยนรหัสผ่านเดโม หรือโหลดจาก secrets
- [ ] จำกัด SSH ตาม IP ที่อนุญาต
- [ ] ใช้ใบรับรอง TLS จริง
- [ ] ไม่เผยพอร์ต OpenSearch `:9200` สู่สาธารณะ
- [ ] ตั้งค่า `ALERT_WEBHOOK_URL` สำหรับสภาพแวดล้อมจริง
