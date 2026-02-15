const apiUrl = 'http://127.0.0.1:5000/expenses/user/1/summary'; //die URL unter der mein flask server die
//daten bereit stellt

fetch(apiUrl) //fetch startet eine anfrage an den server ähnlich wie postman
    .then(response => { //then() wartet bis die antwort vom server eingetroffen ist
        if (!response.ok) { //gucken ob server mit ok status 200 antwortet
            throw new Error('Network response was not ok');
        }
        return response.json() //wandeln rohen Text der Antwort in js-objekt um
    })
    // In diesem .then() arbeiten wir mit dem fertigen Daten-Objekt (data)
    .then(data => {
        //suche das canvas Element aus der index.html anhand seiner id
        const ctx = document.getElementById('myBarChart').getContext('2d');
        //Object.keys extrahieren alle Kategorienamen(keys) in eine Liste []
        const categories = Object.keys(data.by_category);
        //Object.values extrahieren alle Beträge(values) in eine Liste[]
        const amounts = Object.values(data.by_category);

        //neue Instanz der chart Klasse erstellen
        new Chart(ctx, {
            type: 'bar', //steht für balkendiagramm
            data: {
                labels: categories, //die beschriftung der x achse
                datasets: [{
                    label: 'Expenses in €',
                    data: amounts, //höhe der balken auf der y achse
                    backgroundColor: 'rgba(77, 32, 80, 0.6)', //füllfarbe
                    borderColor:'rgba(77, 32, 80, 0.6)', //randfarbe
                    borderWidth: 1, //dicke des randes in pixel
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true //skale zwingen bei 0 zu starten
                    }
                }
            }
        });
    })
    //.catch() fängt fehler ab alls der server zB offline ist
    .catch(error => console.error('Error', error));