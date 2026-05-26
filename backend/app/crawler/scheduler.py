import schedule
import time
import threading
from app import create_app, db
from app.crawler.dldownload import run_crawl
import logging

log = logging.getLogger(__name__)

def crawl_job():
    app = create_app()
    with app.app_context():
        log.info('Running scheduled crawl...')
        run_crawl(max_pages=3)

def start_scheduler():
    schedule.every(6).hours.do(crawl_job)
    def run():
        while True:
            schedule.run_pending()
            time.sleep(60)
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    log.info('Scheduler started — crawling every 6 hours')