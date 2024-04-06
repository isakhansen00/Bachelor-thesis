import time
import pyodbc
from credentials import *
from flightdata import FlightDataClass
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit
from threading import Lock
import sys
sys.path.insert(0, 'Map')
from map_ui import generate_map

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

thread = None
thread_lock = Lock()

db = pyodbc.connect('DRIVER=' + driver + ';SERVER=' +
    server + ';PORT=1433;DATABASE=' + database +
    ';UID=' + username + ';PWD=' + password + ";Mars_Connection=yes")

cursor = db.cursor()
cursor2 = db.cursor()
cursor3 = db.cursor()
cursor4 = db.cursor()
cursor.execute("SELECT ID, ICAO, Callsign, NACp FROM dbo.FlightData order by ID DESC")
rows = cursor.fetchall()
cursor.close()

flight_data_list = []
unique_icao_addresses = set()  # Used to keep track of flight trips
first_time_startup = True

# for row in rows:
#     flight_data = FlightDataClass(*row)  # Unpack the tuple and create an instance of FlightData
#     flight_data_list.append(flight_data)


def get_new_data_from_staging_table():
    cursor2 = db.cursor()
    cursor2.execute("SELECT ID, ICAO, Callsign, NACp FROM dbo.FlightData WHERE isprocessed = 0")
    rows = cursor2.fetchall()
    new_data = []
    for row in rows:
        flight_data = FlightDataClass(*row)
        cursor2.execute("UPDATE dbo.FlightData SET isprocessed = 1 WHERE ID = ?", (flight_data.id,))
        db.commit()

        new_data.append(flight_data)
    cursor2.close()
    return new_data

def check_nacp_threshold():
    nac_p_threshold_value = 9
    while True:
        new_data = get_new_data_from_staging_table()
        #socketio.emit('nacp_alert', {})
        #print("hei")
        #socketio.sleep(1)
        if new_data:
             for flight_data2 in new_data:
                 process_and_insert_into_main_table(flight_data2)
                 insert_trip_id_to_flight_position(flight_data2)  # Insert trip-ID to positions in FlightTripPositions table in the database.
                 if int(flight_data2.nacp) < nac_p_threshold_value:
                     socketio.emit('nacp_alert', {'callsign': flight_data2.callsign, 'nacp': flight_data2.nacp})
                     #socketio.emit('nacp_alert', {'callsign'})
                     socketio.sleep(2)

def process_and_insert_into_main_table(flight_data):
    print(unique_icao_addresses)
    cursor3 = db.cursor()  # Initialize cursor here
    if flight_data.icao not in unique_icao_addresses:
        cursor3.execute("INSERT INTO dbo.FlightTrips (ICAO, TripTimestamp) VALUES (?, ?)", (flight_data.icao, time.time()))
        db.commit()
        cursor3.close()
        unique_icao_addresses.add(flight_data.icao) 
    cursor3 = db.cursor()  # Reinitialize cursor after closing

    cursor3.execute("""
    INSERT INTO dbo.FlightDataNew (ICAO, Callsign, NACp, TripID)
    SELECT ?, ?, ?, ft.TripID
    FROM dbo.FlightTrips ft
    WHERE ft.ICAO = ?
    AND ft.TripTimestamp = (SELECT MAX(TripTimestamp) FROM dbo.FlightTrips WHERE ICAO = ?)
    UNION ALL
    SELECT ?, ?, ?, NULL
    WHERE NOT EXISTS (SELECT 1 FROM dbo.FlightTrips WHERE ICAO = ?)
    """, (flight_data.icao, flight_data.callsign, flight_data.nacp, flight_data.icao, flight_data.icao,
          flight_data.icao, flight_data.callsign, flight_data.nacp, flight_data.icao))


    # cursor3.execute("""
    #     INSERT INTO dbo.FlightDataNew (ICAO, Callsign, NACp, TripID)
    #     SELECT ?, ?, ?, ft.TripID
    #     FROM dbo.FlightTrips ft
    #     WHERE ft.ICAO = ?
    #     """, (flight_data.icao, flight_data.callsign, flight_data.nacp, flight_data.icao))
    db.commit()
    cursor3.close()

    print(flight_data.callsign)
    
    socketio.emit('new_flight_data', {
        'id': flight_data.id,
        'icao': flight_data.icao,
        'callsign': flight_data.callsign,
        'nacp': flight_data.nacp
    })

