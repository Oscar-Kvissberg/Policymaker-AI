from flask import Flask, render_template, request, send_file, redirect, url_for, flash, jsonify, current_app, session
import os
import json
from datetime import datetime, timedelta
import pytz
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT
from io import BytesIO
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_mail import Mail, Message
import threading
import time
import logging
from googletrans import Translator
from dateutil.parser import parse
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, cast, String, or_
from config import Config
from urllib.parse import quote
from itertools import zip_longest
import re
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import inspect
from sqlalchemy import text
import click
from flask.cli import with_appcontext, AppGroup
from celery import Celery
from email.header import Header
from celery.app.control import Inspect as inspect
from celery.contrib.abortable import AbortableTask
import traceback
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from google.cloud.sql.connector import Connector
import sqlalchemy
import pg8000
from google.cloud import secretmanager
from google.oauth2 import service_account
import google.auth
from google.auth import exceptions as auth_exceptions
import pandas as pd
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from tenacity import retry, stop_after_attempt, wait_exponential
from contextlib import contextmanager
import socket
from secrets import token_urlsafe

# Konfigurera loggning
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Konfigurera loggning för Google Cloud-klienten
logging.getLogger('google.auth').setLevel(logging.DEBUG)
logging.getLogger('google.cloud').setLevel(logging.DEBUG)

# Funktion för att säkert hämta miljövariabler
def get_env_variable(name):
    try:
        return os.environ[name]
    except KeyError:
        logger.error(f"Miljövariabeln {name} är inte satt.")
        return None

# Hämta DB_PASSWORD och PRIVATE_KEY
db_password = get_env_variable('DB_PASSWORD')
private_key = get_env_variable('PRIVATE_KEY')

if not db_password:
    logger.error("DB_PASSWORD är inte satt.")

if not private_key:
    logger.error("PRIVATE_KEY är inte satt.")
else:
    # Försök att formatera private_key korrekt om det behövs
    if "-----BEGIN PRIVATE KEY-----" not in private_key:
        private_key = f"-----BEGIN PRIVATE KEY-----\n{private_key}\n-----END PRIVATE KEY-----\n"
    private_key = private_key.replace("\\n", "\n")  # Ersätt eventuella literala "\n" med faktiska radbrytningar

# Skapa ett service account info dictionary
service_account_info = {
    "type": "service_account",
    "project_id": "southern-idea-438120-s0",
    "private_key_id": "8654f7b72ad814b182a4756f16128dc4acfb2d8d",
    "private_key": private_key,
    "client_email": "catalinasoftwaresolutions@southern-idea-438120-s0.iam.gserviceaccount.com",
    "client_id": "103099295167011591369",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/catalinasoftwaresolutions%40southern-idea-438120-s0.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# Skapa credentials
try:
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    logger.info("Credentials skapade framgångsrikt")
except Exception as e:
    logger.error(f"Fel vid skapande av credentials: {str(e)}")
    credentials = None

# Skapa Flask-app
app = Flask(__name__, static_folder=os.path.abspath('static'), static_url_path='/statics')
app.config.from_object(Config)

# Funktion för att skapa databasanslutning
def getconn():
    logger.info("Försöker ansluta till databasen...")
    try:
        connector = Connector(credentials=credentials)
        logger.info("Connector skapad med credentials")
        logger.info(f"Ansluter till: southern-idea-438120-s0:us-central1:psql-f799")
        conn = connector.connect(
            "southern-idea-438120-s0:us-central1:psql-f799",
            "pg8000",
            user="postgres",
            password=db_password,
            db="policymaker"
        )
        logger.info("Anslutning lyckades")
        return conn
    except auth_exceptions.DefaultCredentialsError as e:
        logger.error(f"Autentiseringsfel: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Fel vid anslutning till databasen: {str(e)}")
        logger.error(f"Typ av fel: {type(e).__name__}")
        logger.error(f"Felmeddelande: {str(e)}")
        raise

# Konfigurera SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+pg8000://"
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "creator": getconn
}

# Initiera SQLAlchemy och Migrate
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#      celery -A main.celery worker --loglevel=info (kör i terminalen för att starta celery)
#      python run_command.py custom rensa-skickade-paminda "klubbnamn" (för att rensa skickade och påminda poster för Liverpool FC)
#      python run_command.py custom delete-club "klubbnamn"    fÖR ATT TA BORT EN KLUBB
#      gcloud sql connect psql-f799 --user=postgres (för att komma åt databasen),   \l    (för att se databaser),  \c policymaker    (för att välja databasen),   \dt     (för att se tabeller),  SELECT * FROM tablename; (för att se innehållet i en tabell)
# Konfigurera Celery med RabbitMQ
# Användarnamn: jcmvijwi
# Lösenord: eabQ8Q3VWD0oiz0W1AipFQynIB-TA64g
rabbitmq_url = os.environ.get('RABBITMQ_URL', 'amqps://jcmvijwi:eabQ8Q3VWD0oiz0W1AipFQynIB-TA64g@hawk.rmq.cloudamqp.com/jcmvijwi')
celery = Celery(app.name, broker=rabbitmq_url)
celery.conf.update(app.config)

# Definiera en anpassad Task-klass för att hantera Flask-appkontexten
class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)

celery.Task = ContextTask

# Konfigurera loggning
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app.logger.setLevel(logging.WARNING)  # eller logging.ERROR för ännu mindre loggning

# Stäng av loggning för werkzeug (HTTP-förfrågningar) och andra mindre viktiga loggar
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
logging.getLogger('flask_mail').setLevel(logging.ERROR)

# Uppdatera Celery-konfigurationen
celery.conf.update(
    broker_url=rabbitmq_url,
    result_backend='rpc://',
    task_track_started=True,
    task_publish_retry=True,
    broker_connection_retry_on_startup=True,
    worker_log_format='%(asctime)s - %(levelname)s: %(message)s',
    worker_task_log_format='%(asctime)s - %(levelname)s: %(message)s',
    timezone='Europe/Stockholm',  # Lägg till denna rad
    enable_utc=False,  # Lägg till denna rad
    task_acks_late=True,  # Ändra till True här
    task_reject_on_worker_lost=True,
    task_acks_on_failure_or_timeout=True,
    broker_transport_options={
        'visibility_timeout': 300,  # 5 minuter
        'max_retries': 3,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.5,
    },
    task_default_rate_limit='10/m',  # Begränsa antalet uppgifter per minut
    worker_prefetch_multiplier=1,  # Förhindra att arbetare hämtar för många uppgifter samtidigt
)

