FROM python:3.12-slim
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
# seed chạy lúc khởi động (an toàn khi chạy lại) vì thư mục instance được mount từ máy chủ
CMD ["sh", "-c", "python seed.py && python run.py"]
