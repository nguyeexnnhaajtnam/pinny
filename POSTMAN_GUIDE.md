# 📋 Hướng dẫn sử dụng Postman Collection cho Pinny API

## 🚀 Cách import collection

### **Bước 1: Import Collection**
1. Mở Postman
2. Click **Import** button
3. Chọn file `Pinny_API_Collection.postman_collection.json`
4. Click **Import**

### **Bước 2: Setup Environment Variables**
1. Click **Environments** tab
2. Click **+** để tạo environment mới
3. Đặt tên: `Pinny Local`
4. Thêm các variables:

| Variable | Initial Value | Current Value |
|----------|---------------|---------------|
| `base_url` | `http://localhost:5000` | `http://localhost:5000` |
| `auth_token` | `` | `` |
| `pin_id` | `` | `` |
| `target_user_id` | `` | `` |
| `request_user_id` | `` | `` |
| `connection_user_id` | `` | `` |

5. Click **Save**

## 🔧 Cách sử dụng

### **1. Health Check**
- Chạy **Health Check** để kiểm tra server hoạt động
- Không cần authentication

### **2. Authentication Flow**
1. **Register User**: Tạo tài khoản mới
2. **Login User**: Đăng nhập (tự động lưu token)
3. **Get Current User**: Kiểm tra thông tin user

### **3. User Management**
- **Get/Update Profile**: Quản lý thông tin cá nhân
- **Upload Avatar**: Upload ảnh đại diện
- **Search Users**: Tìm kiếm user khác
- **Connection Management**: Gửi/chấp nhận/từ chối kết nối

### **4. Location Pins**
- **Create Pin**: Tạo pin mới (có thể có ảnh)
- **Get My Pins**: Xem pins của mình
- **Update/Delete Pin**: Chỉnh sửa/xóa pin
- **Search Nearby**: Tìm pins gần đây
- **Search by Name**: Tìm pins theo tên

### **5. Location Sharing**
- **Share Location**: Chia sẻ vị trí hiện tại
- **Get Recent**: Xem vị trí gần đây
- **Get Shared**: Xem vị trí từ connections

## 🔑 Variables tự động

### **auth_token**
- Tự động được set sau khi login thành công
- Sử dụng trong tất cả requests cần authentication

### **pin_id, target_user_id, etc.**
- Cần set thủ công sau khi có response
- Copy từ response của request trước đó

## 📝 Ví dụ workflow

### **Workflow 1: Tạo và quản lý pin**
1. Register/Login
2. Create Location Pin
3. Copy `pin_id` từ response
4. Get My Pins (kiểm tra)
5. Update Pin (sử dụng `pin_id`)
6. Delete Pin (sử dụng `pin_id`)

### **Workflow 2: Kết nối và chia sẻ**
1. Register 2 users
2. Search Users (từ user 1)
3. Copy `target_user_id` từ response
4. Send Connection Request
5. Login với user 2
6. Get Connection Requests
7. Copy `request_user_id` từ response
8. Accept Connection Request
9. Share Location (từ user 1)
10. Get Shared Locations (từ user 2)

## 🛠️ Troubleshooting

### **Lỗi 401 Unauthorized**
- Kiểm tra `auth_token` đã được set chưa
- Chạy lại Login request

### **Lỗi 404 Not Found**
- Kiểm tra `base_url` đúng chưa
- Đảm bảo server đang chạy

### **Lỗi 500 Internal Server Error**
- Kiểm tra database connection
- Xem server logs

## 📊 Response Examples

### **Login Response**
```json
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com"
  }
}
```

### **Create Pin Response**
```json
{
  "message": "Location pin created successfully",
  "pin": {
    "id": 1,
    "name": "Coffee Shop",
    "description": "Great coffee place",
    "latitude": 10.762622,
    "longitude": 106.660172,
    "isPublic": true,
    "createdAt": "2024-01-01T12:00:00.000Z"
  }
}
```

### **Share Location Response**
```json
{
  "message": "Location shared successfully",
  "location": {
    "id": 1,
    "latitude": 10.762622,
    "longitude": 106.660172,
    "accuracy": 10,
    "timestamp": "2024-01-01T12:00:00.000Z"
  }
}
```

## 🎯 Tips

1. **Sử dụng Environment**: Luôn chọn environment đúng
2. **Copy IDs**: Copy ID từ response để sử dụng trong request tiếp theo
3. **Test từng bước**: Chạy từng request để đảm bảo hoạt động
4. **Check Headers**: Đảm bảo Content-Type và Authorization headers đúng
5. **File Upload**: Sử dụng form-data cho file uploads

## 📱 Mobile Testing

Để test trên mobile:
1. Thay đổi `base_url` thành IP máy tính
2. Đảm bảo mobile và máy tính cùng mạng
3. Ví dụ: `http://192.168.1.100:5000` 