from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False) #muss ausgefüllt werden
    email = db.Column(db.String(100), nullable=False, unique=True) #muss ausgefüllt werden
    expenses = db.relationship('Expense', backref='owner', lazy=True, cascade='all, delete-orphan')

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False) #muss ausgefüllt werden
    description = db.Column(db.String(500))
    category = db.Column(db.String(50), nullable=True)
    date = db.Column(db.DateTime)
    title = db.Column(db.String(100), nullable=False) #muss ausgefüllt werden
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) #muss ausgefüllt werden