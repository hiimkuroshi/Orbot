# Orbot · Focus Flow

Mở `Orbot.exe` (bản ZIP đã giải nén) hoặc file `Orbot-<phiên bản>.exe` (bản một file). Không cần cài Python hoặc Node.

[Tải bản phát hành trên GitHub](https://github.com/hiimkuroshi/Orbot/releases/latest). Bản ZIP chứa ứng dụng dạng thư mục, hướng dẫn, giấy phép MIT và giấy phép thư viện. File SHA256SUMS.txt trên trang phát hành chứa mã kiểm tra của EXE và ZIP.

1. Bấm Kết nối Discord hoặc Cài đặt ở góc trên.
2. Nếu chưa bật cổng kết nối: lưu công việc, thoát Discord ở khay hệ thống rồi bấm Mở Discord trong Orbot. Orbot tự chọn một cổng ngẫu nhiên và nhớ cho lần sau.
3. Khi Discord sẵn sàng, bấm Kết nối và kiểm tra đúng tài khoản. Có thể đóng hộp cài đặt sau khi kết nối.
4. Trong Quests, dùng Ctrl/Shift chọn nhiều nhiệm vụ và bấm Thêm vào hàng đợi.
5. Trong Hàng đợi, sắp xếp các mục trước khi chạy. Giữ Tự nhận Orbs bật nếu muốn nhận thưởng sau mỗi Quest; bấm Chạy hàng đợi.
6. Bấm Dừng hoặc nhấn Esc để dừng. Nhật ký có thể mở và lưu từ thanh điều hướng.
7. Dùng xong: thoát Discord ở khay hệ thống rồi mở lại như bình thường để đóng cổng gỡ lỗi.

Nếu Discord đã được mở với cổng kết nối từ trước, chỉ cần Kết nối, không phải mở lại Discord.

## Bảo mật

Trong lúc Discord mở cổng gỡ lỗi, chương trình khác trên máy cũng có thể điều khiển Discord đang đăng nhập. Cổng chỉ đóng khi Discord thoát hẳn; đóng Orbot không đóng cổng. Orbot chọn cổng ngẫu nhiên, chỉ kết nối khi chương trình giữ cổng là Discord, và nhắc bạn thoát Discord khi đóng ứng dụng.

## Cảnh báo SmartScreen

Thông báo "Windows đã bảo vệ máy tính của bạn" xuất hiện vì file chưa ký số và còn ít lượt tải, không phải vì phát hiện virus. Chỉ dùng file tải từ trang phát hành GitHub ở trên, so mã SHA-256 với SHA256SUMS.txt, rồi chọn Thông tin thêm → Vẫn chạy.

## Lưu ý khác

Orbs hiển thị là thưởng cơ bản của Quest, không phải số dư tài khoản hay cam kết ghi có. Banner là hình trang trí, không phải ảnh của Quest. Ứng dụng chỉ kết nối Discord Desktop trên máy; không yêu cầu nhập token hoặc mật khẩu.

Discord cấm dùng hệ thống tự động để tích lũy Orbs; tài khoản có thể bị hạn chế. Orbot không phải công cụ được Discord phê duyệt. Xem [điều khoản Discord Orbs](https://discord.com/terms/paid-services-terms#discord-orbs).

Tham số --demo mở dữ liệu minh họa và không chạy Quest thật. Hướng dẫn phát triển, giấy phép và kết quả kiểm chứng nằm trong thư mục dự án gốc.
