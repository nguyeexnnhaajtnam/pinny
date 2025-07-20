# Hướng dẫn kết nối Database với DBeaver

## 📋 Thông tin kết nối PostgreSQL

### **Thông tin cơ bản:**
- **Database Type**: PostgreSQL
- **Host**: localhost (hoặc IP server của bạn)
- **Port**: 5432 (port mặc định PostgreSQL)
- **Database Name**: pinny_db
- **Username**: postgres (hoặc username bạn đã tạo)
- **Password**: password của bạn

### **Connection String:**
```
postgresql://username:password@localhost:5432/pinny_db
```

## 🔧 Cách kết nối trong DBeaver

### **Bước 1: Tạo Connection mới**
1. Mở DBeaver
2. Click **"New Database Connection"** (icon dấu +)
3. Chọn **PostgreSQL**
4. Click **Next**

### **Bước 2: Nhập thông tin kết nối**
```
Server Host: localhost
Port: 5432
Database: pinny_db
Username: postgres
Password: [nhập password của bạn]
```

### **Bước 3: Test Connection**
1. Click **"Test Connection"** để kiểm tra
2. Nếu thành công → Click **"Finish"**
3. Nếu lỗi → Kiểm tra lại thông tin

## 🚀 Setup Database từ đầu

### **Bước 1: Tạo Database**
```sql
-- Trong DBeaver SQL Editor
CREATE DATABASE pinny_db;
```

### **Bước 2: Enable PostGIS Extension**
```sql
-- Kết nối vào database pinny_db
CREATE EXTENSION IF NOT EXISTS postgis;
```

### **Bước 3: Chạy Schema**
1. Mở file `backend/database.sql` trong DBeaver
2. Chọn database `pinny_db`
3. Click **"Execute SQL Script"** (F5)

## 🔍 Kiểm tra kết nối

### **Test Query:**
```sql
-- Kiểm tra PostGIS extension
SELECT PostGIS_Version();

-- Kiểm tra các bảng đã tạo
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- Kết quả mong đợi:
-- users
-- connections  
-- location_pins
-- location_shares
```

## ⚠️ Troubleshooting

### **Lỗi thường gặp:**

1. **Connection refused**
   - Kiểm tra PostgreSQL service có đang chạy không
   - Kiểm tra port 5432 có bị block không

2. **Authentication failed**
   - Kiểm tra username/password
   - Kiểm tra pg_hba.conf file

3. **Database does not exist**
   - Tạo database trước khi kết nối
   - Kiểm tra tên database

4. **PostGIS extension not found**
   - Cài đặt PostGIS extension cho PostgreSQL
   - Enable extension trong database

## 📝 Cấu hình Environment Variables

Sau khi kết nối thành công, cập nhật file `.env`:

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/pinny_db
```

## 🔐 Security Tips

1. **Không dùng user postgres cho production**
2. **Tạo user riêng cho ứng dụng**
3. **Giới hạn quyền truy cập**
4. **Sử dụng SSL cho production**

## 📊 DBeaver Features hữu ích

- **Schema Browser**: Xem cấu trúc database
- **SQL Editor**: Viết và chạy queries
- **Data Viewer**: Xem dữ liệu trong tables
- **ER Diagram**: Xem mối quan hệ giữa tables
- **Query History**: Lưu lịch sử queries 