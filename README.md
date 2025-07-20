# Pinny - Location Sharing App

Pinny là ứng dụng chia sẻ vị trí với tính năng pin location, cho phép người dùng tạo và chia sẻ các vị trí đặc biệt với bạn bè.

## 🚀 Tính năng chính

- 🔐 **Authentication**: Đăng ký, đăng nhập với JWT
- 📍 **Real-time Location Sharing**: Chia sẻ vị trí real-time với bạn bè
- 📌 **Location Pinning**: Tạo và quản lý các pin location
- 👥 **User Connections**: Kết nối với bạn bè và quản lý danh sách
- 🗺️ **Interactive Maps**: Bản đồ tương tác với Leaflet/React Native Maps
- 📱 **Cross-platform**: Web (Next.js) và Mobile (React Native)
- 🔍 **Search & Discovery**: Tìm kiếm vị trí gần đây và người dùng
- 📸 **Image Upload**: Thêm hình ảnh cho location pins

## 🛠️ Tech Stack

### Backend
- **Node.js + Express.js** - API server
- **PostgreSQL + PostGIS** - Database với hỗ trợ geospatial
- **Socket.io** - Real-time communication
- **JWT** - Authentication
- **Multer** - File uploads

### Frontend Web (Next.js)
- **Next.js 14** với App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **React Query** - State management
- **Leaflet** - Maps
- **Socket.io-client** - Real-time updates

### Mobile (React Native)
- **React Native + Expo** - Cross-platform mobile
- **React Native Maps** - Maps
- **Expo Location** - GPS services
- **React Query** - State management
- **React Navigation** - Navigation

## 📦 Cài đặt và Chạy

### Prerequisites
- Node.js 18+
- PostgreSQL 12+ với PostGIS extension
- npm hoặc yarn

### 1. Clone Repository
```bash
git clone https://github.com/your-username/pinny.git
cd pinny
```

### 2. Setup Database
```bash
# Tạo database
createdb pinny_db

# Chạy schema (xem database-connection-guide.md)
psql -d pinny_db -f backend/database.sql
```

### 3. Setup Backend
```bash
cd backend

# Cài đặt dependencies
npm install

# Copy environment file
copy env.example .env

# Chỉnh sửa .env với thông tin database và JWT secret
# DATABASE_URL=postgresql://username:password@localhost:5432/pinny_db
# JWT_SECRET=your-super-secret-jwt-key

# Chạy development server
npm run dev
```

### 4. Setup Frontend Web
```bash
cd frontend-web

# Cài đặt dependencies
npm install

# Tạo .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:5000" > .env.local

# Chạy development server
npm run dev
```

### 5. Setup Mobile App
```bash
cd mobile-app

# Cài đặt dependencies
npm install

# Chạy với Expo
npx expo start
```

## 📊 Database Schema

Xem file `database-connection-guide.md` để biết chi tiết về:
- Cấu trúc database
- Cách kết nối với DBeaver
- ERD diagram

## 🔗 API Endpoints

### Authentication
- `POST /api/auth/register` - Đăng ký
- `POST /api/auth/login` - Đăng nhập
- `GET /api/auth/me` - Lấy thông tin user hiện tại

### Users
- `GET /api/users/profile` - Lấy profile
- `PUT /api/users/profile` - Cập nhật profile
- `GET /api/users/search` - Tìm kiếm users
- `GET /api/users/connections` - Lấy danh sách connections
- `POST /api/users/connections/:userId` - Gửi connection request
- `PUT /api/users/connections/:connectionId` - Accept/Reject request

### Locations
- `POST /api/locations/share` - Chia sẻ vị trí
- `GET /api/locations/recent` - Lấy vị trí gần đây
- `GET /api/locations/shared` - Lấy vị trí được chia sẻ

### Pins
- `POST /api/pins` - Tạo pin mới
- `GET /api/pins/my-pins` - Lấy pins của user
- `GET /api/pins/shared` - Lấy pins được chia sẻ
- `GET /api/pins/:pinId` - Lấy chi tiết pin
- `PUT /api/pins/:pinId` - Cập nhật pin
- `DELETE /api/pins/:pinId` - Xóa pin
- `GET /api/pins/nearby/search` - Tìm pins gần đây

## 🏗️ Project Structure

```
pinny/
├── backend/              # Node.js API server
│   ├── src/
│   ├── package.json
│   ├── database.sql
│   └── env.example
├── frontend-web/         # Next.js web app
│   ├── app/
│   ├── components/
│   └── package.json
├── mobile-app/           # React Native mobile app
│   ├── src/
│   ├── app.json
│   └── package.json
├── shared/               # Shared types và utilities
│   ├── types/
│   └── api/
├── database-erd.md       # Database documentation
├── database-connection-guide.md
└── README.md
```

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Tạo Pull Request

## 📄 License

MIT License - xem file [LICENSE](LICENSE) để biết thêm chi tiết.

## 🆘 Support

Nếu có vấn đề hoặc câu hỏi, vui lòng tạo issue trên GitHub. 