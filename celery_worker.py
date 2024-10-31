from main import celery, app

app.app_context().push()

if __name__ == '__main__':
    celery.start()