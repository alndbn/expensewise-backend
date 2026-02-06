from models import db, User, Expense

#---------------------User------------------

class DataManager:
    @staticmethod # @staticmethod bedeutet: Ich kann die Funktion direkt über DataManager.create_user() aufrufen
    def create_user(username, email):
        # 1. Prüfen, ob die Email schon da ist (Datenbank-Abfrage)
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return None, "User exists"

        #2. neues Objekt erstellen
        new_user = User(username=username, email=email)

        try:
            db.session.add(new_user) #vorbereiten
            db.session.commit() #speichern
            return new_user, None #erstellt
        except Exception as e:
            db.session.rollback() #bei fehler alles rückgängig machen
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
    def create_expense(title, amount, user_id, description=None, category=None):
        #neues Ausgabenobjekt bauen
        new_exp = Expense(
            title=title,
            amount=amount,
            user_id=user_id,
            description=description,
            category=category
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
            expense.description = data['discription']
        
        try:
            db.session.commit() #alles speichern
            return expense, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)
        


