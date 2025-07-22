FROM python:3.9-slim

WORKDIR /app

# کپی فایل‌های وابستگی
COPY TeleDecepetor/requirements.txt .

# نصب وابستگی‌ها با نسخه‌های دقیق
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install werkzeug==2.0.3

# کپی کل پروژه
COPY . .

# متغیرهای محیطی مورد نیاز
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=TeleDecepetor/app.py

# اجرای برنامه
EXPOSE 5000
CMD ["python", "main.py"] 