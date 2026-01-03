import os
import time
from apscheduler.schedulers.blocking import BlockingScheduler
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("INTERNAL_API_URL", "http://backend:8000")

def collect_job():
    print(f"[{time.ctime()}] Starting collection job...")
    try:
        response = requests.post(f"{API_URL}/api/news/collect")
        print(f"[{time.ctime()}] Job finished: {response.json()}")
    except Exception as e:
        print(f"[{time.ctime()}] Job failed: {e}")

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    # 毎時0分に実行 (必要に応じて調整)
    scheduler.add_job(collect_job, 'cron', minute=0)

    # 初回実行
    collect_job()

    print("Scheduler started. Press Ctrl+C to exit.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
