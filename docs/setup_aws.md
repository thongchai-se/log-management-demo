# ติดตั้งบน AWS (Free Tier / EC2)

คู่มือนี้สำหรับขึ้นโหมด SaaS บน AWS หลังสมัครบัญชีแล้ว

## สำคัญเรื่องขนาดเครื่อง

สแต็กนี้มี OpenSearch + Backend + Frontend + Nginx

| Instance | RAM | ใช้ได้ไหม |
|----------|-----|-----------|
| **t2.micro / t3.micro** (Free Tier) | 1 GB | มักไม่พอ / OOM |
| **t3.small** (แนะนำสำหรับเดโม) | 2 GB | ใช้ได้ถ้ารีดเมม OpenSearch |
| **t3.medium** หรือใหญ่กว่า | 4–8 GB | สบาย |


แนะนำ: ใช้ **Ubuntu 22.04 + t3.small** ช่วงเดโมสั้นๆ (ค่าใช้จ่ายต่ำ)  
ถ้าต้องยึด Free Tier จริงๆ ให้ทำตามหัวข้อ “ลด RAM OpenSearch” ด้านล่างและสร้าง **swap 2 GB**

อย่าเปิด Security Group ให้พอร์ต **9200** ออกอินเทอร์เน็ต

---

## 1) สร้าง EC2

1. AWS Console → **EC2** → **Launch instance**
2. Name: `log-management-demo`
3. AMI: **Ubuntu Server 22.04 LTS**
4. Instance type: **t3.small** (หรือ t3.micro ถ้าทดลอง Free Tier)
5. Key pair: สร้างใหม่ แล้วโหลดไฟล์ `.pem` เก็บดีๆ
6. Network → Security Group อนุญาต:

| Type | Port | Source |
|------|------|--------|
| SSH | 22 | My IP (แนะนำ) |
| HTTP | 80 | 0.0.0.0/0 |
| HTTPS | 443 | 0.0.0.0/0 |
| Custom UDP | 5514 | 0.0.0.0/0 (ถ้าจะเดโม syslog จากภายนอก) |

7. Storage: 20–30 GB gp3
8. Launch → รอสถานะ **Running** → คัดลอก **Public IPv4**

(ทางเลือก) สร้าง **Elastic IP** แล้ว Associate กับ instance เพื่อไม่ให้ IP เปลี่ยนตอนหยุดเครื่อง

---

## 2) SSH เข้าเครื่อง

จาก Windows (PowerShell) — แก้ path ของ `.pem` และ IP:

```powershell
ssh -i "C:\path\to\your-key.pem" ubuntu@<PUBLIC_IP>
```

ครั้งแรกพิมพ์ `yes` แล้วรอเข้า shell

---

## 3) ติดตั้ง Docker

รันบน EC2:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker ubuntu
```

ออกจาก SSH แล้วเข้าใหม่ เพื่อให้กลุ่ม `docker` มีผล:

```powershell
ssh -i "C:\path\to\your-key.pem" ubuntu@<PUBLIC_IP>
docker version
```

### (แนะนำถ้าเครื่องเล็ก) สร้าง swap 2 GB

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
```

---

## 4) ดึงโปรเจกต์แล้วรัน

### แบบมี GitHub repo สาธารณะ/ที่ SSH ได้

```bash
git clone <REPOSITORY_URL> log-management-demo
cd log-management-demo
```

### แบบยังไม่มี remote — อัปโหลดจากเครื่อง Windows

บนเครื่องคุณ (โฟลเดอร์โปรเจกต์):

```powershell
tar --exclude=backend/venv --exclude=client/node_modules --exclude=.git -czf log-demo.tgz .
scp -i "C:\path\to\your-key.pem" log-demo.tgz ubuntu@<PUBLIC_IP>:~
```

บน EC2:

```bash
mkdir -p log-management-demo && cd log-management-demo
tar -xzf ~/log-demo.tgz
```

### ลด RAM OpenSearch (จำเป็นบน t3.small / micro)

แก้ใน `docker-compose.yml` บรรทัด `OPENSEARCH_JAVA_OPTS` เป็น:

```yaml
- OPENSEARCH_JAVA_OPTS=-Xms256m -Xmx256m
```

และคอมเมนต์หรือลบการ map พอร์ต `9200:9200` ออกจาก service `opensearch` (ไม่ควรเปิดออกเน็ต)

### สตาร์ทระบบ

```bash
chmod +x run.sh deploy/nginx/generate-certs.sh sample/send_syslog.sh
./run.sh
```

ดูสถานะ:

```bash
docker compose ps
docker compose logs -f --tail=50
```

รอจน `opensearch` healthy และ `backend` / `nginx` เป็น `Up`

---

## 5) เปิดจากภายนอก

เบราว์เซอร์:

```text
https://<PUBLIC_IP>
```

จะเจอคำเตือน self-signed → **Advanced → Proceed**

บัญชีเดโม:

- `admin` / `admin123`
- `viewer` / `viewer123`

ตรวจ API:

```bash
curl -sk https://<PUBLIC_IP>/health
```

Seed ข้อมูล (บน EC2 หรือจากเครื่องคุณชี้มาที่ IP):

```bash
# บน EC2 — ติดตั้ง python ชั่วคราวแล้วยิงเข้า localhost ผ่าน nginx ยากกว่า
# ง่ายสุด: ใช้ UI แท็บ Ingest อัปโหลดไฟล์ sample/*.json
```

หรือจากเครื่องคุณแก้ `API_URL` ในสคริปต์เป็น `https://<PUBLIC_IP>` แล้วปิด verify SSL ชั่วคราว / ใช้ UI

---

## 6) ข้อมูลสำหรับผู้ทดสอบภายนอก

1. URL: `https://<PUBLIC_IP>` (หรือโดเมนถ้ามี)
2. บัญชี admin / viewer
3. หมายเหตุ: ใช้ **self-signed TLS** — เบราว์เซอร์จะเตือน ต้องกด Advanced → Proceed
4. ลิงก์ Git repository + วิธี Appliance ใน `docs/setup_appliance.md`

---

## แก้ปัญหาเร็ว

| อาการ | ตรวจ |
|--------|------|
| เปิดเว็บไม่ได้ | Security Group 80/443, instance Running, `docker compose ps` |
| OpenSearch ไม่ขึ้น / ฆ่าคอนเทนเนอร์ | RAM ไม่พอ → ลด heap เป็น 256m + เปิด swap หรืออัปเป็น t3.small |
| SSH ไม่ได้ | SG พอร์ต 22 จำกัด My IP, ใช้ user `ubuntu` |
| ใบรับรองเตือน | ปกติของ self-signed |
| ค่าใช้จ่าย | หยุด instance หลังเดโม: EC2 → Stop (หรือ Terminate ถ้าไม่ใช้แล้ว) |

หยุดเพื่อประหยัดเงิน:

```text
EC2 → Instances → Stop instance
```

อย่าลืมปล่อย Elastic IP ถ้าไม่ได้ผูกกับ instance (IP ว่างมีค่าใช้จ่าย)