@celery.task
def clean_queue():
    app.logger.info("Rensar kn från inaktiva uppgifter")
    i = celery.control.inspect()
    active = i.active()
    scheduled = i.scheduled()
    reserved = i.reserved()

    all_tasks = []
    if active:
        all_tasks.extend([task['id'] for worker_tasks in active.values() for task in worker_tasks])
    if scheduled:
        all_tasks.extend([task['id'] for worker_tasks in scheduled.values() for task in worker_tasks])
    if reserved:
        all_tasks.extend([task['id'] for worker_tasks in reserved.values() for task in worker_tasks])

    for task_id in all_tasks:
        task = celery.AsyncResult(task_id)
        if task.state in ['PENDING', 'RECEIVED', 'STARTED'] and (datetime.now() - task.date_done).total_seconds() > 300:
            app.logger.info(f"Tar bort inaktiv uppgift {task_id}")
            celery.control.revoke(task_id, terminate=True)

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60.0, check_celery_status.s(), name='check celery status every minute')
    sender.add_periodic_task(3600.0, clean_old_tasks.s(), name='clean old tasks every hour')
    sender.add_periodic_task(30.0, monitor_active_tasks.s(), name='monitor active tasks every 30 seconds')
    sender.add_periodic_task(300.0, clean_queue.s(), name='clean queue every 5 minutes')

@celery.task
def check_celery_status():
    app.logger.info("Celery is running and processing tasks")
    # Lägg till mer detaljerad information här om nödvändigt

@celery.task
def clean_old_tasks():
    try:
        i = inspect(app=celery)
        active_tasks = i.active()
        reserved_tasks = i.reserved()

        app.logger.info(f"Aktiva uppgifter: {active_tasks}")
        app.logger.info(f"Reserverade uppgifter: {reserved_tasks}")

        # Rensa gamla SentEmail-poster
        cutoff_date = datetime.now() - timedelta(days=7)
        deleted = SentEmail.query.filter(SentEmail.status == "Skickad", SentEmail.date < cutoff_date).delete()
        db.session.commit()
        app.logger.info(f"Raderade {deleted} gamla SentEmail-poster")
    except Exception as e:
        app.logger.error(f"Fel vid rensning av gamla uppgifter: {str(e)}")
        app.logger.error(traceback.format_exc())
        db.session.rollback()

# Lägg till denna funktion någonstans i din kod, förslagsvis nära de andra Celery-relaterade funktionerna
@celery.task
def monitor_active_tasks():
    i = celery.control.inspect()
    active_tasks = i.active()
    scheduled_tasks = i.scheduled()
    app.logger.info(f"Aktiva uppgifter: {active_tasks}")
    app.logger.info(f"Schemalagda uppgifter: {scheduled_tasks}")

# Uppdatera send_reminder_email_task
@celery.task(name='tasks.send_reminder_email_task', bind=True, base=AbortableTask, max_retries=3, priority=10, acks_late=True)
def send_reminder_email_task(self, recipient, klubb):
    start_time = time.time()
    task_id = self.request.id
    app.logger.info(f"Börjar bearbeta påminnelseuppgift {task_id} för {recipient['name']} ({klubb})")
    try:
        with app.app_context():
            name = recipient['name']
            email = recipient['email']

            if not name or not email:
                app.logger.error(f"Ogiltig mottagare för påminnelse: {recipient}")
                return False

            # Kontrollera om personen redan har signerat
            if Signature.query.filter_by(namn=name, klubb=klubb, email=email).first():
                app.logger.info(f"{name} ({email}) har redan signerat för {klubb}")
                return False

            # Hämta SentEmail-post
            sent_email = SentEmail.query.filter_by(klubb=klubb, name=name, email=email).first()
            if not sent_email:
                app.logger.info(f"Ingen SentEmail-post hittades för påminnelse till {name} ({email})")
                return False

            # Kontrollera om en påminnelse redan har skickats inom de senaste 24 timmarna
            if sent_email.status == "Påmind" and (datetime.now() - sent_email.date) < timedelta(hours=24):
                app.logger.info(f"Påminnelse har redan skickats till {name} ({email}) för {klubb} inom de senaste 24 timmarna")
                return False

            # Skicka påminnelse-e-postmeddelandet
            base_url = get_base_url()
            personal_link = f"{base_url}/?name={quote(name)}&club={quote(klubb)}&email={quote(email)}"
            subject = f'Påminnelse: Signera policy för {klubb}'
            
            html_content = f"""
            <html>
            <body>
                <p>Hej {name},</p>
                <p>Vi vill vänligen påminna dig om att läsa igenom och signera den gällande policyn för {klubb}. <br>
                Det är viktigt att denna process fullföljs inom kort för att säkerställa att du följer de aktuella riktlinjerna och kraven.<br>
                Klicka nedan för att läsa och signera policyn: <br>
                <table cellspacing="0" cellpadding="0">
                    <tr>
                        <td align="center" width="200" height="40" bgcolor="#9b59b6" style="color: #ffffff; display: block;">
                            <a href="{personal_link}" 
                               style="font-size:16px; font-weight: bold; font-family: sans-serif; text-decoration: none; line-height:40px; width:100%; display:inline-block">
                                <span style="color: #ffffff;">
                                    Läs policy
                                </span>
                            </a>
                        </td>
                    </tr>
                </table>
                <p>Vänliga hälsningar,<br>Catalina Software Solutions</p>
            </body>
            </html>
            """

            if send_email(subject, html_content, email):
                app.logger.info(f"Påminnelse med HTML skickad till {name} ({email}) för {klubb}")

                # Uppdatera status till "Påmind" och datum
                sent_email.status = "Påmind"
                sent_email.date = datetime.now()
                db.session.commit()

                processing_time = time.time() - start_time
                app.logger.info(f"Påminnelseuppgift {task_id} slutförd för {recipient['name']} ({klubb}). Tid: {processing_time:.2f} sekunder")
                
                return True
            else:
                app.logger.error(f"Fel vid sändning av påminnelse till {name} ({email}) för {klubb}")
                return False
    except Exception as exc:
        app.logger.error(f"Fel vid sändning av påminnelse (uppgift {task_id}): {str(exc)}")
        raise
    finally:
        app.logger.info(f"Påminnelseuppgift {task_id} avslutas")
        self.request.chain = None
        self.request.callbacks = None
        self.update_state(state='SUCCESS')

