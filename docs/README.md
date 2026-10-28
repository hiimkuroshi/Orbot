# Tài liệu Orbot

- [Hướng dẫn chính](../README.md): chạy ứng dụng, tính năng và phát triển.
- [Hướng dẫn bản EXE](RELEASE.md): hướng dẫn ngắn, được chép vào dist khi build.
- [Thiết kế Focus Flow](../DESIGN.md): màu sắc, chữ, bố cục và trạng thái giao diện.
- [Bảo mật](../SECURITY.md): rủi ro cổng gỡ lỗi, biện pháp và cách báo lỗ hổng.
- [Phát hành](PUBLISHING.md): quy trình tag → CI → phát hành, cảnh báo SmartScreen, ký số miễn phí.
- [Kiểm chứng](VERIFICATION.md): kết quả kiểm thử và giới hạn đã xác minh.
- [Lịch sử thay đổi](CHANGELOG.md): các thay đổi đã triển khai qua từng bản.
- [Ba concept UI](design/concepts/README.md): ảnh và prompt trước khi chọn Focus Flow.
- [Giao diện trước đây](design/legacy-ui.png): ảnh đối chiếu trước khi thiết kế lại.
- [Ảnh giao diện hiện tại](images/focus-flow.png): Focus Flow; có thêm ảnh cửa sổ nhỏ, danh mục, kết nối và nhắc đóng cổng trong images/.

Mã nguồn nằm trong orbot/, tài nguyên chạy trong orbot/assets/, kiểm thử trong tests/, công cụ phát triển trong scripts/, giấy phép thư viện trong licenses/. dist/ chỉ giữ bản ZIP, EXE và SHA256SUMS.txt của lần build gần nhất; .venv/ là môi trường phát triển cục bộ.

Cache, file spec và dữ liệu đóng gói được tạo dưới build/ khi chạy lệnh kiểm tra hoặc build. Thư mục này có thể xóa sau khi dùng; scripts sẽ tự tạo lại khi cần. Các ảnh concept và tài liệu không thuộc nhóm cache.
