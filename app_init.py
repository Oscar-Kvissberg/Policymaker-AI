from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
from config import Config
from flask.cli import AppGroup

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

custom_cli = AppGroup('custom')

# Importera modeller efter att db har initialiserats
from models import *

# Importera CLI-kommandon
import cli_commands
# Lägg till denna rad för att upptäcka uppgifter
celery.autodiscover_tasks(['main'])
