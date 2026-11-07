# UNETI AI

Trợ lý AI tự cài trên máy, phát triển tiếp từ [Javis OS](https://github.com/blogminhquy/javis-os), dành cho cán bộ và sinh viên Trường Đại học Kinh tế - Kỹ thuật Công nghiệp.

Phần mềm **chưa kèm AI**. Sau khi cài, mỗi người tự kết nối tài khoản AI của mình và tự chịu chi phí của tài khoản đó.

## Cài đặt

Hướng dẫn từng bước nằm ở [trang tải về](https://uneti-ai.github.io/uneti-ai/tai-ve.html).

- Windows 10/11: [UNETI-AI-Setup.exe](https://github.com/uneti-ai/uneti-ai/releases/download/desktop/UNETI-AI-Setup.exe)
- macOS 11 trở lên: [UNETI-AI-macOS.dmg](https://github.com/uneti-ai/uneti-ai/releases/download/desktop/UNETI-AI-macOS.dmg)

**Lưu ý trước khi cài:** AI được kết nối sẽ có toàn quyền trên máy cài đặt, gồm đọc tệp và chạy lệnh. Chỉ cài trên máy của bạn và đọc [hướng dẫn bảo mật](docs/14-bao-mat-tai-khoan.md).

Nếu máy đã dùng cổng 7777 cho chương trình khác, bộ cài sẽ dừng lại và báo, không tự tắt chương trình đó. Khi đó, tắt chương trình kia, hoặc thêm dòng `UNETI_PORT=8080` vào tệp `.env` trong thư mục cài đặt rồi chạy lại. Biểu tượng mở phần mềm sẽ tự theo cổng mới.

Trên Windows, bấm đúp `UNETI AI.bat` trong thư mục cài đặt để mở phần mềm. Muốn phần mềm tự chạy khi mở máy, chạy `uneti-autostart.bat`.

## Cập nhật

Bản mới được lấy từ phần mềm gốc, chạy kiểm thử rồi quản trị viên duyệt mới phát hành. Phần mềm báo có bản mới ở trang Cài đặt → Cập nhật.

## Tin Nhà trường

Thông báo hiện ở biểu tượng chuông trong phần mềm. Quản trị viên xem cách đăng tin tại [hướng dẫn quản trị](uneti/HUONG-DAN-QUAN-TRI.md).

## Đóng góp kinh phí

Đóng góp là tự nguyện và không ảnh hưởng đến quyền sử dụng. Kinh phí đóng góp sẽ được sử dụng trong việc từ thiện, xã hội hóa, phát triển UNETI AI. Xem cách đóng góp bằng mã QR tại [trang đóng góp](https://uneti-ai.github.io/uneti-ai/).

Tác giả Javis OS cũng nhận ủng hộ riêng, xem mục Support trong [kho mã gốc](https://github.com/blogminhquy/javis-os).

## Giấy phép

UNETI AI dùng giấy phép MIT, xem [LICENSE](LICENSE). Bản quyền phần mã gốc thuộc về Nguyễn Minh Quý (blogminhquy). Thành phần bên thứ ba giữ giấy phép riêng, ví dụ `third_party/harness2` dùng Apache-2.0.
