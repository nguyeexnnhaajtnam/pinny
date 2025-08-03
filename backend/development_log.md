# Pinny Backend - Nhật ký phát triển

*File này ghi lại quá trình phát triển backend của Pinny một cách chi tiết, theo từng ngày và từng bước thực hiện.*

---

## **Ngày 03 tháng 08 năm 2024**

### **Giai đoạn 1: Khởi tạo và Thiết lập Nền tảng**

**Mục tiêu:** Tạo project NestJS mới và tích hợp Prisma ORM để kết nối với database.

---

**Bước 1.1: Tạo Project NestJS**
- **Lệnh đã thực thi:**
  ```bash
  pnpm dlx @nestjs/cli new backend
  ```
- **Kết quả:** Tạo thành công cấu trúc project NestJS mặc định trong thư mục `backend/`.

---

**Bước 1.2: Cài đặt Prisma CLI**
- **Lệnh đã thực thi:**
  ```bash
  pnpm add -D prisma
  ```
- **Kết quả:**
  - Thêm `prisma` vào `devDependencies` trong file `package.json`.
  - Giúp chúng ta có thể sử dụng các lệnh của Prisma trong project.

---

**Bước 1.3: Khởi tạo Prisma trong Project**
- **Lệnh đã thực thi:**
  ```bash
  pnpm exec prisma init
  ```
- **Kết quả:**
  - Tạo thư mục `prisma/` chứa file `schema.prisma`.
  - Tạo file `.env` ở thư mục gốc `backend/` để lưu trữ `DATABASE_URL`.
  - Tự động cập nhật `.gitignore` để bỏ qua file `.env`.

---

**Bước 1.4: Cấu hình Database Schema và Connection**
- **Hành động:** Chỉnh sửa thủ công 2 file.
- **File 1: `backend/.env`**
  - **Thay đổi:** Cập nhật `DATABASE_URL` để trỏ đến database `pinny_db` trên Docker.
  - **Nội dung mới:**
    ```env
    DATABASE_URL="postgresql://user:password@localhost:5432/pinny_db?schema=public"
    ```
- **File 2: `backend/prisma/schema.prisma`**
  - **Thay đổi:**
    - Thêm vào model `User` để định nghĩa bảng người dùng.
    - Cấu hình Prisma để hỗ trợ PostGIS extension.
  - **Nội dung mới:**
    ```prisma
    generator client {
      provider        = "prisma-client-js"
      previewFeatures = ["postgresqlExtensions"]
    }

    datasource db {
      provider   = "postgresql"
      url        = env("DATABASE_URL")
      extensions = [postgis(version: "3.4.2")]
    }

    model User {
      id        String   @id @default(cuid())
      email     String   @unique
      password  String
      username  String?  @unique
      avatarUrl String?
      createdAt DateTime @default(now())
      updatedAt DateTime @updatedAt
    }
    ```

---

**Bước 1.5: Đồng bộ hóa Database (Migration)**
- **Lệnh ban đầu:**
  ```bash
  pnpm exec prisma migrate dev --name init-user-model
  ```
- **Sự cố gặp phải:**
  - **Lỗi:** `ERROR: extension "postgis" has no installation script nor update path for version "3.4.2"`
  - **Nguyên nhân:** Yêu cầu phiên bản PostGIS cụ thể mà PostgreSQL trong Docker không có.
  - **Quá trình xử lý:**
    1. Sửa `schema.prisma` thành `extensions = [postgis]`.
    2. Xóa thư mục migration bị lỗi `backend/prisma/migrations/2025...`.
    3. Reset lại database bằng `pnpm exec prisma migrate reset` để xóa "dấu vết" của migration lỗi.
- **Lệnh cuối cùng (Thành công):**
  ```bash
  pnpm exec prisma migrate dev --name init-user-model
  ```
- **Kết quả:**
  - Tạo thành công migration `init-user-model`.
  - Bảng `User` được tạo trong database `pinny_db`.
  - Prisma Client được cập nhật để nhận biết model `User`.

---
