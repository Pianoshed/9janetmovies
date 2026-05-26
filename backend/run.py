from app import create_app
from app.crawler.scheduler import start_scheduler

app = create_app()

if __name__ == '__main__':
    start_scheduler()
    app.run(debug=True, port=5000)