FROM python:3.12-slim

WORKDIR /app

# 依存関係のインストールに必要なパッケージ
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# requirements.txtをコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードをコピー
COPY . .

# 実行コマンド (Gunicorn + Uvicorn workers for production)
# 4 workers as recommended for moderate workloads
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
