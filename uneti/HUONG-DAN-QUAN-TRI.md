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

## Đóng góp kinh phí

Chỉ mở sau khi Nhà trường thống nhất tài khoản tiếp nhận và cách quản lý khoản đóng góp.

1. Sửa `uneti/site/donate.json`: đổi `open` thành `true`, điền ngân hàng, số tài khoản, chủ tài khoản. Nếu có mã QR, đặt ảnh vào `uneti/site/` rồi ghi tên tệp vào `qr_image`.
2. Sau mỗi khoản thu hoặc chi, thêm một dòng vào `uneti/site/so-thu-chi.csv`, ví dụ `2027-01-15,thu,500000,Ủng hộ qua chuyển khoản`. Cột loại ghi `thu` hoặc `chi`, số tiền không có dấu chấm hay dấu phẩy.

Không ghi tên hay thông tin cá nhân của người đóng góp vào sổ nếu họ chưa đồng ý, vì sổ này công khai.

## Không dùng chung với bản cá nhân

Không cài UNETI AI trên máy đang chạy Javis OS mà chưa kiểm tra cổng 7777. Không dùng lại bot, token hay kết nối của một bản Javis khác.
