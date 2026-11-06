# Hướng dẫn quản trị UNETI AI

Mọi việc dưới đây làm trên trang GitHub của kho mã, không cần cài gì thêm. Người làm phải có quyền ghi vào kho mã.

## Đăng tin Nhà trường

1. Vào tab **Issues**, bấm **New issue**, chọn **Đăng tin Nhà trường**.
2. Điền biểu mẫu rồi bấm **Create**. Tin thường lên trong vòng vài phút và trang tin tự đóng lại.
3. Nếu biểu mẫu sai, trang tin sẽ ghi rõ lỗi và tin chưa được đăng. Bạn tạo lại tin mới.

Lưu ý:

- Tin và cả trang tin đều **công khai**, nên chỉ đăng thông tin công khai.
- Người dùng chỉ thấy tin ở chuông thông báo khi mở phần mềm.
- Tin chỉ có chữ và một nút liên kết. Muốn kèm ảnh, hãy đặt ảnh ở trang web của Trường rồi dẫn liên kết.

**Gỡ tin:** mở trang tin đã đăng, gắn nhãn `go-tin`.

## Duyệt bản cập nhật

1. Sáng thứ Hai hằng tuần, hệ thống kiểm tra Javis OS. Nếu có bản mới, tab **Pull requests** sẽ có yêu cầu tên "Cập nhật từ Javis OS …".
2. Bạn chờ phần **Checks** chạy xong và hiện dấu xanh.
3. Bấm **Merge pull request**. Mọi bản đã cài sẽ thấy có bản mới.

Khi có tin vá lỗi bảo mật gấp, vào tab **Actions**, chọn **Cập nhật từ Javis OS**, bấm **Run workflow** để kiểm tra ngay.

Nếu lượt chạy báo lỗi "Không thấy đoạn cần sửa", nghĩa là bản gốc đã đổi chỗ mà công cụ đổi tên cần sửa. Các bản đã cài không bị ảnh hưởng. Người kỹ thuật cần sửa `uneti/apply_brand.py`.

Nếu **Checks** hiện dấu đỏ, không bấm Merge và nhờ người kỹ thuật xem. Bản gốc thỉnh thoảng thêm bài kiểm thử mới kiểm tra đúng chữ "Javis", khi đó cần cập nhật `uneti/apply_brand.py`.

## Đóng góp kinh phí

Trang đóng góp nằm ở `uneti/site/index.html`, đang nhận qua tài khoản MB 221268686868 của HOI SINH VIEN UNETI.

Khi đổi tài khoản nhận:

1. Thay ảnh `uneti/site/qr-ung-ho.png` bằng mã QR mới, giữ nguyên tên tệp.
2. Sửa tên người nhận, số tài khoản và ngân hàng trong `uneti/site/index.html`.
3. Dùng điện thoại quét thử mã trên trang thật và kiểm tra đúng tên người nhận, nhưng chưa chuyển tiền.

## Không dùng chung với bản cá nhân

Không cài UNETI AI trên máy đang chạy Javis OS mà chưa kiểm tra cổng 7777. Không dùng lại bot, token hay kết nối của một bản Javis khác.