# Retrieves the latest trip ID associated with a given ICAO code from the FlightTrips table in the database.
# Returns: None
def get_latest_trip_id(icao_address):
    cursor5 = db.cursor()
    cursor5.execute("""
        SELECT TripID 
        FROM FlightTrips 
        WHERE ICAO = ? 
        AND TripTimestamp = (
            SELECT MAX(TripTimestamp) 
            FROM FlightTrips 
            WHERE ICAO = ?
        )
    """, (icao_address, icao_address))
    trip_id = cursor5.fetchone()
    cursor5.close()
    return trip_id[0] if trip_id else None

# Retrieves the latest trip ID associated with a given ICAO code from the FlightTrips table in the database.
# Returns: None
def get_latest_trip_timestamp(icao_address):
    cursor5 = db.cursor()
    cursor5.execute("""
        SELECT TripTimestamp 
        FROM FlightTrips 
        WHERE ICAO = ? 
        AND TripTimestamp = (
            SELECT MAX(TripTimestamp) 
            FROM FlightTrips 
            WHERE ICAO = ?
        )
    """, (icao_address, icao_address))
    trip_id = cursor5.fetchone()
    cursor5.close()
    return trip_id[0] if trip_id else None

# Inserts the latest trip ID associated with a flight's ICAO code into the FlightTripPositions table in the database.
# Returns:
#   - The latest trip ID associated with the given ICAO address if found, else returns None.
def insert_trip_id_to_flight_position(flight_data):
    trip_id = get_latest_trip_id(flight_data.icao)
    cursor6 = db.cursor()
    cursor6.execute("UPDATE dbo.FlightTripPositions SET TripID = ? WHERE ICAO = ?", (trip_id, flight_data.icao))
    cursor6.close()

# Retrieves the latest position timestamp for a given ICAO address from the FlightTripPositions table.
# Returns:
#    - Latest position timestamp
def get_latest_position_timestamp(icao_address):
    cursor8 = db.cursor()
    cursor8.execute("""
        SELECT MAX(PositionTimestamp)
        FROM FlightTripPositions
        WHERE ICAO = ?
    """, (icao_address,))
    latest_position_timestamp = cursor8.fetchone()
    cursor8.close()
    return latest_position_timestamp[0] if latest_position_timestamp else None

def add_icao_for_positions_under_5_minutes_old_to_set():
    # Define the threshold time (5 minutes ago)
    threshold_time = 300
    current_time = time.time()
    cursor9 = db.cursor()
    cursor9.execute("""
        SELECT DISTINCT ICAO 
        FROM FlightTripPositions 
        WHERE PositionTimestamp > ?
    """, (current_time - threshold_time,))  # Compare PositionTimestamp with current time minus threshold

    # Fetch all rows from the executed query
    rows = cursor9.fetchall()
    
    # If there are no rows, return False
    if len(rows) == 0:
        cursor9.close()
        return False
    
    # Add unique ICAO addresses to the set
    for row in rows:
        unique_icao_addresses.add(row[0])  # Assuming ICAO is the first column in the result
        
    cursor9.close()
    return True

def add_icao_for_trips_under_5_minutes_old_to_set():
    # Define the threshold time (5 minutes ago)
    threshold_time = 300
    current_time = time.time()
    cursor10 = db.cursor()
    cursor10.execute("""
        SELECT ICAO 
        FROM FlightTrips 
        WHERE TripTimestamp > ?
    """, (current_time - threshold_time,))  # Compare TripTimestamp with current time minus threshold


    # Fetch all rows from the executed query
    rows = cursor10.fetchall()
    
    # If there are no rows, return False
    if len(rows) == 0:
        cursor10.close()
        return False
    
    # Add unique ICAO addresses to the set
    for row in rows:
        unique_icao_addresses.add(row[0])  # Assuming ICAO is the first column in the result
        
    cursor10.close()
    return True

