from flask import Flask #anfragen aus dem internet verstehen
from models import db #verbindung zum datenbank-bauplan in models.py

app = Flask(__name__) #start engine

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expensewise.db' #datenbank ist sqllite datei 
#und soll expensewise.db heißen
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #SQLAlchemy Überwachungssystem ausschalten

db.init_app(app) #Datenbank wird mit App verbunden

with app.app_context():
    db.create_all() #app schaut in models.py und baut User und Expense Tabellen


@app.route('/') #ruft jemand die website mit / auf, wird die Funktion ausgeführt
def home():
    return "Backend ist online :)"





if __name__ == "__main__": #startet das programm nur dann, wenn ich app.py aufrufe
    app.run(debug=True) #Startet die App + wenn ich etwas ändere/speicher startet f
    #lask automatisch den server neu + gibt im browser detailierte Fehlermeldung aus