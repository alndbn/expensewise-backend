from flask import Flask, request, jsonify, render_template #anfragen aus dem internet verstehen
from flask_cors import CORS
from models import db, User, Expense, RefreshToken, EmailVerificationToken, SavingGoal #verbindung zum datenbank-bauplan in models.py
import os
from dotenv import load_dotenv
from service.data_manager import DataManager
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
from datetime import timedelta

load_dotenv() 


app = Flask(__name__) #start engine

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') 
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
#print("DB URL:", os.getenv('DATABASE_URL'))
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_SECRET_KEY"] = "mein-sehr-langer-geheimer-schluessel-abc-123456"
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_DOMAIN'] = False
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)

db.init_app(app) #Datenbank wird mit App verbunden

# erlauben explizit dem React-Frontend den Zugriff
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "http://localhost:5174", "https://expensewise-frontend.vercel.app"]}}, supports_credentials=True)

jwt = JWTManager(app)

with app.app_context():
    db.create_all() #app schaut in models.py und legt alle Tabellen an



#-----------------------------TableUser-----------------------------------------------------

@app.route('/api/') #ruft jemand die website mit / auf, wird die Funktion ausgeführt
def index():
    return jsonify({"message": "ExpenseWise API is running"}), 200


@app.route('/api/users', methods=['PUT'])
@jwt_required()
def update_user():
    user_id = get_jwt_identity()
    data = request.get_json()
    user, error = DataManager.update_user(user_id, data)
    if error:
        return jsonify({"error": error}), 404
    return jsonify({"message": "User successfully updated"}), 200


@app.route('/api/users', methods=['DELETE'])
@jwt_required()
def delete_user():
    user_id = int(get_jwt_identity())
    success, error = DataManager.delete_user(user_id)

    if not success:
        return jsonify({"error": error}), 404
    
    return jsonify({"message": f"User {user_id} successfully deleted."}), 200


@app.route('/api/register', methods=['POST'])
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

    access_token = create_access_token(identity=str(user.id)) 

    return jsonify({
        "message": "User registered successfully",
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "monthly_budget": user.monthly_budget,  
        "access_token": access_token
    }), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Missing email or password"}), 400

    # User suchen
    user = User.query.filter_by(email=data.get('email')).first()

    if user and user.check_password(data.get('password')):
        login_user(user)
        
        access_token = create_access_token(identity=str(user.id))

        response = jsonify({
            "message": "login successful",
            "access_token":  access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "monthly_budget": user.monthly_budget,
                "base_currency": user.base_currency
            }
        })
        return response, 200
    return jsonify({"error": "Invalid credentials"}), 401


@app.route('/api/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    print(user_id)
    user = db.session.get(User, int(user_id))

    if not user:
        return jsonify({"error": "User not existing"}), 404

    rate = DataManager.get_exchange_rate("EUR", user.base_currency)
    if user.monthly_budget is not None:
        converted_budget = user.monthly_budget * rate
    else:
        converted_budget = None
    print("base_currency:", user.base_currency)
    print("rate:", rate)
    print("converted_budget:", converted_budget)

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "monthly_budget": converted_budget,
        "base_currency": user.base_currency
    })
    

#----------------------------tableExpense-----------------------------------------------

@app.route('/api/expenses', methods=['POST'])
@jwt_required()
def create_expense():
    user_id = int(get_jwt_identity()) #id aus token holen
    data = request.get_json()
    expense, error = DataManager.create_expense(data, user_id)

    if not expense: 
        return jsonify({"error": error}), 400
    
    return jsonify({"message": "Expense successful created"}), 201


@app.route('/api/expenses/<int:expense_id>', methods=['PUT'])
@jwt_required()
def update_expense(expense_id):
    user_id = get_jwt_identity()
    data = request.get_json() #daten aus postman holen

    expense, error = DataManager.update_expense(expense_id, int(user_id), data)

    if error == "No access":
        return jsonify({"error": error}), 403
    if error:
        return jsonify({"error": error}), 404
    
    return jsonify({"message": "Updated successfully."}), 200


