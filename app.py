from flask import Flask, request, jsonify, render_template #anfragen aus dem internet verstehen
from flask_cors import CORS
from models import db, User, Expense #verbindung zum datenbank-bauplan in models.py
import os
from dotenv import load_dotenv
from service.data_manager import DataManager


load_dotenv()


app = Flask(__name__) #start engine
CORS(app) #postman zugriff auf forbidden Fehler geben

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #SQLAlchemy Überwachungssystem ausschalten


db.init_app(app) #Datenbank wird mit App verbunden


with app.app_context():
    db.create_all() #app schaut in models.py und baut User und Expense Tabellen



#-----------------------------Table User----------------------------------------------------------------

@app.route('/') #ruft jemand die website mit / auf, wird die Funktion ausgeführt
def index():
    users = User.query.all()
    return render_template('index.html', users=users)


@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json() #json daten aus Postman Anfrage holen
    
    #übergeben Arbeit an data_manager
    user, error = DataManager.create_user(data['username'], data['email'])

    if error:
        return jsonify({"error": error}), 400 #falls es user nicht gibt
    
    #wenn alles klappt, wird ID des neues Users zurückgegeben
    return jsonify({"message": "User created", "id": user.id}), 201


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
    #app.py fragt Manager: "Lösch mal bitte User X"
    success, error = DataManager.delete_user(user_id)

    if not success:
        return jsonify({"error": error}), 404
    
    return jsonify({"message": f"User {user_id} successfully deleted."}), 200


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data.get("username") or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Username, email and password are required"}), 400

    user, error = DataManager.create_user(
        data["username"],
        data["email"],
        data["password"]
    )

    if error:
        return jsonify({"error": error}), 400

    return jsonify({
        "message": "User registered successfully",
        "id": user.id,
        "username": user.username,
        "email": user.email
    }), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Missing email or password"}), 400

    # User suchen
    user = User.query.filter_by(email=data.get('email')).first()

    # Passwort prüfen
    if user and user.check_password(data.get('password')):
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username
            }
        }), 200
    
    # Fehler, falls User nicht existiert oder Passwort falsch
    return jsonify({"error": "Invalid credentials"}), 401





#----------------------------table expense---------------------------------------------------------------

@app.route('/expenses', methods=['POST'])
def create_expense():
    data = request.get_json()

    #guckt, ob alle daten da sind
    if not data.get('amount') or not data.get('user_id') or not data.get('title'):
        return jsonify({"error": "Missing amount, title or user ID"}), 400
    
    #prüfen, ob der user existiert
    user = db.session.get(User, data.get('user_id'))
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    #neue Ausgabe erstellen un dem user zuweisen
    new_expense = Expense(
        amount=data.get('amount'),
        title=data.get('title'),
        category=data.get('category', 'other'), #other=Standardwert, falls Feld leer
        description=data.get('description'),
        user_id=user.id #verknüpfung
    )
    try: 
        db.session.add(new_expense)
        db.session.commit()
        return jsonify({
            "message": "Expense saved successfully",
            "id": new_expense.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


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
    data = request.get_json() #daten aus postman holen

    expense, error = DataManager.update_expense(expense_id, data)

    if error:
        return jsonify({"error": error}), 404
    
    return jsonify({"message": "Updated successfully."}), 200


@app.route('/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    expense = db.session.get(Expense, expense_id)
    if not expense:
        return jsonify({"error": "Couldn't find expense"})
    
    db.session.delete(expense)
    db.session.commit()
    return jsonify({"message": "Expense successful deleted"}), 200


@app.route('/expenses/user/<int:user_id>', methods=['GET'])
def get_user_expenses(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Ausgaben des Users holen
    expenses = user.expenses

    # leere Liste für die Ergebnisse
    results = []

    for expense in user.expenses:
        #Wörterbuch für jede einzelne Ausgabe
        expense_data = {
            "id": expense.id,
            "amount": expense.amount,
            "title": expense.title,
            "category": expense.category,
            "date": expense.date.strftime('%Y-%m-%d') # Datum schön formatieren
        }
        # Dieses Wörterbuch hängen wir an unsere Liste an
        results.append(expense_data)
    
    return jsonify(results), 200


@app.route('/expenses/user/<int:user_id>/summary', methods=['GET'])
def get_expense_summary(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    category_totals = {}
    total_expenses = 0

    for expense in user.expenses:
        cat = expense.category
        amount = expense.amount
        
        total_expenses += amount

        if cat in category_totals:
            # Kategorie existiert schon -> addieren
            category_totals[cat] += amount
        else:
            # Kategorie ist neu -> anlegen
            category_totals[cat] = amount

    return jsonify({
        "total_amount": total_expenses,
        "by_category":category_totals
    }), 200


if __name__ == "__main__": #startet das programm nur dann, wenn ich app.py aufrufe
    with app.app_context():
    # Das hier erstellt die Tabellen automatisch, falls sie fehlen
        db.create_all()
        print("Tabellen in Neon wurden erfolgreich angelegt!")
    app.run(debug=True) #Startet die App + wenn ich etwas ändere/speicher startet f
        #lask automatisch den server neu + gibt im browser detailierte Fehlermeldung aus