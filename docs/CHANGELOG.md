# Lịch sử thay đổi Orbot

## 0.2.1: Bảo mật và phát hành minh bạch

- Mỗi lần Mở Discord, Orbot chọn một cổng gỡ lỗi ngẫu nhiên (20000–48999) thay vì `9222` và nhớ cổng này trong `%LOCALAPPDATA%\Orbot\settings.json`. Nếu Discord đã mở cổng, Orbot dùng lại thay vì mở Discord lần nữa.
- Trên Windows, chỉ kết nối khi chương trình đang giữ cổng là Discord; từ chối và nêu tên nếu là chương trình khác hoặc không xác minh được.
- Cảnh báo bảo mật trong hộp kết nối, ghi chú "Cổng gỡ lỗi đang mở" ở chân trang, và hộp nhắc thoát Discord khi đóng Orbot nếu cổng vẫn mở.
- Sửa lỗi phản hồi sai định dạng từ cổng kết nối làm luồng nền dừng hẳn và Orbot không đóng được.
- Build trên GitHub Actions với thư viện ghim mã băm, Action ghim theo commit, chứng nhận nguồn gốc và tự công bố bản phát hành khi đẩy tag. Thêm bản ZIP dạng thư mục (khuyên dùng), EXE có thông tin phiên bản, không nén UPX.
- Thêm SECURITY.md và hướng dẫn phát hành, xử lý cảnh báo SmartScreen trong docs/PUBLISHING.md.

## 0.2.0: Focus Flow

- Giao diện slate/amber theo concept 3, hàng đợi bên trái và tiến độ ở vùng trọng tâm.
- Điều hướng ngang, cài đặt kết nối riêng, nhật ký thu gọn và công tắc tự nhận Orbs.
- Hỗ trợ Ctrl/Shift, sắp xếp bằng phím, giữ nút Dừng khi đổi màn hình.
- Bộ kiểm thử, ảnh giao diện và EXE đã xác minh; engine giữ nguyên.
- Dọn dự án: script trong scripts/, tài liệu trong docs/, giấy phép trong licenses/. dist/ chỉ giữ bản phát hành hiện tại; cache và spec tập trung trong build/.

## 0.1.3: Hàng đợi và nhận Orbs

- Thêm tab Hàng đợi, lưu danh sách riêng thay vì phụ thuộc vào lựa chọn hiện tại trong bảng. Lọc Video/Chơi game, chọn dòng khác hoặc cập nhật tiến độ không làm mất các Quest đã thêm.
- Giữ thứ tự cố định trong mỗi lượt chạy. Nhật ký ghi số thứ tự, bước chuyển Quest và tổng kết sau khi xử lý hết danh sách.
- Trạng thái **Đang nhận Orbs**, **Đã nhận thưởng** và **Cần nhận trong Discord** phân biệt kết quả nhận thưởng với hoàn thành nhiệm vụ. Tự nhận Orbs mặc định bật.
- Phân biệt xử lý hết, chủ động dừng và tạm dừng do lỗi Discord. Quest chưa xử lý được giữ lại trong phiên Orbot hiện tại; hàng đợi chưa được lưu ra đĩa khi đóng/ngắt kết nối ứng dụng.

## 0.1.1: Sửa lỗi kết nối

- Nhận diện lớp QuestStore/UserStore thật, dùng phương thức khai báo trên object/prototype để tránh chọn nhầm namespace động.
- Bật CDP Page domain trước khi đăng ký preload; tải lại cửa sổ hiện có thay vì điều hướng toàn bộ Electron renderer.
- Khi không tìm được module, nhật ký cho biết thành phần còn thiếu và số module đã thu thập.

## 0.1.2: Sửa lỗi phản hồi HTML

Bản cũ có thể chọn thư viện HTTP cấp thấp vì nó cũng có các hàm `get/post`. Khi truyền object `{url, body}` vào hàm cần chuỗi URL, request bị gửi tới `/[object Object]` và nhận trang HTML của Discord.

- Loại bỏ thư viện HTTP cấp thấp khỏi danh sách API ứng viên.
- Kiểm chứng từng client bằng GET chỉ đọc `/users/@me`, đối chiếu ID ngay trong Discord với phiên hiện tại, và ghi nhớ dạng tham số đã xác minh. Dữ liệu phản hồi của bước này không gửi về Python.
- Chỉ cho chạy Quest sau khi API được xác minh. Áp dụng đúng dạng tham số cho cả GET và POST.
- Dừng hàng đợi nếu gặp HTML và ghi thông báo ngắn, không đổ mã trang web vào nhật ký.