@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
@jwt_required()
def delete_expense(expense_id):
    user_id = get_jwt_identity()

    success, error = DataManager.delete_expense(expense_id, int(user_id))

    if error == "No access":
        return jsonify({"error": error}), 403
    if not success:
        return jsonify({"error": error}), 404

    
    return jsonify({"message": "Expense successful deleted"}), 200


@app.route('/api/expenses/user', methods=['GET'])
@jwt_required()
def get_user_expenses():
    user_id = get_jwt_identity()
    expenses, error = DataManager.get_user_expenses(user_id)

    if error:
        return jsonify({"error": error}), 404
    
    return jsonify(expenses), 200


@app.route('/api/expenses/user/summary', methods=['GET'])
@jwt_required()
def get_expense_summary():
    user_id = get_jwt_identity()
    expense, error = DataManager.get_expense_summary(user_id)

    if error:
        return jsonify({"error": error}), 404
    
    return jsonify(expense), 200


@app.route('/api/users/<user_id>', methods=['GET'])
@jwt_required()
def budget(user_id):
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"message": "User not found"})
    
    return jsonify({"monthly_budget": user.monthly_budget}), 200


#---------------------tableSavingGoal------------- 

@app.route('/api/saving-goals', methods=['POST'])
@jwt_required()
def create_saving_goal():
    user_id = int(get_jwt_identity()) 
    data = request.get_json()
    saving_goal, error = DataManager.create_saving_goal(user_id, data)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"message": "Saving Goal created"}), 201


@app.route('/api/saving-goals/users', methods=['GET']) #abrufen
@jwt_required()
def get_saving_goal():
    user_id = get_jwt_identity()
    saving_goal, error = DataManager.get_saving_goal(user_id)
    if error:
        return jsonify({"error": error}), 400
    
    return jsonify(saving_goal), 200


@app.route('/api/saving-goals/<goal_id>', methods=['PUT']) #updaten
@jwt_required()
def update_saving_goal(goal_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    saving_goal, error = DataManager.update_saving_goal(goal_id, user_id, data)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"message": "Saving Goal successfully updated"}), 200


#------------------TableCategory---------------------

@app.route('/api/categories', methods=['POST'])
@jwt_required()
def create_category():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    data['user_id'] = user_id 
    expense, error = DataManager.create_category(user_id, data)

    if not expense: 
        return jsonify({"error": error}), 400
    
    return jsonify({"message": "Category successful created"}), 201


@app.route('/api/categories', methods=['GET']) 
@jwt_required()
def get_categories():
    user_id = get_jwt_identity()
    categories, error = DataManager.get_category(int(user_id))
    if error:
        return jsonify({"error": error}), 400
    
    return jsonify(categories), 200


@app.route('/api/categories/<category_id>', methods=['DELETE'])
@jwt_required()
def delete_category(category_id):
    user_id = get_jwt_identity()

    success, error = DataManager.delete_category(int(category_id), int(user_id))

    if error == "No access":
        return jsonify({"error": error}), 403
    if not success:
        return jsonify({"error": error}), 404

    
    return jsonify({"message": "Category successful deleted"}), 200



if __name__ == "__main__": #startet das programm nur dann, wenn ich app.py aufrufe
    with app.app_context():
    # Das hier erstellt die Tabellen automatisch, falls sie fehlen
        db.create_all()
        print("Tabellen in Neon wurden erfolgreich angelegt!")
    app.run(debug=True) #Startet die App + wenn ich etwas ändere/speicher startet f
        #lask automatisch den server neu + gibt im browser detailierte Fehlermeldung aus








#---------------------tableReceipts------------- 
#erstellen
#@app.route('/api/receipts', methods=['POST'])
#@jwt_required()
#def create_receipt():
    #user_id = get_jwt_identity()
    #data = request.get_json()
    #data['user_id'] = user_id

    #receipt, error = DataManager.create_receipt(data)
    #if error: 
        #return jsonify({"error": error}), 400
    #return jsonify({"message": "Receipt created"}), 201

#abrufen 
#@app.route('/api/receipts', methods=['GET'])

#löschen 
#@app.route('/api/receipts/<receipt_id>', methods=['DELETE'])









#---------------------tableRefreshTokentableEmailVerificationToken------------- 

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


   