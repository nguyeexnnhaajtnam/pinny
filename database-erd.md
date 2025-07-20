# Pinny Database - Entity Relationship Diagram

## 📊 Cấu trúc Database

### 1. **users** Table (Bảng người dùng)
- **id** (PK): Khóa chính, tự động tăng
- **username**: Tên người dùng (unique)
- **email**: Email (unique)
- **password_hash**: Mật khẩu đã mã hóa
- **avatar**: URL hình đại diện
- **created_at**: Thời gian tạo
- **updated_at**: Thời gian cập nhật

### 2. **connections** Table (Bảng kết nối bạn bè)
- **id** (PK): Khóa chính, tự động tăng
- **user1_id** (FK): ID người dùng 1 (tham chiếu users.id)
- **user2_id** (FK): ID người dùng 2 (tham chiếu users.id)
- **status**: Trạng thái kết nối ('pending', 'accepted', 'rejected')
- **created_at**: Thời gian tạo
- **updated_at**: Thời gian cập nhật
- **UNIQUE(user1_id, user2_id)**: Đảm bảo không có kết nối trùng lặp

### 3. **location_pins** Table (Bảng pin vị trí)
- **id** (PK): Khóa chính, tự động tăng
- **user_id** (FK): ID người tạo pin (tham chiếu users.id)
- **name**: Tên pin
- **description**: Mô tả
- **location**: Vị trí địa lý (PostGIS Point)
- **image_url**: URL hình ảnh
- **is_public**: Có public không
- **created_at**: Thời gian tạo
- **updated_at**: Thời gian cập nhật

### 4. **location_shares** Table (Bảng chia sẻ vị trí real-time)
- **id** (PK): Khóa chính, tự động tăng
- **user_id** (FK): ID người chia sẻ (tham chiếu users.id)
- **location**: Vị trí địa lý (PostGIS Point)
- **accuracy**: Độ chính xác GPS
- **timestamp**: Thời gian chia sẻ

## 🔗 Relationships (Mối quan hệ)

1. **users** → **connections** (1:N)
   - Một user có thể có nhiều connections
   - connections.user1_id và connections.user2_id đều tham chiếu users.id

2. **users** → **location_pins** (1:N)
   - Một user có thể tạo nhiều location pins
   - location_pins.user_id tham chiếu users.id

3. **users** → **location_shares** (1:N)
   - Một user có thể chia sẻ nhiều vị trí
   - location_shares.user_id tham chiếu users.id

## 🗺️ PostGIS Features

- **GEOMETRY(POINT, 4326)**: Lưu trữ tọa độ địa lý (latitude, longitude)
- **GIST Indexes**: Tối ưu cho truy vấn địa lý
- **ST_Distance()**: Tính khoảng cách giữa 2 điểm
- **ST_Within()**: Kiểm tra điểm có trong vùng không

## 📈 Indexes

- **users**: email, username
- **connections**: user1_id, user2_id, status
- **location_pins**: user_id, location (GIST), is_public
- **location_shares**: user_id, location (GIST), timestamp

## 🔄 Triggers

- **update_updated_at_column()**: Tự động cập nhật updated_at khi có thay đổi

## 📋 Cách xem ERD

1. Mở file `database-erd.drawio` trong [draw.io](https://app.diagrams.net/)
2. Hoặc import file vào draw.io online
3. ERD sẽ hiển thị:
   - Các bảng với màu sắc khác nhau
   - Mối quan hệ giữa các bảng
   - Legend giải thích các ký hiệu 