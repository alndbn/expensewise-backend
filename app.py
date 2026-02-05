from flask import Flask, request, jsonify, render_template #anfragen aus dem internet verstehen
from models import db, User, Expense #verbindung zum datenbank-bauplan in models.py
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__) #start engine

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #SQLAlchemy Überwachungssystem ausschalten

db.init_app(app) #Datenbank wird mit App verbunden

with app.app_context():
    db.create_all() #app schaut in models.py und baut User und Expense Tabellen



#---------------Table User--------------

@app.route('/') #ruft jemand die website mit / auf, wird die Funktion ausgeführt
def index():
    users = User.query.all()
    return render_template('index.html', users=users)


@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json() #json daten aus Postman Anfrage holen
    #guckt, ob der Nutzer schon existiert:
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({"error": "A user with this mail address already exists."})

    #neuen nutzer anlegen:
    new_user = User(username=data['username'], email=data['email']) 

    try:
        db.session.add(new_user) #in die neon cloud adden
        db.session.commit()
        return jsonify({"message": "User successful created", "id": new_user.id}), 201 
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/users', methods=['GET'])
def get_all_users():
    all_users = User.query.all() #holen alle Nutzer aus der Datenbank

    #Wir wandeln die Objekte in eine Liste aus Dictionaries um, 
    # damit wir sie als JSON verschicken können
    results = []
    for user in all_users:
        results.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
        })
    return jsonify(results), 200


@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    # 1. User suchen
    user = db.session.get(User, user_id) # Modernerer Weg als .query.get()

    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # 2. Daten holen
    data = request.get_json()

    # 3. Felder aktualisieren
    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']
    
    # 4. Speichern
    db.session.commit()
    
    return jsonify({
        "message": "User updated", 
        "username": user.username}), 200


@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    #1. den nutzer in der datenbank suchen
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404
    
    #2. den nutzer aus der session entfernen
    db.session.delete(user)
    #3. die änderungen in neon speichern
    db.session.commit()
    return jsonify({"message": f"User {user_id} succesfful deleted."}), 200


#--------------table expense----------------

@app.route('/expenses', methods=['POST'])
def create_expense():
    data = request.get_json()

    #neues objekt erstellen:
    new_expense= Expense (
        title=data['title'],
        amount=data['amount'],
        description=data.get('description'),
        category=data.get('category'),
        user_id=data['user_id']
    )

    db.session.add(new_expense)
    db.session.commit()

    return jsonify({"message": "Expense safed", "id": new_expense.id}), 201


@app.route('/expenses/user/<int:user_id>', methods=['GET'])
def get_expenses_by_user(user_id):
    user_expenses = Expense.query.filter_by(user_id=user_id).all()
    #die liste wieder in json umwandeln:
    results = []
    for exp in user_expenses:
        results.append({
            "id": exp.id,
            "title": exp.title,
            "amount": exp.amount,
            "category": exp.category,
            "date": exp.date
        })
    return jsonify(results), 200


@app.route('/expenses/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    expense = db.session.get(Expense, expense_id)
    if not expense:
        return jsonify({"error": "Couldn't find expense"}), 404
    
    data = request.get_json()
    # Wir aktualisieren nur die Felder, die im JSON geschickt wurden
    if 'title' in data: expense.title = data['title']
    if 'amount' in data: expense.amount = data['amount']
    if 'category' in data: expense.category = data['category']
    if 'description' in data: expense.description = data['description']

    db.session.commit()
    return jsonify({"message": "Expense updated"}), 200


@app.route('/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    expense = db.session.get(Expense, expense_id)
    if not expense:
        return jsonify({"error": "Couldn't find expense"})
    
    db.session.delete(expense)
    db.session.commit()
    return jsonify({"message": "Expense successful deleted"}), 200



if __name__ == "__main__": #startet das programm nur dann, wenn ich app.py aufrufe
    app.run(debug=True) #Startet die App + wenn ich etwas ändere/speicher startet f
    #lask automatisch den server neu + gibt im browser detailierte Fehlermeldung aus