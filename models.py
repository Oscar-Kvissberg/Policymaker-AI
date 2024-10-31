from app_init import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class SentEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    internal_id = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    klubb = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False)

class Policy(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    internal_id = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    klubb = db.Column(db.String(100), nullable=False)
    policy_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Signature(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    internal_id = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    namn = db.Column(db.String(100), nullable=False)
    klubb = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    datum = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Club(db.Model):
    __tablename__ = 'club'
    id = db.Column(db.Integer, primary_key=True)
    klubb = db.Column(db.String(100), nullable=False)
    namn = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(300))  # Ändra till 255 eller större



# Lägg till andra modeller här (Policy, Signature, etc.)