# Uppdatera Flask-appens konfiguration för att använda samma RabbitMQ-URL
app.config['CELERY_BROKER_URL'] = rabbitmq_url
celery.conf.update(app.config)

# Definiera modeller
class Policy(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    internal_id = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    klubb = db.Column(db.String(100), nullable=False)
    policy_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

class Signature(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    internal_id = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    namn = db.Column(db.String(100), nullable=False)
    klubb = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    datum = db.Column(db.DateTime, nullable=False)

class SentEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    internal_id = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    klubb = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # "Skickad", "Påmind", eller "Signerad"

class Club(db.Model):
    __tablename__ = 'club'
    id = db.Column(db.Integer, primary_key=True)
    klubb = db.Column(db.String(100), nullable=False)
    namn = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255))
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiry = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def generate_reset_token(self):
        self.reset_token = token_urlsafe(32)
        self.reset_token_expiry = datetime.now() + timedelta(hours=24)
        return self.reset_token

app.secret_key = 'din_hemliga_nyckel_här'  # Ändra detta till en säker, slumpmässig sträng

# Lägg till dessa konfigurationer
import os

# Lägg till dessa konfigurationer i din app-konfiguration
app.config['SENDGRID_API_KEY'] = os.environ.get('SENDGRID_API_KEY')
app.config['SENDGRID_DEFAULT_FROM'] = 'oscarkvissberg@gmail.com'


# Stäng av SMTP-debugging
import smtplib
smtplib.SMTP.debuglevel = 0

# Stäng av all SMTP-relaterad loggning
logging.getLogger("mail").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

translator = Translator()

def get_available_clubs():
    return [club.klubb for club in Policy.query.with_entities(Policy.klubb).distinct()]

def send_email(subject, body, to_email):
    message = Mail(
        from_email=app.config['SENDGRID_DEFAULT_FROM'],
        to_emails=to_email,
        subject=subject,
        html_content=body)
    try:
        sg = SendGridAPIClient(app.config['SENDGRID_API_KEY'])
        response = sg.send(message)
        app.logger.info(f"E-post skickad till {to_email}, status kod: {response.status_code}")
        return True
    except Exception as e:
        app.logger.error(f"Fel vid sändning av e-post: {str(e)}")
        return False

def get_base_url():
    return "https://c4f1efc6-4c30-41a4-be21-2b361a6f71e7-00-2611blikl0bn1.spock.replit.dev/"  # Lokal utvecklingsserver
    #return "https://policymaker-oscarkvissberg.replit.app" #För online versionen.

def build_external_url(endpoint, **values):
    base_url = get_base_url()
    if endpoint == 'index':
        encoded_values = {k: quote(v) for k, v in values.items()}
        return f"{base_url}/?name={encoded_values['name']}&club={encoded_values['club']}&email={encoded_values['email']}"
    # Lgg till fler endpoints vid behov
    return base_url

@app.route('/')
def index():
    name = request.args.get('name', '')
    club = request.args.get('club', '')
    email = request.args.get('email', '')

    if not name or not club or not email:
        return redirect(url_for('valj_klubb'))

    klubbar = get_available_clubs()
    return render_template('index.html', klubbar=klubbar, name=name, club=club, email=email)

@app.route('/policy', methods=['POST'])
def policy():
    name = request.form.get('name')
    klubb_namn = request.form.get('club')
    position = request.form.get('position', 'Position saknas')
    email = request.form.get('email')
    language = request.form.get('language', 'sv')
    if not name or not klubb_namn or not email:
        return "Ogiltig begäran. Namn, klubb och e-post mste anges.", 400

    policy_data = get_policy(klubb_namn)
    if not policy_data:
        return f"Policy för {klubb_namn} hittades inte.", 404

    # Översätt sektioner och frgor
    translated_policy = {
        'title': [translate_text(title, language) for title in policy_data['title']],
        'content': [translate_text(content, language) for content in policy_data['content']],
        'questions': [
            {
                'text': translate_text(q['text'], language),
                'correct_answer': q['correct_answer']
            } for q in policy_data['questions']
        ]
    }

    messages = {
        "name": translate_text("Namn", language),
        "position": translate_text("Position", language),
        "email": translate_text("E-post", language),
        "questions": translate_text("Frågor", language),
        "true": translate_text("Sant", language),
        "false": translate_text("Falskt", language),
        "wrong_answer": translate_text("Fel svar. Försök igen.", language),
        "check_answers": translate_text("Kontrollera svar", language),
        "sign_policy": translate_text("Signera policy", language),
        "congratulations": translate_text("Grattis! Alla rätt, du kan nu gå vidare och signera policyn för ", language)
    }

    # Skapa en lista av tupler med titel och innehåll
    policy_sections = list(zip_longest(translated_policy['title'], translated_policy['content']))

    return render_template('policy.html', 
                           club=klubb_namn,
                           policy_sections=policy_sections,
                           questions=translated_policy['questions'],
                           name=name, 
                           position=position,
                           email=email,
                           language=language,
                           messages=messages)

@app.route('/sign_policy', methods=['POST'])
def sign_policy():
    print("sign_policy funktion anropad")
    app.logger.debug("sign_policy funktion anropad")
    app.logger.debug(f"Formulärdata: {request.form}")
    name = request.form.get('name')
    club = request.form.get('club')
    position = request.form.get('position')
    email = request.form.get('email')
    language = request.form.get('language')

    app.logger.debug(f"Extraherade data: name={name}, club={club}, position={position}, email={email}, language={language}")

    try:
        spara_signatur(name, club, position, email)
        app.logger.info(f"Signatur sparad för {name}")
    except Exception as e:
        app.logger.exception(f"Fel vid sparande av signatur: {str(e)}")
        return f"Ett fel uppstod vid sparande av signatur: {str(e)}", 500

    confirmation_url = url_for('confirmation', name=name, club=club, position=position, email=email, language=language)
    app.logger.info(f"Omdirigerar till: {confirmation_url}")
    return redirect(confirmation_url)

@app.route('/confirmation')
def confirmation():
    app.logger.debug(f"confirmation anropad med args: {request.args}")
    name = request.args.get('name')
    club = request.args.get('club')
    position = request.args.get('position')
    email = request.args.get('email')
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    language = request.args.get('language', 'sv')

    translated_messages = {
        "title": translate_text("Policy Signerad", language),
        "thank_you": translate_text("Tack för att du har signerat policyn!", language),
        "name": translate_text("Namn", language),
        "club": translate_text("Klubb", language),
        "position": translate_text("Position", language),
        "email": translate_text("E-post", language),
        "date": translate_text("Datum för signering", language),
        "download_pdf": translate_text("Ladda ner PDF", language)
    }

    return render_template('confirmation.html', name=name, club=club, position=position, email=email, date=date, messages=translated_messages, language=language)

