# คู่มือ Postman / Insomnia

นำเข้าไฟล์ `Log_Management_Demo.postman_collection.json` ใน Postman หรือ Insomnia

## Login

`POST {{baseUrl}}/api/auth/login`  
JSON: `{"username":"admin","password":"admin123"}`

## Ingest

`POST {{baseUrl}}/api/ingest`  
Auth: Bearer `{{token}}`  
JSON: ดูตัวอย่างใน `sample/api_login_failed.json`

## ค้นหา

`GET {{baseUrl}}/api/logs?tenant=demoA&size=20`

## Dashboard

`GET {{baseUrl}}/api/dashboard?tenant=demoA`

## Alerts

`GET {{baseUrl}}/api/alerts?window_minutes=5&min_count=3`

ค่าเริ่มต้นของ `baseUrl`: `http://127.0.0.1:8000`  
API ต้องพร้อมใช้งานก่อนเรียกคอลเลกชัน
