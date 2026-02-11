from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    expenses = db.relationship('Expense', backref='owner', lazy=True, cascade='all, delete-orphan')

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