@app.route('/download_pdf')
def download_pdf():
    try:
        name = request.args.get('name', 'Namn saknas')
        club = request.args.get('club', 'Klubb saknas')
        position = request.args.get('position', 'Position saknas')
        date = request.args.get('date', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        language = request.args.get('language', 'sv')

        # Hmta policy-information för den valda klubben
        policy_data = get_policy(club)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        styles = getSampleStyleSheet()

        # Skapa en ny stil för vänsterjusterad text
        styles.add(ParagraphStyle(name='LeftAligned', parent=styles['Normal'], alignment=TA_LEFT))

        story = []

        # Lägg till rubrik
        story.append(Paragraph(translate_text(f"{club} Policy", language), styles['Title']))
        story.append(Spacer(1, 12))

        # Lägg till användarinformation
        story.append(Paragraph(translate_text(f"Namn: {name}", language), styles['LeftAligned']))
        story.append(Paragraph(translate_text(f"Position: {position}", language), styles['LeftAligned']))
        story.append(Paragraph(translate_text(f"Datum för signering: {date}", language), styles['LeftAligned']))
        story.append(Spacer(1, 12))

        # Lägg till policy-sektioner
        if policy_data:
            for title, content in zip(policy_data['title'], policy_data['content']):
                story.append(Paragraph(translate_text(title, language), styles['Heading2']))
                story.append(Paragraph(translate_text(content, language), styles['LeftAligned']))
                story.append(Spacer(1, 12))

            # Lägg till frgor
            story.append(Paragraph(translate_text("Frgor", language), styles['Heading2']))
            for question in policy_data['questions']:
                story.append(Paragraph(translate_text(question['text'], language), styles['LeftAligned']))
                story.append(Paragraph(translate_text(f"Korrekt svar: {'Sant' if question['correct_answer'] else 'Falskt'}", language), styles['LeftAligned']))
                story.append(Spacer(1, 6))

        doc.build(story)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f'{club}_policy.pdf', mimetype='application/pdf')
    except Exception as e:
        print(f"Ett fel uppstod: {str(e)}")
        return translate_text(f"Ett fel uppstod vid generering av PDF: {str(e)}", language), 500

@app.route('/generera_policy', methods=['GET', 'POST'])
def generera_policy():
    print(f"Metod: {request.method}")  # Debug-utskrift
    if request.method == 'POST':
        # Hantera POST-förfrågan (när formuläret skickas)
        # ... (din kod för att hantera formulärdata)
        pass
    else:
        # Visa formuläret (GET-förfrågan)
        return render_template('generera_policy.html')

@app.route('/skicka_policy_info', methods=['POST'])
def skicka_policy_info():
    print("skicka_policy_info anropad")  # Debug-utskrift
    klubb = request.form['klubb']
    namn = request.form['namn']
    username = request.form['username']
    email = request.form['email']
    losenord = request.form['losenord']

    # Kontrollera om användarnamnet redan existerar
    existing_user = Club.query.filter_by(username=username).first()
    if existing_user:
        flash('Användarnamnet är redan taget. Vänligen välj ett annat.', 'error')
        return redirect(url_for('generera_policy'))

    # Skapa ny klubb/användare och spara i databasen
    hashed_password = generate_password_hash(losenord)
    new_club = Club(klubb=klubb, namn=namn, username=username, email=email, password_hash=hashed_password)
    
    try:
        db.session.add(new_club)
        db.session.commit()
        # Ta bort flash-meddelandet här
        return redirect(url_for('generera_policy_inskickat'))
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Fel vid sparande av klubb/användare: {str(e)}")
        flash('Ett fel uppstod vid registrering. Vänligen försök igen.', 'error')
        return redirect(url_for('generera_policy'))

# Lägg till denna nya route fr att hantera den nya sidan
@app.route('/generera_policy_inskickat')
def generera_policy_inskickat():
    return render_template('generera_policy_inskickat.html')

@app.route('/valj_klubb', methods=['GET', 'POST'])
def valj_klubb():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = Club.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['klubb'] = user.klubb
            return redirect(url_for('visa_klubboversikt'))
        else:
            return render_template('valj_klubb.html', error='Felaktigt användarnamn eller lösenord')
    
    return render_template('valj_klubb.html')

@app.route('/visa_klubboversikt')
def visa_klubboversikt():
    if 'user_id' not in session:
        return redirect(url_for('valj_klubb'))
    
    klubb = session['klubb']
    
    # Hämta policyinformation
    policy_data = get_policy(klubb)

    # Hämta data från SentEmail
    sent_emails = SentEmail.query.filter_by(klubb=klubb).all()
    sent_email_data = [{
        'internal_id': str(item.internal_id),  # Konvertera UUID till sträng
        'name': item.name,
        'email': item.email,
        'date': item.date,
        'status': item.status
    } for item in sent_emails]

    # Hämta data från Signature
    signatures = Signature.query.filter_by(klubb=klubb).all()
    signature_data = [{
        'internal_id': str(item.internal_id),  # Lägg till denna rad
        'name': item.namn,
        'email': item.email,
        'date': item.datum,
        'status': 'Signerad'
    } for item in signatures]

    # Kombinera data från båda källorna
    all_data = sent_email_data + signature_data

    # Sortera data efter datum, med de senaste först
    sorted_data = sorted(all_data, key=lambda x: x['date'], reverse=True)

    # Ta bort dubbletter, behåll den senaste posten för varje unik kombination av e-post och namn
    unique_data = {}
    for item in sorted_data:
        key = (item['email'], item['name'])
        if key not in unique_data or item['date'] > unique_data[key]['date']:
            unique_data[key] = item

    final_data = list(unique_data.values())

    return render_template('klubboversikt.html', klubb=klubb, all_data=final_data, policy_data=policy_data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('valj_klubb'))

def get_signaturer_for_klubb(klubb):
    signatures = Signature.query.filter_by(klubb=klubb).all()
    return [{'internal_id': str(s.internal_id), 'name': s.namn, 'email': s.email, 'date': s.datum, 'status': 'Signerad'} for s in signatures]

