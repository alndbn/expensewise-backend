from models import db, User, Expense
from werkzeug.security import generate_password_hash

#---------------------User------------------

class DataManager:
    @staticmethod
    def create_user(username, email, password):
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return None, "User already exists"

        password_hash = generate_password_hash(password)

        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            return new_user, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)


    @staticmethod
    def delete_user(user_id):
        #user anhand der id suchen
        user = db.session.get(User, user_id)

        if not user:
            return False, "User not found" #wenn es ID nicht gibt
        
        try:
            #user zum löschen makieren, cascade kümmert sich um löschen der Ausgaben
            db.session.delete(user)
            #bestätigen und in neon datenbank speichern
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, str(e)
        

#---------------------Expense--------------------

    @staticmethod
    def create_expense(data): # Wir nehmen nur noch das Paket 'data' an
    # 1. Schritt: Validierung 
        if not data.get('title') or data.get('amount') is None:
            return None, "Title and Amount are mandatory fields!"

        category_input = data.get('category')
        if not category_input or category_input.strip() == "":
            category_input = "Other"

        # 2. Schritt: Das Objekt bauen
        new_exp = Expense(
            title=data.get('title'),
            amount=data.get('amount'),
            user_id = data.get('user_id'),
            description=data.get('description'),
            category=category_input
        )

        try:
            db.session.add(new_exp)
            db.session.commit()
            return new_exp, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)
        

    @staticmethod
    def delete_expense(expense_id):
        #die einzelnen Ausgaben suchen
        expense= db.session.get(Expense, expense_id)

        if not expense:
            return False, "Expense not found"
        
        try:
            db.session.delete(expense)
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, str(e)
        
    @staticmethod
    def update_expense(expense_id, data):
        #ausgabe suchen
        expense = db.session.get(Expense, expense_id)
        if not expense:
            return None, "Expense not found"
        
        # 2. prüfen, welche Felder im "data"-Paket stecken
        # .get() verhindert Abstürze, falls ein Feld fehlt
        if 'title' in data:
            expense.title = data['title']
        if 'amount' in data:
            expense.amount = data['amount']
        if 'category' in data:
            expense.category = data['category']
        if 'description' in data:
            expense.description = data['description']
        
        try:
            db.session.commit() #alles speichern
            return expense, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)
        


