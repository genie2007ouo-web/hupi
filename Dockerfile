# 使用官方 Python 輕量版基底
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 複製套件清單並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有專案檔案（包含 main.py 與 tarot.json）
COPY . .

# 啟動機器人（假設你的主程式檔名是 main.py）
CMD ["python", "main.py"]