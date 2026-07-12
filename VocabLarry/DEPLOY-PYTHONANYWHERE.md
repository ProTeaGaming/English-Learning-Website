# Deploy VocabLarry lên PythonAnywhere (free)

Kết quả cuối: website chạy tại `https://<username>.pythonanywhere.com`, HTTPS sẵn,
giữ nguyên toàn bộ dữ liệu (5.000 từ, ngữ pháp) vì SQLite được upload kèm.

> Thay `USERNAME` trong toàn bộ hướng dẫn bằng username PythonAnywhere của bạn.
> Username chính là tên miền phụ, nên hãy chọn tên đẹp — ví dụ `vocablarry`
> → `vocablarry.pythonanywhere.com`.

---

## Bước 1 — Tạo tài khoản

1. Vào https://www.pythonanywhere.com → **Pricing & signup** → **Create a Beginner account** (miễn phí, không cần thẻ).
2. Xác nhận email đăng ký.

## Bước 2 — Upload code

File `vocablarry-deploy.zip` đã được tạo sẵn cạnh thư mục dự án
(đã loại `.env`, `admin-credentials.txt`, cache — và **có kèm** `db.sqlite3`).

1. Trên PythonAnywhere: tab **Files** → **Upload a file** → chọn `vocablarry-deploy.zip`.
2. Tab **Consoles** → **Bash**, chạy:

```bash
cd ~
unzip vocablarry-deploy.zip -d VocabLarry
```

## Bước 3 — Cài môi trường Python

Trong cùng Bash console:

```bash
mkvirtualenv vocablarry --python=python3.11
pip install -r ~/VocabLarry/requirements.txt
```

(Chờ vài phút. Nếu sau này mở console mới, gõ `workon vocablarry` để vào lại venv.)

## Bước 4 — Tạo file `.env` trên server

```bash
cd ~/VocabLarry
python -c "import secrets; print('DJANGO_SECRET_KEY=' + secrets.token_urlsafe(50))" > .env
cat >> .env << 'EOF'
DJANGO_DEBUG=false
ALLOWED_HOSTS=USERNAME.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://USERNAME.pythonanywhere.com

# Đăng ký/đăng nhập bằng email hoạt động ngay mà không cần SMTP:
EMAIL_VERIFICATION=optional

# Khi nào có Gmail App Password thì điền vào đây và đổi dòng trên
# thành EMAIL_VERIFICATION=mandatory (tài khoản PA free CHỈ gửi được
# qua smtp.gmail.com):
#SMTP_HOST=smtp.gmail.com
#SMTP_PORT=587
#SMTP_USER=youraccount@gmail.com
#SMTP_PASS=xxxx xxxx xxxx xxxx
#FROM_EMAIL=youraccount@gmail.com
#FROM_NAME=VocabLarry
EOF
nano .env   # sửa USERNAME thành username thật của bạn, Ctrl+O Enter Ctrl+X để lưu
```

## Bước 5 — Chuẩn bị static files + kiểm tra DB

```bash
cd ~/VocabLarry
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py check --deploy   # không còn cảnh báo đỏ nào là ổn
```

## Bước 6 — Tạo Web app

1. Tab **Web** → **Add a new web app** → chọn **Manual configuration** (KHÔNG chọn
   "Django" — mục đó tạo project mới) → **Python 3.11**.
2. Trong trang cấu hình web app, điền:
   - **Source code:** `/home/USERNAME/VocabLarry`
   - **Working directory:** `/home/USERNAME/VocabLarry`
   - **Virtualenv:** `/home/USERNAME/.virtualenvs/vocablarry`
3. Bấm vào link **WSGI configuration file** và thay TOÀN BỘ nội dung bằng:

```python
import os
import sys

path = '/home/USERNAME/VocabLarry'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

4. Kéo xuống mục **Static files**, thêm 2 dòng:

   | URL       | Directory                              |
   |-----------|----------------------------------------|
   | `/static/`| `/home/USERNAME/VocabLarry/staticfiles`|
   | `/media/` | `/home/USERNAME/VocabLarry/media`      |

   (Bắt buộc: khi `DEBUG=false` Django không tự phục vụ `/media/` nữa —
   thiếu dòng này thì ảnh đại diện người dùng sẽ lỗi 404.)

5. Mục **Security**: bật **Force HTTPS**.
6. Bấm nút **Reload** to màu xanh ở đầu trang.

## Bước 7 — Kiểm tra

- Mở `https://USERNAME.pythonanywhere.com` — trang chủ VocabLarry hiện ra,
  đủ 5.000 từ, chuyển tab Vocabulary/Grammar, đổi ngôn ngữ Anh/Việt.
- Đăng ký một tài khoản mới bằng email → đăng nhập → đánh dấu vài từ đã học
  → tải lại trang xem tiến độ có lưu không.
- Đăng nhập trang quản trị bằng tài khoản admin sẵn có trong DB
  (xem `admin-credentials.txt` trên máy của bạn — file này KHÔNG được upload).

## Lưu ý riêng cho tài khoản free

- **3 tháng phải bấm gia hạn 1 lần:** tab Web có nút "Run until 3 months from
  today" — bấm **Extend** trước ngày thi để web không bị tắt.
- **Email:** tài khoản free chỉ gửi được email qua `smtp.gmail.com`. Muốn bật
  xác minh email bắt buộc: tạo App Password trong Google Account (Security →
  2-Step Verification → App passwords), điền vào `.env`, đổi
  `EMAIL_VERIFICATION=mandatory`, rồi Reload web app.
- **Social login (Google/Facebook/...):** nút vẫn hiện nhưng chưa hoạt động cho
  tới khi bạn tạo OAuth app ở console của từng nhà cung cấp với callback
  `https://USERNAME.pythonanywhere.com/accounts/google/login/callback/`
  và điền client id/secret vào `.env`. Cho cuộc thi, demo đăng nhập email là đủ.
- **Cập nhật code sau này:** upload zip mới, unzip đè (`unzip -o`), chạy lại
  `collectstatic` + `migrate` nếu cần, rồi bấm **Reload**.
- **Sao lưu:** tải `db.sqlite3` về máy định kỳ (tab Files) — đó là toàn bộ
  dữ liệu người dùng.
