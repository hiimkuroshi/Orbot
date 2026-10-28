# Phát hành Orbot

## Quy trình

1. Cập nhật `orbot/__init__.py` và [CHANGELOG.md](CHANGELOG.md), merge vào `main`.
2. Thử bản build trước khi phát hành: mở lần chạy **Build Windows** của commit trên `main`, tải `orbot-windows-x64` trong mục **Artifacts** và thử với Discord thật.
3. Phát hành trên web, không cần git: mở tab **Actions → Build Windows → Run workflow**, giữ nhánh `main`, đánh dấu **Phát hành phiên bản trong orbot/__init__.py**, rồi bấm **Run workflow**.

   Hoặc, từ máy có bản clone, đẩy tag trùng phiên bản:

   ```bash
   git tag v0.2.1
   git push origin v0.2.1
   ```

4. Workflow [Build Windows](../.github/workflows/build.yml) chạy kiểm thử, build ZIP dạng thư mục và EXE một file, kiểm tra `SHA256SUMS.txt`, tạo chứng nhận nguồn gốc (attestation) rồi **công bố ngay** bản phát hành và đánh dấu Latest. Workflow dừng nếu tag khác phiên bản trong mã, nếu nút phát hành được bấm trên nhánh khác `main`, hoặc nếu tag của phiên bản đã tồn tại.

Không phát hành file build trên máy cá nhân. Nếu bản phát hành có lỗi, sửa trong Releases (chuyển về bản nháp hoặc xóa) rồi phát hành bản vá với phiên bản mới.

Mỗi lần push, workflow cũng chạy kiểm thử và build; file build nằm trong mục **Artifacts** của lần chạy, giữ 30 ngày.

Thư viện cài trong CI lấy từ `requirements-lock.txt` với `--require-hashes`, nên một gói bị thay thế trên PyPI sẽ làm build thất bại thay vì lọt vào bản phát hành. Các GitHub Action được ghim theo mã commit.

## Cảnh báo SmartScreen

Thông báo "Windows đã bảo vệ máy tính của bạn" đến từ SmartScreen. SmartScreen dựa vào **uy tín**: file chưa ký số được tính uy tín theo từng mã băm, nên mỗi bản mới bắt đầu lại từ đầu. Không có cách miễn phí làm cảnh báo biến mất ngay. Những việc giúp giảm cảnh báo:

### 1. Gửi file cho Microsoft (miễn phí)

1. Mở <https://www.microsoft.com/en-us/wdsi/filesubmission>, đăng nhập tài khoản Microsoft và chọn **Software developer**.
2. Tải lên file ZIP và EXE của bản phát hành (mỗi file một lần gửi), chọn sản phẩm **Microsoft Defender SmartScreen**, ghi rõ đây là ứng dụng mã nguồn mở, kèm link repo và link bản phát hành.
3. Thời gian xử lý tùy Microsoft. Kết quả không được đảm bảo, và phải gửi lại cho mỗi bản mới.

Nếu Microsoft Defender (không phải SmartScreen) báo tên mối đe dọa, gửi theo cùng trang, chọn **Microsoft Defender Antivirus** và ghi tên mối đe dọa.

### 2. Xin ký số miễn phí từ SignPath Foundation

[SignPath Foundation](https://signpath.org) cấp ký số miễn phí cho dự án mã nguồn mở có giấy phép OSI (MIT đạt yêu cầu), build công khai trên CI. Khi được duyệt, file hiển thị nhà phát hành là SignPath Foundation, và uy tín SmartScreen được cộng dồn theo chứng chỉ qua các bản phát hành thay vì mất sau mỗi bản.

- Đăng ký trên trang SignPath; họ xét duyệt từng dự án và **có thể từ chối**, đặc biệt với công cụ tự động hóa dịch vụ của bên thứ ba như Orbot.
- Khi được duyệt, chèn bước ký của SignPath vào job `release` trước bước **Attest build provenance** (ký trước, chứng nhận file đã ký sau).

### 3. Những gì đã áp dụng trong build

- Bản ZIP dạng thư mục: không tự giải nén vào `%TEMP%` như EXE một file, ít bị chương trình diệt virus báo nhầm hơn.
- Không nén bằng UPX; EXE có thông tin phiên bản (tên sản phẩm, phiên bản, bản quyền).
- Build công khai trên GitHub Actions, có mã SHA-256 và chứng nhận nguồn gốc để người dùng tự kiểm tra.

Không dùng công cụ làm rối mã hoặc đóng gói lại để né phần mềm diệt virus: cách đó làm file giống phần mềm độc hại hơn và vi phạm điều kiện của các chương trình ký số.

## Ẩn email trong commit

Commit `43a3139` ghi email cá nhân và repo đang công khai. Để các commit sau không lộ email:

1. GitHub → **Settings → Emails**: bật **Keep my email addresses private** và **Block command line pushes that expose my email**.
2. Trên máy cá nhân:

   ```bash
   git config --global user.email "86469475+hiimkuroshi@users.noreply.github.com"
   ```

Commit cũ vẫn giữ email. Viết lại lịch sử để xóa cần force-push lên `main` và làm thay đổi mọi mã commit, nên chỉ làm khi thật cần.