def get_sent_emails_for_klubb(klubb):
    sent_emails = SentEmail.query.filter_by(klubb=klubb).all()
    return [{'internal_id': str(s.internal_id), 'name': s.name, 'email': s.email, 'date': s.date or datetime.min, 'status': s.status} for s in sent_emails]

def spara_signatur(namn, klubb, position, email):
    # Kontrollera om signaturen redan finns baserat på både namn och e-post
    existing_signature = Signature.query.filter_by(namn=namn, klubb=klubb, email=email).first()
    if existing_signature:
        app.logger.info(f"Signatur finns redan för {namn}, {klubb}, {email}")
        return

    try:
        with db.session.begin_nested():
            # Ta bort från SentEmail
            deleted = SentEmail.query.filter_by(klubb=klubb, name=namn, email=email).delete()
            app.logger.info(f"Raderade {deleted} post(er) från SentEmail för {namn} ({email})")

            # Lägg till i Signature
            new_signature = Signature(namn=namn, klubb=klubb, position=position, email=email, datum=datetime.now())
            db.session.add(new_signature)

        db.session.commit()
        app.logger.info(f"Signatur sparad: {namn}, {klubb}, {position}, {email}")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Fel vid sparande av signatur och borttagning frn SentEmail: {str(e)}")
        raise

def update_sent_emails_status(klubb, email, name, new_status, internal_id=None):
    if internal_id:
        sent_email = SentEmail.query.filter_by(internal_id=internal_id).first()
    else:
        sent_email = SentEmail.query.filter_by(klubb=klubb, name=name, email=email).first()

    if sent_email:
        sent_email.status = new_status
        sent_email.date = datetime.now()
    else:
        new_sent_email = SentEmail(internal_id=uuid.uuid4(), klubb=klubb, name=name, email=email, date=datetime.now(), status=new_status)
        db.session.add(new_sent_email)
    db.session.commit()
    app.logger.info(f"Status uppdaterad för {name} ({email}) till {new_status}")

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

@app.route('/skicka_email', methods=['POST'])
def skicka_email():
    try:
        data = json.loads(request.data)
        recipients = data.get('recipients', [])
        klubb = data.get('klubb')

        for recipient in recipients:
            name = recipient['name']
            email = recipient['email']

            if not is_valid_email(email):
                app.logger.error(f"Ogiltig e-postadress: {email}")
                continue

            personal_link = build_external_url('index', name=name, club=klubb, email=email)
            subject = f'Länk till indexsidan för {klubb}'
            
            html_content = f"""
            <html>
            <body>
                <p>Hej {name},</p>
                <p>Vi hoppas att detta meddelande når dig väl. Härmed vill vi informera dig om att din åtkomst till {klubb} policie nu är 
                tillgänglig via följande länk.<br> Vi rekommenderar att du tar del av dokumentationen för att säkerställa att du är fullt uppdaterad 
                på de senaste riktlinjerna.<br>

                Klicka nedan för att läsa och signera policyn:</p>
                <table cellspacing="0" cellpadding="0">
                    <tr>
                        <td align="center" width="200" height="40" bgcolor="#9b59b6" style="color: #ffffff; display: block;">
                            <a href="{personal_link}" 
                               style="font-size:16px; font-weight: bold; font-family: sans-serif; text-decoration: none; line-height:40px; width:100%; display:inline-block">
                                <span style="color: #ffffff;">
                                    Läs policy
                                </span>
                            </a>
                        </td>
                    </tr>
                </table>
                <p>Vänliga hälsningar,<br>Catalina Software Solutions</p>
            </body>
            </html>
            """

            if send_email(subject, html_content, email):
                # Uppdatera eller skapa SentEmail-post
                sent_email = SentEmail.query.filter_by(klubb=klubb, name=name, email=email).first()
                if sent_email:
                    sent_email.date = datetime.now()
                    sent_email.status = "Skickad"
                else:
                    new_sent_email = SentEmail(klubb=klubb, name=name, email=email, date=datetime.now(), status="Skickad")
                    db.session.add(new_sent_email)

                db.session.commit()

                # Schemalägg påminnelse
                task = send_reminder_email_task.apply_async(
                    args=[recipient, klubb],
                    countdown=15,
                    expires=300,
                    acks_late=True,
                )
                app.logger.info(f"Schemalagt påminnelseuppgift {task.id} för {recipient['name']} ({klubb})")

                # Använd en callback-funktion
                task.then(lambda result: app.logger.info(f"Påminnelseuppgift {task.id} slutförd med resultat: {result}"))

        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Fel vid sändning av e-post: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Lägg till denna funktion för att schemalägga påminnelser
@app.route('/schedule_reminders', methods=['POST'])
def schedule_reminders():
    data = request.json
    recipients = data.get('recipients', [])
    klubb = data.get('klubb')

    for recipient in recipients:
        send_reminder_email_task.apply_async(args=[recipient, klubb], countdown=24*60*60)  # Schemalägg om 24 timmar

    return jsonify({'success': True, 'message': 'Påminnelser schemalagda'})

# Lägg till denna funktion för att logga tiden
# def log_current_time():
#     while True:
#         logging.info(f"Nuvarande tid: {datetime.now(pytz.UTC)}")
#         time.sleep(60)  # Logga varje minut

# Och där du startar tråden:
# time_logging_thread = threading.Thread(target=log_current_time)
# time_logging_thread.daemon = True
# time_logging_thread.start()

# Ny funktion för att spara policy
def save_policy(klubb, policy_content):
    new_policy = Policy(klubb=klubb, policy_content=json.dumps(policy_content), created_at=datetime.now())
    db.session.add(new_policy)
    db.session.commit()
    app.logger.info(f"Policy sparad fr {klubb}")

# Ny funktion för att hämta policy
def get_policy(klubb):
    policy = Policy.query.filter_by(klubb=klubb).order_by(Policy.created_at.desc()).first()
    return json.loads(policy.policy_content) if policy else None

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

def translate_text(text, dest_language):
    if dest_language == 'sv':
        return text  # Returnera texten oförändrad om målspråket är svenska

    try:
        if text.lower() == 'sant':
            return 'True' if dest_language == 'en' else 'Sant'
        elif text.lower() == 'falskt':
            return 'False' if dest_language == 'en' else 'Falskt'

        translated = translator.translate(text, dest=dest_language)
        app.logger.info(f"Översätter '{text}' till '{translated.text}' ({dest_language})")
        return translated.text
    except Exception as e:
        app.logger.error(f"Översättningsfel: {str(e)}")
        return text

