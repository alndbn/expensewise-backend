from models import db, User, Expense, SavingGoal
from werkzeug.security import generate_password_hash
import jwt
from datetime import datetime, timedelta
import os

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
        

    @staticmethod
    def update_user(user_id, data):
        user = db.session.get(User, user_id)
        if not user:
            return None, "User not found"
        
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'monthly_budget' in data:
            user.monthly_budget = data['monthly_budget']

        try:
            db.session.commit() 
            return user, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

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
            category=category_input,
            is_recurring=data.get('is_recurring', False),
            recurring_interval=('recurring_interval'),
            date=data.get('date'),
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
        if 'is_recurring' in data:
            expense.is_recurring = data['is_recurring']
        if 'recurring_interval' in data:
            expense.recurring_interval = data['recurring_interval']


        try:
            db.session.commit() #alles speichern
            return expense, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)


    @staticmethod
    def get_user_expenses(user_id):
        user = db.session.get(User, user_id)

        if not user:
            return None, "User not found"
    
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
                "date": expense.date.strftime('%Y-%m-%d') if expense.date else None
            }
            # Dieses Wörterbuch hängen wir an unsere Liste an
            results.append(expense_data)
        
        return results, None


    @staticmethod
    def get_expense_summary(user_id):
        user = db.session.get(User, user_id)

        if not user:
            return None, "User not found"

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
                category_totals[cat] = amount #auf die Kategorie cat im Dictionary category_totals zugreifen und
                #den Betrag addieren

        return {"total amount": total_expenses, "by category": category_totals}, None


#---------------------Token--------------------
    @staticmethod 
    def create_tokens(user_id):
        access_token = jwt.encode(
            {"user_id": user_id, "exp": datetime.utcnow() + timedelta(minutes=15)},
            os.getenv('SECRET_KEY'),
            algorithm="HS256"
        )
        refresh_token = jwt.encode(
            {"user_id": user_id, "exp": datetime.utcnow() + timedelta(days=7)},
            os.getenv('SECRET_KEY'),
            algorithm="HS256"
        )
        return access_token
        

 #---------------------SavingGoal-------------        

    @staticmethod
    def create_saving_goal(data):
        if not data.get('title') or data.get('target_amount') is None:
            return None, "Title and Saving Amount are mandatory fields!"
        
        new_goal = SavingGoal(
            title=data.get('title'),
            target_amount=data.get('target_amount'),
            current_amount=data.get('current_amount', 0),
            deadline=data.get('deadline'),
            user_id=data.get('user_id')
        )
        
        try:
            db.session.add(new_goal)
            db.session.commit()
            return new_goal.id, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)


    @staticmethod
    def get_saving_goal(user_id):
        user = db.session.get(User, user_id)

        if not user:
            return None, "User not found"

        results = []

        for savings in user.saving_goals:
            savings_data = {
                "id": savings.id,
                "title": savings.title,
                "target_amount": savings.target_amount,
                "current_amount": savings.current_amount,
                "deadline": savings.deadline
            }
            results.append(savings_data)
        
        return results, None
    

    @staticmethod
    def update_saving_goal(saving_id, data):
        savings = db.session.get(SavingGoal, saving_id)
        if not savings:
            return None, "Savings not found"
        
        if 'title' in data:
            savings.title = data['title']
        if 'target_amount' in data:
            savings.target_amount = data['target_amount']
        if 'current_amount' in data:
            savings.current_amount = data['current_amount']
        if 'deadline' in data:
            savings.deadline = data['deadline']

        try:
            db.session.commit()
            return savings, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)


