# SKILL: Auto Push to GitHub (Safe)

## Mô tả
Skill này giúp push code lên GitHub một cách **an toàn**, tự động kiểm tra không có thông tin bí mật bị leak trước khi push.

---

## Khi nào dùng skill này

Dùng khi user yêu cầu:
- "push code lên github"
- "push lên git"
- "commit và push"
- "đẩy code lên"
- "upload code"

---

## Các bước thực hiện (theo thứ tự)

### Bước 1 — Kiểm tra bảo mật TRƯỚC khi push

Chạy lệnh kiểm tra xem có file bí mật nào bị staged không:

```powershell
git status --short
```

**Kiểm tra bắt buộc:** File `.env` KHÔNG được xuất hiện trong danh sách staged (ký hiệu `A` hoặc `M` phía trước).

Nếu thấy `.env` bị staged → chạy ngay:
```powershell
git rm --cached .env
```

Kiểm tra thêm xem có key nào bị hardcode trong staged files không:
```powershell
git diff --cached | Select-String -Pattern "AIzaSy|GOCSPX|client_secret\s*=\s*['\"][^'\"]+|password\s*=\s*['\"][^'\"]+" -CaseSensitive
```

Nếu có kết quả → **DỪNG LẠI**, báo user biết và yêu cầu fix trước khi push.

---

### Bước 2 — Hỏi user commit message

Hỏi user: **"Bạn muốn đặt tên commit là gì?"**

Nếu user không cung cấp, dùng format mặc định dựa trên các file đã thay đổi:
- Có thay đổi controllers → `"Update controllers"`
- Có thay đổi templates → `"Update UI templates"`
- Có thay đổi database.py → `"Update database logic"`
- Nhiều loại → `"Update project files"`

---

### Bước 3 — Stage và commit

```powershell
git add .
git commit -m "<commit_message_từ_user>"
```

---

### Bước 4 — Push lên GitHub

```powershell
git push origin master
```

Nếu lỗi `rejected` (do remote có commits mới hơn):
```powershell
git pull --rebase origin master
git push origin master
```

---

### Bước 5 — Xác nhận thành công

Sau khi push xong, báo kết quả cho user:
- ✅ Link GitHub repo: lấy từ `git remote get-url origin`
- ✅ Tên commit vừa push
- ✅ Số file thay đổi
- ✅ Xác nhận `.env` không bị push

---

## Các lỗi thường gặp và cách xử lý

| Lỗi | Nguyên nhân | Cách fix |
|-----|-------------|----------|
| `rejected - non-fast-forward` | Remote có commit mới | `git pull --rebase origin master` rồi push lại |
| `Authentication failed` | Chưa đăng nhập GitHub | Hướng dẫn dùng Personal Access Token |
| `src refspec master does not match` | Chưa có commit nào | Chạy `git add . && git commit -m "..."` trước |
| `.env` bị staged | .gitignore chưa đúng | `git rm --cached .env` và kiểm tra .gitignore |

---

## Lưu ý quan trọng

- **KHÔNG BAO GIỜ** push nếu phát hiện `.env` hoặc API key trong staged files
- **LUÔN** kiểm tra bảo mật ở Bước 1 trước khi làm bất cứ thứ gì
- Nếu user yêu cầu push kể cả có leak → từ chối và giải thích rủi ro