@app.context_processor
def inject_base_url():
    return dict(base_url=get_base_url())

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logging.info(f"Skapade mapp: {directory}")

def ensure_file_exists(file_path):
    directory = os.path.dirname(file_path)
    ensure_directory_exists(directory)
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.write('[]')
        logging.info(f"Skapade fil: {file_path}")

@app.template_filter('datetime')
def format_datetime(value):
    if isinstance(value, str):
        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    elif isinstance(value, datetime):
        dt = value
    else:
        return value  # Om det varken är en sträng eller ett datetime-objekt, returnera det oförändrat
    return dt + timedelta(hours=2)

def init_db():
    with app.app_context():
        try:
            db.create_all()
            logger.info("Databastabeller skapade framgångsrikt")
        except Exception as e:
            logger.error(f"Fel vid skapande av databastabeller: {str(e)}")
            raise

# Ersätt cleanup_database funktionen med denna:
def cleanup_database():
    with app.app_context():
        app.logger.debug("Börjar rensa databasen...")

        # Logga antalet poster före rensning
        sent_emails_count = SentEmail.query.count()
        signatures_count = Signature.query.count()
        app.logger.debug(f"Antal poster före rensning: SentEmail: {sent_emails_count}, Signature: {signatures_count}")

        # Rensa upp sent_emails tabellen - ta bort poster med ogiltiga datum
        deleted = SentEmail.query.filter(SentEmail.date == None).delete(synchronize_session='fetch')
        app.logger.debug(f"Raderade {deleted} ogiltiga poster frn SentEmail")

        # Ta bort SentEmail poster som finns i Signature
        subquery = db.session.query(Signature.email, Signature.namn, Signature.klubb)
        deleted = SentEmail.query.filter(
            db.tuple_(SentEmail.email, SentEmail.name, SentEmail.klubb).in_(subquery)
        ).delete(synchronize_session='fetch')
        app.logger.debug(f"Raderade {deleted} poster från SentEmail som finns i Signature")

        # Ta bort dubbletter i sent_emails-tabellen, behåll den senaste posten
        subquery = db.session.query(
            SentEmail.klubb, 
            SentEmail.email, 
            SentEmail.name, 
            func.max(SentEmail.id).label('max_id')
        ).group_by(SentEmail.klubb, SentEmail.email, SentEmail.name).subquery()
        deleted = SentEmail.query.filter(~SentEmail.id.in_(db.session.query(subquery.c.max_id))).delete(synchronize_session='fetch')
        app.logger.debug(f"Raderade {deleted} dubbletter från SentEmail")

        db.session.commit()

        # Logga antalet poster efter rensning
        sent_emails_count = SentEmail.query.count()
        signatures_count = Signature.query.count()
        app.logger.debug(f"Antal poster efter rensning: SentEmail: {sent_emails_count}, Signature: {signatures_count}")

    app.logger.debug("Databas upprensad")

# Lägg till denna funktion för att rensa tomma poster
def cleanup_empty_entries():
    with app.app_context():
        app.logger.debug("Börjar rensa tomma poster...")

        # Rensa tomma poster från SentEmail
        deleted = SentEmail.query.filter(or_(SentEmail.name == '', SentEmail.email == '')).delete(synchronize_session='fetch')
        app.logger.debug(f"Raderade {deleted} tomma poster från SentEmail")

        # Rensa tomma poster från Signature
        deleted = Signature.query.filter(or_(Signature.namn == '', Signature.email == '')).delete(synchronize_session='fetch')
        app.logger.debug(f"Raderade {deleted} tomma poster från Signature")

        db.session.commit()
        app.logger.debug("Tomma poster har rensats från databasen")

def check_database_status():
    with app.app_context():
        signatures_count = Signature.query.count()
        sent_emails_count = SentEmail.query.count()
        app.logger.debug(f"Databasstatus vid uppstart: Signatures: {signatures_count}, SentEmail: {sent_emails_count}")

def log_table_contents():
    with app.app_context():
        app.logger.debug("Database contents summary:")
        app.logger.debug(f"SentEmail count: {SentEmail.query.count()}")
        app.logger.debug(f"Signature count: {Signature.query.count()}")


@app.route('/visa_all_data')
def visa_all_data():
    signatures = Signature.query.all()
    sent_emails = SentEmail.query.all()

    all_data = (
        [{'type': 'Signature', 'klubb': s.klubb, 'name': s.namn, 'email': s.email, 'date': s.datum, 'status': 'Signerad'} for s in signatures] +
        [{'type': 'SentEmail', 'klubb': s.klubb, 'name': s.name, 'email': s.email, 'date': s.date, 'status': s.status} for s in sent_emails]
    )

    return jsonify(all_data)

@app.route('/debug_data/<klubb>')
def debug_data(klubb):
    signaturer = get_signaturer_for_klubb(klubb)
    skickade_epostadresser = get_sent_emails_for_klubb(klubb)
    all_data = signaturer + skickade_epostadresser
    return jsonify({
        'signaturer': signaturer,
        'skickade_epostadresser': skickade_epostadresser,
        'all_data': all_data
    })

def cleanup_sent_emails():
    with app.app_context():
        try:
            # Ta bort gamla "Skickad" poster som är äldre än en viss tid (t.ex. 7 dagar)
            cutoff_date = datetime.now() - timedelta(days=7)
            old_sent_emails = SentEmail.query.filter(SentEmail.status == "Skickad", SentEmail.date < cutoff_date)
            deleted_count = old_sent_emails.delete(synchronize_session='fetch')

            db.session.commit()
            app.logger.debug(f"Raderade {deleted_count} gamla SentEmail-poster")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Fel vid rensning av gamla SentEmail-poster: {str(e)}")

# Kör denna funktion periodiskt, till exempel var 10:e minut
def periodic_cleanup():
    while True:
        cleanup_sent_emails()
        time.sleep(600)  # Vänta i 10 minuter

# Starta den periodiska rensningen i en separat tråd
cleanup_thread = threading.Thread(target=periodic_cleanup)
cleanup_thread.daemon = True
cleanup_thread.start()

