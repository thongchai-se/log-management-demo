# สถาปัตยกรรมระบบ

## ภาพรวม

Log Management Demo เป็นระบบ SIEM-lite ที่รวม ingest, normalize, ค้นหา และแสดงผลในสแต็กเดียว:

```text
แหล่งข้อมูล (Syslog UDP / HTTP JSON / File batch)
        │
        ▼
┌───────────────────┐
│  FastAPI Backend  │  AuthN/AuthZ · Normalize · Alert · Retention
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│    OpenSearch     │  Index `logs` · keyword mapping · ลบตามอายุ retention
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  React Dashboard  │  Overview · Logs · Alerts · Ingest (admin)
└───────────────────┘
```

ขอบ Appliance / SaaS:

```text
Client ──HTTPS:443──► Nginx (TLS) ──► Frontend (static)
                              └──/api──► Backend :8000
Syslog UDP :5514 ─────────────────────► Backend
```

## เหตุผลในการเลือกสแต็ก

| ชั้น | เทคโนโลยี | เหตุผล |
|------|-----------|--------|
| Ingest + API | FastAPI | พัฒนาเร็ว มี OpenAPI และสคีมาแบบ typed |
| ที่เก็บค้นหา | OpenSearch | full-text และ aggregation สำหรับ Top-N / timeline |
| UI | React + Recharts | คอนโซลปฏิบัติการที่เบา ไม่ผูกกับ Grafana |
| แพ็กเกจ | Docker Compose | รันบนเครื่องเดียว (Appliance) หรือ VM คลาวด์ (SaaS) |
| TLS | Nginx + self-signed หรือใบรับรองจริง | รองรับ HTTPS ในโหมด SaaS |

## Data flow

1. **Syslog** — รับ UDP ที่ `:5514` แปลงข้อความ `key=value` → normalize → เก็บเข้า index
2. **HTTP ingest** — `POST /api/ingest` (admin) รับ JSON; `POST /api/ingest/batch` อัปโหลดไฟล์ JSON (เช่น AWS / M365 / AD / CrowdStrike)
3. **Normalize** — แมปทุกแหล่งเข้า schema กลาง (`@timestamp`, `tenant`, `source`, `severity`, `src_ip`, `user`, `cloud.*`, `raw`, `_tags`, …)
4. **Index** — เก็บใน OpenSearch index `logs` พร้อม mapping ที่กำหนดไว้
5. **Query** — `/api/logs`, `/api/dashboard` (aggregations), `/api/alerts` (กฎ login ล้มเหลวซ้ำ)
6. **UI** — ส่งโทเคนในหัว `Authorization` และกรองตาม tenant / source / ช่วงเวลา

## โมเดล Tenant

| บทบาท | ขอบเขต tenant |
|--------|----------------|
| `admin` | เข้าถึงทุก tenant (`tenant` ใน query เป็นตัวเลือก) |
| `viewer` | จำกัดเฉพาะ tenant จาก claim (`demoA`) ไม่สามารถอ่านข้ามได้ |

การแยกข้อมูลบังคับที่ `resolve_tenant()` บนทุกเส้นทางอ่าน Ingest จำกัดเฉพาะ admin

บัญชีเดโม:

- `admin` / `admin123` — role admin, tenant `null`
- `viewer` / `viewer123` — role viewer, tenant `demoA`

## การแจ้งเตือน (Alert)

กฎ **`login_failed_same_ip`**:

- หน้าต่างเวลา: N นาทีล่าสุด (ค่าเริ่มต้น 5)
- เงื่อนไข: มีอย่างน้อย N อีเวนต์ (ค่าเริ่มต้น 3) ที่ `event_type` เป็น `app_login_failed` / `LogonFailed` หรือ `action=login_failed` จาก `src_ip` เดียวกัน
- การส่งผล: แท็บ Alerts ใน UI; webhook เป็นตัวเลือกผ่าน `ALERT_WEBHOOK_URL` และพารามิเตอร์ `?notify=true`

## Retention

- ค่าเริ่มต้น **7 วัน** (`RETENTION_DAYS`)
- worker พื้นหลังลบเอกสารที่ `@timestamp` เก่ากว่า cutoff ด้วย `delete_by_query`
- เรียกด้วยมือ: `POST /api/admin/retention/purge`

## หมายเหตุด้านความปลอดภัย

- Auth โหมดเดโมใช้โทเคนแบบ opaque (`demo-token-<user>`) เหมาะกับการสาธิต ไม่ใช่ระบบ IdP ระดับโปรดักชัน
- TLS ยุติที่ Nginx; backend อยู่ใน Docker network ภายใน
- CORS ปรับผ่าน `CORS_ORIGINS`
