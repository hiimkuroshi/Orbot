# Orbot 0.2.0 · Focus Flow

Ứng dụng Windows có giao diện tiếng Việt để điều phối Discord Quests thưởng Orbs. Kết nối với Discord Desktop trên máy bằng phiên đã đăng nhập; không yêu cầu nhập token hay mật khẩu.

## Tải xuống

**[Tải Orbot 0.2.0 cho Windows x64 (.exe)](https://github.com/hiimkuroshi/Orbot/releases/download/v0.2.0/Orbot-0.2.0.exe)** — tải về và mở trực tiếp, không cần cài Python hoặc Node.

[Bản ZIP kèm hướng dẫn và giấy phép](https://github.com/hiimkuroshi/Orbot/releases/download/v0.2.0/Orbot-0.2.0-windows-x64.zip) · [Tất cả bản phát hành](https://github.com/hiimkuroshi/Orbot/releases) · [SHA-256](https://github.com/hiimkuroshi/Orbot/releases/download/v0.2.0/SHA256SUMS.txt)

## Chạy ứng dụng

Đóng Orbot cũ, mở **`dist/Orbot-0.2.0.exe`**, hoặc bấm đúp **`Start-Orbot.cmd`** trong thư mục dự án. File EXE đã đóng gói Python và thư viện; máy chạy không cần cài Python hoặc Node. Nếu Discord đã bật cổng kết nối từ lần trước, chỉ cần kết nối, không cần mở lại Discord.

1. Lưu việc đang làm và thoát Discord từ biểu tượng ở khay hệ thống.
2. Mở Orbot, bấm **Kết nối Discord** (hoặc **Cài đặt**) ở góc trên. Giữ cổng `9222`, bấm **Mở Discord**. Nếu không tìm thấy bản cài, chọn `Discord.exe` khi hộp thoại xuất hiện.
3. Khi Discord mở xong, bấm **Kết nối** trong hộp cài đặt. Khi cần, Orbot mở Quest Home và tải lại giao diện một lần để nạp bộ kết nối. Kết nối xong có thể đóng hộp cài đặt.
4. Kiểm tra tên tài khoản ở góc trên. Ở tab **Quests**, giữ Ctrl/Shift để chọn nhiều hoặc bấm **Chọn tất cả có thể chạy**, rồi **Thêm vào hàng đợi →**.
5. Mục **Hàng đợi** hiển thị thứ tự bên trái và tiến độ Quest bên phải. Có thể đưa lên/xuống, **Bỏ Quest** đã chọn hoặc **Xóa hết** trước khi chạy. Giữ **Tự nhận Orbs** bật (mặc định), rồi bấm **Chạy hàng đợi**.
6. Bấm **Dừng**, nhấn Esc, ngắt kết nối hoặc đóng Orbot để dừng hàng đợi. Sau khi xong, có thể mở lại Discord theo cách thông thường để không bật cổng gỡ lỗi nữa.

Nếu Discord đã chạy trước khi bấm Mở Discord, phiên hiện tại có thể không nhận cổng mới. Orbot không tự đóng Discord; hãy thoát ở khay hệ thống rồi mở lại từ Orbot. Giữ cửa sổ Orbot mở trong lúc chạy.

## Giao diện Focus Flow

- Nền slate tối, điểm nhấn amber, điều hướng ngang: **Quests**, **Hàng đợi**, **Nhật ký**.
- Hàng đợi có số thứ tự, chọn nhiều bằng Ctrl/Shift; Alt+↑/↓ để đổi thứ tự, Delete để bỏ mục đã chọn. Không chỉnh sửa khi đang chạy.
- Vùng trọng tâm hiển thị tên Quest, thưởng cơ bản, thời gian, tiến độ và ba bước: bắt đầu, thực hiện, nhận Orbs. Chọn mục khác khi đang chạy vẫn giữ Quest đang xử lý ở vùng trọng tâm.
- Nút **Dừng · Esc** vẫn có mặt khi chuyển sang Quests hoặc Nhật ký. Nhật ký mặc định chỉ hiện thông báo gần nhất; bấm để mở toàn bộ và lưu ra file.
- Cửa sổ mặc định 1360×900, tối thiểu 1040×740. Khi thiếu chiều cao, ẩn banner trang trí để giữ các nút thao tác trong khung.
- Banner là hình minh họa đi kèm ứng dụng, không phải ảnh của Quest. Chế độ `--demo` được gắn nhãn và không chạy Quest thật.

![Giao diện Focus Flow với dữ liệu minh họa](docs/images/focus-flow.png)

## Phạm vi

- Quét các Quest hiện có và chỉ hiển thị Quest có thưởng Orbs.
- Hỗ trợ `WATCH_VIDEO`, `WATCH_VIDEO_ON_MOBILE`, `PLAY_ON_DESKTOP`, `PLAY_ON_DESKTOP_V2`, với cấu hình Quest cũ và `taskConfigV2`.
- Chạy tuần tự, tự nhận Quest chưa đăng ký, hiển thị tiến độ và nhận thưởng theo tùy chọn.
- Danh sách hàng đợi độc lập với dòng đang chọn và bộ lọc. Hoàn thành/nhận thưởng Quest trước rồi tự chuyển sang Quest sau; không cần bấm chạy lại sau mỗi Quest.
- Quest đã hoàn thành chỉ cần bước nhận thưởng. Lỗi riêng của một Quest hoặc lỗi nhận thưởng thông thường được ghi lại rồi chuyển Quest tiếp theo. Hàng đợi bị dừng do xác thực/hạn chế tài khoản giữ nguyên các mục còn chờ; nhật ký cho biết nguyên nhân. Bấm chạy lại chỉ xử lý các mục chưa hoàn thành/nhận thưởng theo tùy chọn hiện tại.
- Video báo tiến độ theo thời gian thực. Game dùng trạng thái nhận diện của Discord và heartbeat do Discord gửi.
- Phân biệt hoàn thành, đã nhận thưởng, lỗi, chưa hỗ trợ và đã dừng. Mốc tiến độ video tự báo không được tính là xác nhận hoàn thành.
- Hỗ trợ dừng, giới hạn thời gian chờ, chờ khi HTTP 429, ngừng khi HTTP 401/403 hoặc cần xác minh, và khôi phục các hàm nhận diện game.
- Không xử lý Quest chỉ dành cho console, stream, thành tích trong game hoặc Activity. Không tạo Quest mới, thay đổi điều kiện khu vực hay chi tiêu Orbs.
- Cột thưởng là **Orbs cơ bản** từ cấu hình Quest, không phải số dư hoặc cam kết số Orbs sẽ được ghi có sau các ưu đãi tài khoản.

## Kết nối và dữ liệu

Python chỉ kết nối tới CDP trên `127.0.0.1`, với cửa sổ thuộc tên miền Discord được xác định. Mã JavaScript chạy trong Discord dùng API client sẵn có của phiên. Không có backend, telemetry, tự đọc token, hoặc lưu thông tin đăng nhập.

Một số bản Discord không còn cho đọc bộ nhớ module sau khi khởi động. Bộ kết nối có thể thu thập **tham chiếu module trong bộ nhớ của chính Discord** khi tải lại, rồi tìm các store theo phương thức. Orbot chỉ nhận tên/ID tài khoản, thông tin Quest, trạng thái và nhật ký qua kết nối cục bộ. Khi đóng Orbot bình thường, bộ xử lý và preload được gỡ; nếu mất liên lạc, watchdog dừng hàng đợi sau khoảng 15 giây khi bộ hẹn giờ của Discord hoạt động.

Trong lúc xử lý game, Discord có thể hiển thị trạng thái chơi game tương ứng. Orbot không thay đổi cài đặt hiển thị hoạt động của tài khoản.

## Tương thích và kiểm chứng

Đã kiểm thử engine bằng dữ liệu Discord giả lập, kết nối HTTP/WebSocket cục bộ, giao diện Tk và khởi động EXE. Bản 0.1.2 đã xác minh API JSON khớp với phiên đăng nhập và đọc được danh sách Quest thật trên Discord Desktop 1.0.9263. Bản 0.1.3 thêm kiểm thử hàng đợi nhiều Quest, game → video, nhận thưởng, tiếp tục sau lỗi và dừng/chạy lại. **Chưa kiểm chứng hoàn thành/nhận thưởng bằng bản mới trên tài khoản thật.** API nội bộ, store và điều kiện xét Quest có thể thay đổi; khi không tương thích, Orbot hiển thị lỗi hoặc hết thời gian chờ.

Nếu Discord được cài ở vị trí khác, dùng hộp thoại chọn file EXE.

[Lịch sử thay đổi chi tiết](docs/CHANGELOG.md).

Discord cấm sử dụng hệ thống tự động hoặc bot để tích lũy Orbs; tài khoản có thể bị hạn chế hoặc đình chỉ. Xem [điều khoản Discord Orbs](https://discord.com/terms/paid-services-terms#discord-orbs). Orbot không phải công cụ được Discord phê duyệt.

## Phát triển

Python 3.12 trở lên, Windows 10/11. Node chỉ dùng để chạy kiểm thử engine.

```powershell
python -m venv .venv
python -m pip --python .venv/Scripts/python.exe install -r requirements-dev.txt
.venv/Scripts/python.exe -m orbot
.venv/Scripts/python.exe -m orbot --demo
```

Nếu bước tạo venv báo lỗi `ensurepip`, có thể tạo bằng `python -m venv --without-pip .venv` rồi dùng lệnh `python -m pip --python ...` bên trên. Pip của Python hệ thống cài vào môi trường riêng, không cần cài pip trong venv.

```powershell
node --test tests/engine.test.cjs
.venv/Scripts/python.exe -m unittest discover -s tests -p "test_*.py" -v
.venv/Scripts/python.exe scripts/gui_smoke.py
.venv/Scripts/python.exe -m ruff check orbot tests scripts run_orbot.py
.venv/Scripts/python.exe -m mypy orbot
.venv/Scripts/python.exe -m bandit -r orbot -ll
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build.ps1
```

Kiểm thử socket cần được phép kết nối `127.0.0.1`. Chế độ `--demo` dùng dữ liệu minh họa riêng và vô hiệu hóa mọi thao tác chạy Quest thật.

## Cấu trúc dự án

```text
Orbot/
├── Start-Orbot.cmd        # Mở bản chạy hiện tại
├── orbot/                # Mã nguồn và tài nguyên ứng dụng
├── scripts/              # Build, kiểm tra, tạo icon, chụp giao diện
├── tests/                # Kiểm thử engine và kết nối
├── docs/                 # Tài liệu, ảnh giao diện, concept và lịch sử
├── licenses/             # Giấy phép thư viện đi kèm
├── dist/                 # Chỉ bản EXE hiện tại, SHA-256 và hướng dẫn
└── .venv/                # Môi trường phát triển cục bộ
```

[Mục lục tài liệu](docs/README.md) · [Kiểm chứng](docs/VERIFICATION.md) · [Thiết kế](DESIGN.md)

Cache và file đóng gói tạm được gom vào `build/`, chỉ xuất hiện khi chạy các công cụ phát triển. Script build lấy phiên bản từ `orbot/__init__.py`, đặt file `.spec` trong `build/spec/` và xuất EXE vào `dist/`.

## Mã nguồn

- `orbot/app.py`: giao diện tiếng Việt.
- `orbot/workspace.py`: bố cục Focus Flow, điều hướng và cập nhật trình bày.
- `orbot/ui.py`: hàng đợi hỗ trợ bàn phím, banner và tiến độ.
- `orbot/controller.py`: hàng đợi và worker nền.
- `orbot/cdp.py`: kết nối và xác minh cửa sổ Discord.
- `orbot/engine.js`: chuẩn hóa Quest, tiến độ, hàng đợi và khôi phục.
- `orbot/capture.js`: thu thập module trong lúc tải lại khi cần.
- `orbot/launcher.py`: tìm và mở bản Discord sẵn có.

Bộ xử lý được viết riêng sau khi tham khảo cấu trúc Quest công khai trong [Orion](https://github.com/nyxxbit/discord-quest-completer) và [OrbSniper](https://github.com/syntaxixr/OrbSniper). Thư viện chạy gồm [websocket-client](https://github.com/websocket-client/websocket-client) và [Pillow](https://github.com/python-pillow/Pillow) để hiển thị ảnh và công tắc. Tcl/Tk và Python được đóng gói cùng EXE. Tất cả thư viện giữ giấy phép riêng.

Orbot được phân phối theo [giấy phép MIT](LICENSE).