# Lägg till en ny policy
@app.route('/add_policy', methods=['POST'])
def add_policy():
    data = request.json
    klubb = data.get('klubb')
    policy_content = data.get('policy_content')

    if not klubb or not policy_content:
        return jsonify({'error': 'Klubb och policy_content krävs'}), 400

    try:
        new_policy = Policy(klubb=klubb, policy_content=json.dumps(policy_content), created_at=datetime.now())
        db.session.add(new_policy)
        db.session.commit()
        return jsonify({'message': 'Policy tillagd framgångsrikt'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Hämta alla policys för en klubb
@app.route('/get_policies/<klubb>', methods=['GET'])
def get_policies(klubb):
    policies = Policy.query.filter_by(klubb=klubb).order_by(Policy.created_at.desc()).all()
    return jsonify([
        {
            'id': policy.id,
            'klubb': policy.klubb,
            'policy_content': json.loads(policy.policy_content),
            'created_at': policy.created_at.isoformat()
        } for policy in policies
    ])

# Uppdatera en befintlig policy
@app.route('/redigera_policy/<klubb>', methods=['POST'])
def redigera_policy(klubb):
    app.logger.info(f"redigera_policy funktion anropad för klubb: {klubb}")
    try:
        data = request.get_json()
        app.logger.info(f"Mottagen data: {data}")
        
        if not data:
            raise ValueError("Ingen data mottagen")

        new_policy_data = {
            'title': data.get('title', []),
            'content': data.get('content', []),
            'questions': data.get('questions', [])
        }
        
        app.logger.info(f"Ny policy data: {new_policy_data}")
        
        update_policy(klubb, new_policy_data)
        app.logger.info("Policy uppdaterad framgångsrikt")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Fel vid uppdatering av policy: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 400

def update_policy(klubb, new_policy_data):
    app.logger.info(f"Uppdaterar policy för klubb: {klubb}")
    try:
        policy = Policy.query.filter_by(klubb=klubb).order_by(Policy.created_at.desc()).first()
        if policy:
            app.logger.info("Uppdaterar befintlig policy")
            policy.policy_content = json.dumps(new_policy_data)
            policy.created_at = datetime.now()
        else:
            app.logger.info("Skapar ny policy")
            new_policy = Policy(klubb=klubb, policy_content=json.dumps(new_policy_data), created_at=datetime.now())
            db.session.add(new_policy)
        db.session.commit()       
        app.logger.info("Policy sparad i databasen")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Fel vid uppdatering av policy i databasen: {str(e)}")
        app.logger.error(traceback.format_exc())
        raise

# Ta bort en policy
@app.route('/delete_policy/<int:policy_id>', methods=['DELETE'])
def delete_policy(policy_id):
    policy = Policy.query.get(policy_id)
    if not policy:
        return jsonify({'error': 'Policy hittades inte'}), 404

    try:
        db.session.delete(policy)
        db.session.commit()
        return jsonify({'message': 'Policy borttagen framgångsrikt'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.cli.command("add-policy")
@click.argument("klubb")
def lägg_till_policy_command(klubb):
    try:
        from app_init import app
        import json
        
        # Skapa filvägen baserat på klubbnamnet
        filväg = f"/home/runner/policymaker/Policies_till_SQL/{klubb}.json"
        
        if not os.path.exists(filväg):
            click.echo(f"Ingen JSON-fil hittades för klubben '{klubb}' på sökvägen: {filväg}")
            return
        
        with app.app_context():
            with open(filväg, 'r', encoding='utf-8') as fil:
                policy_content = json.load(fil)
            
            ny_policy = Policy(klubb=klubb, policy_content=json.dumps(policy_content))
            db.session.add(ny_policy)
            db.session.commit()
            click.echo(f"En ny policy har laggs till för klubben '{klubb}' från filen '{filväg}'.")
    except Exception as e:
        click.echo(f"Ett fel uppstod vid tillägg av policy för klubb '{klubb}': {str(e)}")

@app.cli.command("delete-club")
@click.argument("klubb")
def delete_club_command(klubb):
    try:
        with app.app_context():
            # Kontrollera om klubben existerar innan vi frsöker ta bort den
            club_exists = db.session.query(
                (Policy.query.filter_by(klubb=klubb).exists()) |
                (Signature.query.filter_by(klubb=klubb).exists()) |
                (SentEmail.query.filter_by(klubb=klubb).exists())
            ).scalar()

            if not club_exists:
                click.echo(f"Klubben '{klubb}' hittades inte i databasen.")
                return

            result = delete_club(klubb)
            click.echo(f"Klubb '{klubb}' har tagits bort.")
            click.echo(f"Borttagna poster: {result['policies']} policys, {result['signatures']} signaturer, {result['sent_emails']} skickade e-postmeddelanden.")
    except Exception as e:
        click.echo(f"Ett fel uppstod vid borttagning av klubb '{klubb}': {str(e)}")

def delete_club(klubb):
    try:
        # Använd LIKE för att matcha klubbnamn som börjar med det givna namnet
        deleted_policies = Policy.query.filter(Policy.klubb.like(f"{klubb}%")).delete()
        deleted_signatures = Signature.query.filter(Signature.klubb.like(f"{klubb}%")).delete()
        deleted_sent_emails = SentEmail.query.filter(SentEmail.klubb.like(f"{klubb}%")).delete()

        db.session.commit()

        return {
            'policies': deleted_policies,
            'signatures': deleted_signatures,
            'sent_emails': deleted_sent_emails
        }
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Fel vid borttagning av klubb {klubb}: {str(e)}")
        raise

@app.cli.command("list-clubs")
def list_clubs_command():
    with app.app_context():
        all_clubs = db.session.query(Policy.klubb).union(
            db.session.query(Signature.klubb),
            db.session.query(SentEmail.klubb)
        ).distinct().all()
        click.echo("Existerande klubbar i databasen:")
        for club in all_clubs:
            click.echo(club[0])


# I din Flask-app
@app.route('/celery_status')
def celery_status():
    try:
        result = check_celery_status.delay()
        result.get(timeout=5)  # Vänta på resultat i max 5 sekunder
        return jsonify({'status': 'OK', 'message': 'Celery is running'})
    except Exception as e:
        return jsonify({'status': 'Error', 'message': str(e)}), 500

@celery.task(base=AbortableTask, max_concurrency=10)
def limited_concurrency_task():
    app.logger.info("Kör en uppgift med begränsad samtidighet")
    # Här kommer din specifika uppgiftskod
    # Till exempel:
    # result = perform_some_operation()
    # return result

# Lägg till denna rad någonstans efter att du har skapat Celery-instansen
celery.autodiscover_tasks(['main'])

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def execute_with_retry(session, query, params=None):
    try:
        result = session.execute(query, params)
        session.commit()
        return result
    except OperationalError as e:
        session.rollback()
        raise e

# Använd denna funktion istället för direkt exekvering
def execute_raw_sql(query, params=None):
    with app.app_context():
        try:
            result = execute_with_retry(db.session, text(query), params)
            return result
        except Exception as e:
            app.logger.error(f"Fel vid körning av SQL-query efter återförsök: {str(e)}")
            raise

def add_columns_to_club():
    query = """
    ALTER TABLE club 
    ADD COLUMN IF NOT EXISTS klubb VARCHAR(100) NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS namn VARCHAR(100) NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS email VARCHAR(120) UNIQUE NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);  -- Ändrat till 255
    """
    try:
        execute_raw_sql(query)
        print("klubb, namn, email och password_hash kolumner har lagts till i club tabellen")
    except Exception as e:
        print(f"Ett fel uppstod: {str(e)}")

def update_password_hash_column():
    query = """
    ALTER TABLE club 
    ALTER COLUMN password_hash TYPE VARCHAR(255);
    """
    try:
        execute_raw_sql(query)
        print("password_hash kolumnen har uppdaterats till VARCHAR(255)")
    except Exception as e:
        print(f"Ett fel uppstod: {str(e)}")

def initialize_database():
    add_columns_to_club()
    update_password_hash_column()

@app.cli.command("update-club-table")
def update_club_table():
    initialize_database()

@app.context_processor
def utility_processor():
    return dict(zip=zip)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    app.logger.info("Admin-sidan anropades")
    if request.method == 'POST':
        klubb = request.form['klubb']
        policy_content = request.form['policy_content']
        try:
            policy_json = json.loads(policy_content)
            new_policy = Policy(klubb=klubb, policy_content=json.dumps(policy_json), created_at=datetime.now())
            db.session.add(new_policy)
            db.session.commit()
            flash('Policy har lagts till framgångsrikt', 'success')
        except json.JSONDecodeError:
            flash('Ogiltigt JSON-format för policy', 'error')
        except Exception as e:
            flash(f'Ett fel uppstod: {str(e)}', 'error')
        return redirect(url_for('admin'))
    
    policies = Policy.query.order_by(Policy.created_at.desc()).all()
    return render_template('admin.html', policies=policies)

# Lägg till denna nya route för att hantera Excel-filuppladdning
@app.route('/upload_excel', methods=['POST'])
def upload_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'Ingen fil uppladdad'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Ingen fil vald'}), 400

    if file and allowed_file(file.filename):
        try:
            df = pd.read_excel(file)
            headers = df.columns.tolist()
            return jsonify({'headers': headers, 'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Ogiltig filtyp'}), 400

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls'}

# Lägg till denna nya route för att extrahera data från Excel-filen
@app.route('/extract_excel_data', methods=['POST'])
def extract_excel_data():
    data = request.json
    file = request.files['file']
    name_column = data['name_column']
    email_column = data['email_column']

    try:
        df = pd.read_excel(file)
        extracted_data = df[[name_column, email_column]].to_dict('records')
        return jsonify({'data': extracted_data, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@contextmanager
def get_db_connection():
    connection = engine.connect()
    try:
        yield connection
    finally:
        connection.close()

def execute_query(query, params=None):
    with get_db_connection() as conn:
        result = conn.execute(text(query), params)
        return result

#def run_celery():
#    with app.app_context():
#        celery.worker_main(['worker', '--loglevel=info', '--concurrency', '1'])

@app.route('/remove_row', methods=['POST'])
def remove_row():
    data = request.json
    internal_id = data.get('internal_id')
    is_signature = data.get('is_signature', False)
    
    app.logger.info(f"Försöker ta bort rad med internal_id: {internal_id}, is_signature: {is_signature}")
    
    if not internal_id or internal_id == 'None':
        return jsonify({'success': False, 'error': 'Inget giltigt ID tillhandahållet'}), 400
    
    try:
        if is_signature:
            deleted = Signature.query.filter_by(internal_id=internal_id).delete()
        else:
            deleted = SentEmail.query.filter_by(internal_id=internal_id).delete()
        
        if deleted:
            db.session.commit()
            app.logger.info(f"Rad med internal_id {internal_id} borttagen från {'Signature' if is_signature else 'SentEmail'}")
            return jsonify({'success': True})
        else:
            app.logger.warning(f"Ingen post hittades med internal_id {internal_id} i {'Signature' if is_signature else 'SentEmail'}")
            return jsonify({'success': False, 'error': 'Ingen post hittades med det angivna ID:t'}), 404
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Fel vid borttagning av post: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = Club.query.filter_by(email=email).first()
        
        if user:
            token = user.generate_reset_token()
            db.session.commit()
            
            # Ta bort eventuellt avslutande slash från base_url
            base_url = get_base_url().rstrip('/')
            reset_link = f"{base_url}/reset-password/{token}"
            subject = "Återställ ditt lösenord"
            html_content = f"""
            <html>
            <body>
                <p>Hej {user.namn},</p>
                <p>Du har begärt att återställa ditt lösenord. Klicka på länken nedan för att välja ett nytt lösenord:</p>
                <p><a href="{reset_link}">Återställ lösenord</a></p>
                <p>Länken är giltig i 24 timmar.</p>
                <p>Om du inte har begärt denna återställning kan du ignorera detta mail.</p>
                <p>Vänliga hälsningar,<br>Catalina Software Solutions</p>
            </body>
            </html>
            """
            
            if send_email(subject, html_content, email):
                flash('Ett mail med instruktioner har skickats till din e-postadress.', 'success')
            else:
                flash('Det gick inte att skicka återställningsmailet. Försök igen senare.', 'error')
        else:
            flash('Ett mail med instruktioner har skickats till din e-postadress om kontot existerar.', 'success')
            
        return redirect(url_for('valj_klubb'))
        
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = Club.query.filter_by(reset_token=token).first()
    
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.now():
        flash('Ogiltig eller utgången återställningslänk.', 'error')
        return redirect(url_for('valj_klubb'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Lösenorden matchar inte.', 'error')
            return render_template('reset_password.html')
        
        user.set_password(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        flash('Ditt lösenord har återställts. Du kan nu logga in.', 'success')
        return redirect(url_for('valj_klubb'))
        
    return render_template('reset_password.html')


if __name__ == '__main__':
    #threading.Thread(target=run_celery).start()
    app.run(debug=True)