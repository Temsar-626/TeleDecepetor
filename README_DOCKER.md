# راه‌اندازی TeleDeceptor با Docker

این راهنما نحوه راه‌اندازی پروژه TeleDeceptor با استفاده از Docker را توضیح می‌دهد.

## پیش‌نیازها

- Docker و Docker Compose نصب شده باشند
- داشتن API_ID و API_HASH از [my.telegram.org](https://my.telegram.org)
- در صورت استفاده از بات ادمین، یک BOT_TOKEN از [BotFather](https://t.me/BotFather) و ADMIN_ID کاربر تلگرام

## مراحل راه‌اندازی

1. ابتدا فایل `.env` را بر اساس نمونه `.env.example` ایجاد کنید:

```bash
cp .env.example .env
```

2. فایل `.env` را ویرایش کرده و اطلاعات خود را وارد کنید:

```
API_ID=12345
API_HASH=abcdef123456789
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
ADMIN_ID=123456789
```

3. ساخت و اجرای کانتینر Docker:

```bash
docker-compose up -d
```

4. مشاهده لاگ‌ها:

```bash
docker-compose logs -f
```

5. برای دسترسی به برنامه، به آدرس http://localhost:5000 در مرورگر خود بروید.

## توقف برنامه

برای توقف برنامه، دستور زیر را اجرا کنید:

```bash
docker-compose down
```

## عیب‌یابی

اگر با مشکلی مواجه شدید، ابتدا لاگ‌ها را با دستور زیر بررسی کنید:

```bash
docker-compose logs -f
```

اگر برنامه به درستی شروع نشد، می‌توانید کانتینر را بازسازی کنید:

```bash
docker-compose build --no-cache
docker-compose up -d
``` 