# Function to periodically check and remove stale entries from flight_data
def check_stale_entries():
    time.sleep(5)
    while True:
        # Check if the set is empty
        if not unique_icao_addresses:
            print("VENT")
            # If the set is empty, wait for 1 minute before checking again
            time.sleep(60)
            continue

        current_time = time.time()
        stale_threshold = 300  # 5 minutes in seconds
        print("KJØR")

        # Copy the set to avoid modification during iteration
        icao_addresses_copy = unique_icao_addresses.copy()

        for icao_address in icao_addresses_copy:
            # Get the latest position timestamp for the ICAO code
            latest_position_timestamp = get_latest_position_timestamp(icao_address)
            # If position older than 5 minutes, remove the ICAO code from the set
            if latest_position_timestamp is not None:
                print(current_time)
                print(f"latest position timestamp: {latest_position_timestamp} of type {type(latest_position_timestamp)}")
                print(unique_icao_addresses)
                if current_time - float(latest_position_timestamp) > stale_threshold:
                    unique_icao_addresses.remove(icao_address)
                    print("FJERNET VIA POSITION")
                    print(unique_icao_addresses)
            # If no position and trip is older than 5 minutes, remove the ICAO code from the set
            else:
                latest_trip_timestamp = get_latest_trip_timestamp(icao_address)
                print(f"latest trip timestamp: {latest_trip_timestamp} of type {type(latest_trip_timestamp)}")
                print(unique_icao_addresses)
                if latest_trip_timestamp is not None:
                    print(current_time)
                    if current_time - int(latest_trip_timestamp) > stale_threshold:
                        unique_icao_addresses.remove(icao_address)
                        print("FJERNET VIA TRIP")
                        print(unique_icao_addresses)

        # Wait for 1 minute before checking again
        time.sleep(60)

@app.route("/")
def index():
    cursor4 = db.cursor()
    cursor4.execute("SELECT ID, ICAO, Callsign, NACp FROM dbo.FlightDataNew order by ID DESC")

    rows = cursor4.fetchall()

    flight_data_list = []
    for row in rows:
        flight_data = FlightDataClass(*row)  # Unpack the tuple and create an instance of FlightData
        flight_data_list.append(flight_data)
    numberOfItems = len(flight_data_list)
    cursor4.close()

    return render_template('index.html', flight_data_list = flight_data_list, numberOfItems = numberOfItems)

# Retrieves flight position data based on provided row-ID, ICAO code and TripID,
# generates a map based on the position data, and returns the HTML representation
# of the map along with success or failure status in JSON format.
# Returns:
#   - JSON object with the HTML representation of the generated map and status message
@app.route("/get_flight_map")
def get_flight_map():
    # Retrieve row-ID and ICAO code from the request query string
    flight_id = request.args.get('id')
    icao = request.args.get('icao')

    # Create a cursor for interacting with the database
    cursor7 = db.cursor()

    # Retrieve TripID from FlightDataNew table in database based on the provided row-ID
    cursor7.execute("SELECT TripID FROM FlightDataNew WHERE ID = ?", (flight_id,))
    row = cursor7.fetchone()
    if row:
        trip_id = row[0]
        
        # Fetch positions based on ICAO and TripID
        cursor7.execute("SELECT Longitude, Latitude FROM FlightTripPositions WHERE ICAO = ? AND TripID = ?", (icao, trip_id))
        positions = cursor7.fetchall()

        cursor7.close()

        # Construct dictionary with flight positions
        if positions:
            flight_positions = {icao: [(float(pos[1]), float(pos[0])) for pos in positions]}
            # Generate map based on flight positions
            flight_map = generate_map(flight_positions)
            # Get the HTML representation of the map
            flight_map_html = flight_map.get_root()._repr_html_()
            return jsonify({'success': True, 'html': flight_map_html})
        else:
            return jsonify({'success': False, 'message': 'No available position data for this airplane.'})
    else:
        return jsonify({'success': False, 'message': 'ICAO value not found'})

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
            thread = socketio.start_background_task(check_stale_entries)

"""
Decorator for disconnect
"""
# @socketio.on('disconnect')
# def disconnect():
#     print('Client disconnected',  request.sid)

if __name__=="__main__":
    if first_time_startup:
        print("STARTER APP")
        if add_icao_for_positions_under_5_minutes_old_to_set():
            if add_icao_for_trips_under_5_minutes_old_to_set():
                print("LAGT TIL FLIGHTTRIPS VED START VIA POSITION OG TRIP")
                print(unique_icao_addresses)
            else:
                print("LAGT TIL FLIGHTTRIPS VED START VIA POSITION")
                print(unique_icao_addresses)
        elif add_icao_for_trips_under_5_minutes_old_to_set():
            print("LAGT TIL FLIGHTTRIPS VED START VIA TRIP")
            print(unique_icao_addresses)
        else:
            print("INGEN VERDIER Å LEGGE TIL FRA START")
        
        first_time_startup = False  # Set the flag to False after initialization
    socketio.run(app, debug=True)
    db.close()