import os
from dotenv import load_dotenv
from google.cloud import secretmanager
from google.oauth2 import service_account
import google.auth

load_dotenv()  # Ladda miljövariabler från .env filen

# Funktion för att säkert hämta miljövariabler
def get_env_variable(name):
    try:
        return os.environ[name]
    except KeyError:
        print(f"Miljövariabeln {name} är inte satt.")
        return None

# Hämta DB_PASSWORD och PRIVATE_KEY
db_password = get_env_variable('DB_PASSWORD')
private_key = get_env_variable('PRIVATE_KEY')

if not db_password:
    print("DB_PASSWORD är inte satt.")

if not private_key:
    print("PRIVATE_KEY är inte satt.")
else:
    # Formatera private_key korrekt om det behövs
    if "-----BEGIN PRIVATE KEY-----" not in private_key:
        private_key = f"-----BEGIN PRIVATE KEY-----\n{private_key}\n-----END PRIVATE KEY-----\n"
    private_key = private_key.replace("\\n", "\n")

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

class Config:
    # Google Cloud SQL-anslutningsinformation
    DB_USER = 'postgres'
    DB_PASSWORD = db_password
    DB_NAME = 'policymaker'
    CLOUD_SQL_CONNECTION_NAME = 'southern-idea-438120-s0:us-central1:psql-f799'
    
    # Skapa credentials
    try:
        credentials = service_account.Credentials.from_service_account_info(service_account_info)
    except Exception as e:
        print(f"Fel vid skapande av credentials: {str(e)}")
        credentials = None
    
    # SQLAlchemy-konfiguration
    SQLALCHEMY_DATABASE_URI = "postgresql+pg8000://"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "creator": lambda: credentials.with_scopes(["https://www.googleapis.com/auth/cloud-platform"]).authorize(google.auth.transport.requests.Request())
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    DEBUG = True
    DEVELOPMENT = True

    CELERY_BROKER_URL = os.environ.get('RABBITMQ_URL', 'amqps://jcmvijwi:eabQ8Q3VWD0oiz0W1AipFQynIB-TA64g@hawk.rmq.cloudamqp.com/jcmvijwi')
