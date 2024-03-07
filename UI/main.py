import pyodbc
from credentials import *
from flightdata import FlightDataClass
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import time
from threading import Lock
from requests import request

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

thread = None
thread_lock = Lock()

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
        socketio.sleep(2)

def get_new_data_from_staging_table():
    cursor.execute("SELECT ID, ICAO, Callsign, NACp FROM dbo.FlightData WHERE isprocessed = 0")
    rows = cursor.fetchall()
    new_data = []
    for row in rows:
        flight_data = FlightDataClass(*row)
        cursor.execute("UPDATE dbo.FlightData SET isprocessed = 1 WHERE ID = ?", (flight_data.id,))
        db.commit()

        new_data.append(flight_data)
    return new_data

def check_nacp_threshold():
    nac_p_threshold_value = 10
    while True:
        new_data = get_new_data_from_staging_table()
        #socketio.emit('nacp_alert', {})
        #print("hei")
        socketio.sleep(5)
        if new_data:
             for flight_data2 in new_data:
                 process_and_insert_into_main_table(flight_data2)
                 if int(flight_data2.nacp) < nac_p_threshold_value:
                     socketio.emit('nacp_alert', {'callsign': flight_data2.callsign, 'nacp': flight_data2.nacp})
                     #socketio.emit('nacp_alert', {'callsign'})
                     #socketio.sleep(1)

def process_and_insert_into_main_table(flight_data):
    cursor.execute("INSERT INTO dbo.FlightDataNew (ICAO, Callsign, NACp) VALUES (?, ?, ?)", (flight_data.icao, flight_data.callsign, flight_data.nacp))
    db.commit()
    print(flight_data.callsign)
    
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

"""
Decorator for connect
"""
@socketio.on('connect')
def connect():
    global thread
    print('Client connected')

    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(check_nacp_threshold)

"""
Decorator for disconnect
"""
# @socketio.on('disconnect')
# def disconnect():
#     print('Client disconnected',  request.sid)

if __name__=="__main__":
    socketio.run(app, debug=True)
    db.close()