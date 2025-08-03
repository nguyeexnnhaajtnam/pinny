# 📍 Project: Pinny - Real-time Location Sharing App

## 🧠 Mục tiêu
Đây là ứng dụng mình xây dựng vừa để **học tập** vừa để **phát triển MVP**. Ban đầu chỉ cần hỗ trợ 2 user (kiểu cặp đôi/couple), nhưng về lâu dài sẽ mở rộng thành một social app (vị trí + ảnh + tương tác).

---

## 🔧 Tech Stack

### Frontend (Web)
- Next.js 14 (App Router, TypeScript)
- Tailwind CSS + shadcn/ui
- React Query (hoặc Server Actions nếu cần)
- Leaflet (hiển thị bản đồ)
- Socket.io client (real-time)

### Mobile
- React Native + Expo
- React Native Maps + Expo Location
- React Navigation
- Image picker + camera
- Socket.io client

### Backend
- NestJS (TypeScript)
- RESTful API
- JWT Auth
- Multer (upload ảnh)
- PostgreSQL + PostGIS (toạ độ & pin)
- WebSocket Gateway (Socket.io)
- Prisma ORM
- Rate limiting & security middleware (Helmet, CORS, etc.)

#### Lưu ý: 
- Khi cần cài thư viện hãy hỏi ý mình và để mình quyết định cài hay không.
- Giải thích chi tiết từng bước code, không bỏ qua dù là chi tiết nhỏ nhất.
- Đưa ra nhiều lựa chọn, và giải thích ưu, nhược điểm của từng lựa chọn và gợi ý lựa chọn phù hợp nhất.
- Hướng dẫn mình viết và sử dụng unit test phù hợp.
- Đưa ra ví dụ cụ thể thực tế khi giải thích.
- Hướng dẫn mình làm không tự ý apply code hay tạo file code, hướng dẫn chi tiết từng bước

---