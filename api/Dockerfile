FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# pip 업데이트
RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 복사
COPY . .

CMD ["python", "main.py"]