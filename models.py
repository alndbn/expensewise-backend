from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import datetime, timedelta

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    expenses = db.relationship('Expense', backref='owner', lazy=True, cascade='all, delete-orphan')
    monthly_budget = db.Column(db.Float, nullable=True)
    saving_goals = db.relationship('SavingGoal', backref='owner', lazy=True, cascade='all, delete-orphan')
    #is_verified = db.Column(db.Boolean, default=False) #für token


    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False) #muss ausgefüllt werden
    description = db.Column(db.String(500))
    category = db.Column(db.String(50), nullable=True)
    date = db.Column(db.DateTime)
    title = db.Column(db.String(100), nullable=False) #muss ausgefüllt werden
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) #muss ausgefüllt werden
    is_recurring = db.Column(db.Boolean, default=False)
    recurring_interval = db.Column(db.String(50), nullable=True)


class SavingGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, nullable=False, default=0)
    deadline = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class RefreshToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expires_at = db.Column(db.Boolean, default=False) #sicherheit:token nur ein mal nutzbar

    @staticmethod
    def generate(user_id, days=7): #generate Funktion baut neuen Token
        token = RefreshToken(
            token=secrets.token_urlsafe(64),
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(days=days)
        )
        return token
    
    def is_valid(self): #if true Token zugriff erlauben
        return not self.is_used and self.expires_at > datetime.utcnow() 


class EmailVerificationToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)

    @staticmethod
    def generate(user_id, hours=24):
        token = EmailVerificationToken(
            token=secrets.token_urlsafe(32),
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(hours=hours)
        )
        return token
    
    def is_valid(self):
        return not self.is_used and self.expires_at > datetime.utcnow()

#class Receipts(db.Model):
    #id = db.Column(db.Integer, primary_key=True)
    #date = db.Column(db.DateTime)
    #amount = db.Column(db.Float)
    #shop = db.Column(db.String(200))
    #category = db.Column(db.String(250))
    #user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        