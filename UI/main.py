import pyodbc
from credentials import *
from flightdata import FlightDataClass
from flask import Flask, render_template

app = Flask(__name__)

db = pyodbc.connect('DRIVER=' + driver + ';SERVER=' +
    server + ';PORT=1433;DATABASE=' + database +
    ';UID=' + username + ';PWD=' + password)

cursor = db.cursor()
cursor.execute("SELECT ID, ICAO, Callsign, NACp FROM dbo.FlightData order by ID")
rows = cursor.fetchall()


flight_data_list = []
for row in rows:
    flight_data = FlightDataClass(*row)  # Unpack the tuple and create an instance of FlightData
    flight_data_list.append(flight_data)

@app.route("/")
def index():
    return render_template('index.html', flight_data_list = flight_data_list)

if __name__=="__main__":
    app.run(debug=True)
    db.close()