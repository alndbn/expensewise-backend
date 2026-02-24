from flask import Flask, request, jsonify, render_template #anfragen aus dem internet verstehen
from flask_cors import CORS
from models import db, User, Expense, RefreshToken, EmailVerificationToken #verbindung zum datenbank-bauplan in models.py
import os
from dotenv import load_dotenv
from service.data_manager import DataManager
#from flask_jwt_extended import create_access_token, JWTManager


load_dotenv() #lädt Variablen aus einer Textdatei mit dem Namen .env, brauche die Verbimdung
#zur datenbank, möchte das Passwort aber nicht in Quelltext schreiben


app = Flask(__name__) #start engine

# erlauben explizit dem React-Frontend den Zugriff
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #SQLAlchemy Überwachungssystem ausschalten
app.config["JWT_SECRET_KEY"] = "super-secret" 

#jwt = JWTManager(app)
db.init_app(app) #Datenbank wird mit App verbunden


with app.app_context():
    db.create_all() #app schaut in models.py und baut User und Expense Tabellen



#-----------------------------Table User----------------------------------------------------------------

@app.route('/') #ruft jemand die website mit / auf, wird die Funktion ausgeführt
def index():
    return jsonify({"message": "ExpenseWise API is running"}), 200


@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    user, error = DataManager.update_user(user_id, data)
    if error:
        return jsonify({"error": error}), 404
    return jsonify({"message": "User successfully updated"}), 200


@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    #app.py fragt Manager: "Lösch mal bitte User X"
    success, error = DataManager.delete_user(user_id)

    if not success:
        return jsonify({"error": error}), 404
    
    return jsonify({"message": f"User {user_id} successfully deleted."}), 200


@app.route('/register', methods=['POST'])
def register():
    #holen uns die JSON-Daten aus dem "Paket", das React geschickt hat
    data = request.get_json()
    #check: prüfen, ob alle drei Felder (Username, Email, Passwort) 
    # im Paket enthalten sind. Wenn eines fehlt, brechen wir sofort ab.
    if not data.get("username") or not data.get("email") or not data.get("password"):
        #400: client hat was falsch gemacht
        return jsonify({"error": "Username, email and password are required"}), 400
    
    #schicken die Daten an 'DataManager'. 
    #kümmert sich darum, den User in der Neon-Datenbank anzulegen
    user, error = DataManager.create_user(
        data["username"],
        data["email"],
        data["password"]
    )
    #falls der DataManager einen Fehler meldet (z.B. Email existiert schon),
    #schicken wir diesen Fehler direkt zurück an das Frontend.
    if error:
        return jsonify({"error": error}), 400

    #wenn erfolg: schicken eine Bestätigung zurück
    # 201 Created' - etwas Neues wurde erfolgreich erschaffen
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

    if user and user.check_password(data.get('password')):
        access_token, refresh_token, error = DataManager.create_tokens(user.id)

        if error:
            return jsonify({"error": error}), 500
        
        response = jsonify({
            "message": "login successful",
            "user": {
                "id": user.id,
                "username": user.username
            }
        })
        response.set_cookie('access_token', access_token, httponly=True)
        response.set_cookie('refresh_token', refresh_token, httponly=True)
        return response, 200


#----------------------------table expense---------------------------------------------------------------

@app.route('/expenses', methods=['POST'])
def create_expense():
    data = request.get_json()
    expense, error = DataManager.create_expense(data)

    if not expense: 
        return jsonify({"error": error}), 400
    
    return jsonify({"message": "Expense successful created"}), 201


@app.route('/expenses/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    data = request.get_json() #daten aus postman holen

    expense, error = DataManager.update_expense(expense_id, data)

    if error:
        return jsonify({"error": error}), 404
    
    return jsonify({"message": "Updated successfully."}), 200


@app.route('/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    success, error = DataManager.delete_expense(expense_id)

    if not success:
        return jsonify({"error": error}), 404
    
    return jsonify({"message": "Expense successful deleted"}), 200


@app.route('/expenses/user/<int:user_id>', methods=['GET'])
def get_user_expenses(user_id):
    expenses, error = DataManager.get_user_expenses(user_id)

    if error:
        return jsonify({"error": error}), 404
    
    return jsonify(expenses), 200


@app.route('/expenses/user/<int:user_id>/summary', methods=['GET'])
def get_expense_summary(user_id):
    expense, error = DataManager.get_expense_summary(user_id)

    if error:
        return jsonify({"error": error}), 404
    return jsonify(expense), 200


if __name__ == "__main__": #startet das programm nur dann, wenn ich app.py aufrufe
    with app.app_context():
    # Das hier erstellt die Tabellen automatisch, falls sie fehlen
        db.create_all()
        print("Tabellen in Neon wurden erfolgreich angelegt!")
    app.run(debug=True) #Startet die App + wenn ich etwas ändere/speicher startet f
        #lask automatisch den server neu + gibt im browser detailierte Fehlermeldung aus



#----------------------------table RefreshToken/table EmailVerificationToken---------------------------------------------------------------

# @app.route('/verify/<token>', methods=['GET'])
# def verify_email(token):
#     db_token = EmailVerificationToken.query.filter_by(token=token).first()

#     if not db_token or not db_token.is_valid():
#         return jsonify({"error": "Token invalid or expired"}), 400


#     user = db.session.get(User, db_token.user_id)

#     if not user:
#         return jsonify({"error": "User not found"}), 404
    
#     user.is_verified = True
#     db_token.is_used = True
#     db.session.commit()

#     access_token, refresh_token, error = DataManager.create_tokens(user.id)   

#     if error:
#         return jsonify({"error": error}), 500
    
#     response = jsonify({"message": "Email verified, logged in!"})
#     response.set_cookie('access_token', access_token, httponly=True)
#     response.set_cookie('refresh_token', refresh_token, httponly=True)
#     return response, 200