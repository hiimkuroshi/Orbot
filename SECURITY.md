# Bảo mật Orbot

## Báo lỗ hổng

Không mở issue công khai cho lỗ hổng. Hãy dùng **Security → Report a vulnerability** trên trang GitHub của repo (Private vulnerability reporting). Mô tả phiên bản Orbot, phiên bản Discord, các bước tái hiện và ảnh hưởng. Chỉ bản phát hành mới nhất được sửa lỗi.

## Mô hình rủi ro

Orbot không có máy chủ, không gửi dữ liệu ra ngoài, không đọc hay lưu token và mật khẩu. Ứng dụng chỉ lưu số cổng đã dùng trong `%LOCALAPPDATA%\Orbot\settings.json`.

Rủi ro chính nằm ở **cổng gỡ lỗi của Discord** (Chrome DevTools Protocol):

- Orbot mở Discord với `--remote-debugging-port` trên `127.0.0.1`. Cổng không có xác thực.
- Trong lúc cổng mở, mọi chương trình trên máy, kể cả của tài khoản Windows khác, có thể chạy mã trong Discord đang đăng nhập. Trang web bị chặn vì Chromium bản mới kiểm tra `Origin` và `Host` của kết nối.
- Cổng chỉ đóng khi Discord thoát hẳn; đóng Orbot không đóng cổng.

Biện pháp trong Orbot:

| Biện pháp | Giới hạn |
| --- | --- |
| Cổng ngẫu nhiên trong khoảng 20000–48999 thay vì `9222` | Chương trình trên máy vẫn có thể quét hết các cổng |
| Kiểm tra chương trình giữ cổng là `Discord.exe`, `DiscordCanary.exe` hoặc `DiscordPTB.exe` (Windows) | Chỉ dựa trên tên file |
| Chỉ kết nối `127.0.0.1`, tắt proxy, chặn chuyển hướng, kiểm tra địa chỉ WebSocket và tên miền Discord | — |
| Lệnh gửi vào Discord nằm trong danh sách cho phép, tham số mã hóa JSON | — |
| Cảnh báo trong hộp kết nối, ghi chú ở chân trang và nhắc thoát Discord khi đóng Orbot | Người dùng vẫn phải tự thoát Discord |

Khuyến nghị: chỉ dùng trên máy tin tưởng, không dùng trên máy dùng chung nhiều tài khoản, và thoát Discord ở khay hệ thống sau khi dùng xong.

## Kiểm tra bản tải

Mỗi bản phát hành từ 0.2.1 được build bằng [GitHub Actions](.github/workflows/build.yml) và có chứng nhận nguồn gốc:

```powershell
gh attestation verify .\Orbot-0.2.1-windows-x64.zip -R hiimkuroshi/Orbot
```

So thêm mã SHA-256 với `SHA256SUMS.txt`. Không dùng file Orbot tải từ nguồn khác.
