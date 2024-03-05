import pyodbc
from credentials import *
from flightdata import FlightDataClass
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import time

app = Flask(__name__)
socketio = SocketIO(app)

db = pyodbc.connect('DRIVER=' + driver + ';SERVER=' +
    server + ';PORT=1433;DATABASE=' + database +
    ';UID=' + username + ';PWD=' + password)

cursor = db.cursor()
cursor.execute("SELECT ID, ICAO, Callsign, NACp FROM dbo.FlightData order by ID DESC")
rows = cursor.fetchall()

flight_data_list = []
for row in rows:
    flight_data = FlightDataClass(*row)  # Unpack the tuple and create an instance of FlightData
    flight_data_list.append(flight_data)

# Function to periodically check staging table for new data
def check_staging_table():
    while True:

        new_data = get_new_data_from_staging_table()
        if new_data:
            for flight_data in new_data:
                process_and_insert_into_main_table(flight_data)
                check_nacp_threshold(flight_data)
        time.sleep(2)

def get_new_data_from_staging_table():
    cursor.execute("SELECT ID, ICAO, Callsign, NACp FROM dbo.FlightData WHERE isprocessed = 0")
    rows = cursor.fetchall()
    new_data = []
    for row in rows:
        # Assuming FlightDataClass is defined similarly to your FlightDataClass
        flight_data = FlightDataClass(*row)
        new_data.append(flight_data)
    return new_data

def check_nacp_threshold(flight_data):
    threshold_value = 11
    if int(flight_data.nacp[1]) < threshold_value:
        socketio.emit('nacp_alert', {'callsign': flight_data.callsign, 'nacp': flight_data.nacp})

def process_and_insert_into_main_table(flight_data):
    # Code to process and insert new data into main table
    # Example:
    # cursor.execute("INSERT INTO dbo.FlightDataNew (ICAO, Callsign, NACp) VALUES (?, ?, ?)", (flight_data.icao, flight_data.callsign, flight_data.nacp))
    # db.commit()
    
    # Emit new_flight_data signal
    socketio.emit('new_flight_data', {
        'id': flight_data.id,
        'icao': flight_data.icao,
        'callsign': flight_data.callsign,
        'nacp': flight_data.nacp
    })

    # Update flight_data_list
    flight_data_list.append(flight_data)

@app.route("/")
def index():
    cursor = db.cursor()
    cursor.execute("SELECT ID, ICAO, Callsign, NACp FROM dbo.FlightData order by ID DESC")
    rows = cursor.fetchall()

    flight_data_list = []
    for row in rows:
        flight_data = FlightDataClass(*row)  # Unpack the tuple and create an instance of FlightData
        flight_data_list.append(flight_data)
    return render_template('index.html', flight_data_list = flight_data_list)

if __name__=="__main__":
    import threading
    check_thread = threading.Thread(target=check_staging_table)
    check_thread.daemon = True
    check_thread.start()

    socketio.run(app, debug=True)
    db.close()