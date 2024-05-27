import time
import pyodbc
from credentials import *
from flightdata import FlightDataClass
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit
from threading import Lock
import sys
import pyModeS as mps
import datetime
sys.path.insert(0, 'Map')
from map_ui import generate_map
from get_sensor_status import get_sensor_status
import asyncio
import numpy as np
import pymssql

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

thread = None
thread_lock = Lock()

db = pyodbc.connect('DRIVER=' + driver + ';SERVER=' +
    server + ';PORT=1433;DATABASE=' + database +
    ';UID=' + username + ';PWD=' + password + ";Mars_Connection=yes")

conn = pymssql.connect(server, username, password, database)
Py_cursor = conn.cursor()
cursor = db.cursor()
cursor2 = db.cursor()
cursor3 = db.cursor()
cursor4 = db.cursor()


unique_icao_addresses = set()  # Used to keep track of flight trips
first_time_startup = True 

# Dictionary to hold device information
devices = {
    "RaspberryPiMorkved": {
        "device_id": "RaspberryPiMorkved"
    },
    "RaspberryPiFauskeISE": {
        "device_id": "RaspberryPiFauskeISE"
    },
    "RaspberryPiBodo": {
        "device_id": "RaspberryPiBodo"
    }
}


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
    nac_p_threshold_value = 8
    while True:
        new_data = get_new_data_from_staging_table()
        if new_data:
             for flight_data2 in new_data:
                 process_and_insert_into_main_table(flight_data2)
                 insert_trip_id_to_flight_position(flight_data2.icao)  # Insert trip-ID to positions in FlightTripPositions table in the database.
                 if int(flight_data2.nacp) < nac_p_threshold_value:
                     socketio.emit('nacp_alert', {'callsign': flight_data2.callsign, 'nacp': flight_data2.nacp})
                     socketio.sleep(2)
        # Check if there are any positions with unassigned TripID, and retrieve them and insert trip IDs for each.
        else:
            unassigned_icao_addresses = get_icao_positions_with_unassigned_trip_id()
            if unassigned_icao_addresses:
                for icao_address in unassigned_icao_addresses:
                    insert_trip_id_to_flight_position(icao_address[0])

def process_and_insert_into_main_table(flight_data):
    cursor3 = db.cursor()  # Initialize cursor here
    if flight_data.icao not in unique_icao_addresses:
        # Insert a new entry into the 'FlightTrips' table with the ICAO address and current timestamp
        cursor3.execute("INSERT INTO dbo.FlightTrips (ICAO, TripTimestamp) VALUES (?, ?)", (flight_data.icao, time.time()))
        db.commit()
        cursor3.close()
        unique_icao_addresses.add(flight_data.icao)  # Add the ICAO address to the set of unique ICAO addresses
    cursor3 = db.cursor()  # Reinitialize cursor after closing

    # Insert flight data into the 'FlightDataNew' table
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
    db.commit()
    cursor3.close()
    
    socketio.emit('new_flight_data', {
        'id': flight_data.id,
        'icao': flight_data.icao,
        'callsign': flight_data.callsign,
        'nacp': flight_data.nacp,
        'date': str(datetime.date.today())
    })

# Retrieves the latest trip ID associated with a given ICAO address from the FlightTrips table in the database.
# Returns:
#   - The latest trip ID associated with the given ICAO address if found, else returns None.
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
# Returns: None
def insert_trip_id_to_flight_position(icao_address = None):
    trip_id = get_latest_trip_id(icao_address)
    cursor6 = db.cursor()
    cursor6.execute("UPDATE dbo.FlightTripPositions SET TripID = ? WHERE ICAO = ?", (trip_id, icao_address))
    db.commit()
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

# This function adds unique ICAO addresses of flight trip positions that are less than 5 minutes old to a set.
# It queries the 'FlightTripPositions' table for distinct ICAO addresses with position timestamps within the last 5 minutes.
# Returns
#   - If no recent flight position are found, it returns False, otherwise, it returns True.
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

# This function adds ICAO addresses of flight trips that are less than 5 minutes old to a set.
# It queries the database for flight trips with timestamps within the last 5 minutes,
# retrieves the ICAO addresses from the results, and adds them to a set to ensure uniqueness.
# Returns
#   - If no recent flight trips are found, it returns False, otherwise, it returns True.
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

# This function retrieves the unique ICAO addresses from the FlightTripPositions table
# where the TripID is not assigned.
# Returns
#   - A list of tuples containing the unassigned ICAO addresses.
def get_icao_positions_with_unassigned_trip_id():
    cursor11 = db.cursor()
    cursor11.execute("""
        SELECT DISTINCT ICAO 
        FROM FlightTripPositions 
        WHERE TripID IS NULL
    """)
    unassigned_icao_addresses = cursor11.fetchall()
    #print(unassigned_icao_addresses)
    cursor11.close()

    return unassigned_icao_addresses


# This function serves as the starter application logic.
# It initializes the unique_icao_addresses set after a restart of the application, 
# by adding ICAO addresses for flight trips and positions that are under 5 minutes old,
# and prints relevant messages based on the outcome.
def initialize_flight_trips_overview():
    if add_icao_for_positions_under_5_minutes_old_to_set():
        if add_icao_for_trips_under_5_minutes_old_to_set():
            pass
    elif add_icao_for_trips_under_5_minutes_old_to_set():
        pass

# Function to periodically check and remove stale entries from flight_data
# This function iterates through the set of unique ICAO addresses, 
# checks their latest position and trip timestamps, and removes entries 
# older than 5 minutes. It waits for 1 minute if the set is empty before checking again.
def check_stale_entries():
    time.sleep(5)
    while True:
        # Check if the set of unique ICAO addresses is empty
        if not unique_icao_addresses:
            # If the set is empty, wait for 1 minute before checking again
            time.sleep(60)
            continue

        current_time = time.time()
        stale_threshold = 300  # 5 minutes in seconds

        # Copy the set to avoid modification during iteration
        icao_addresses_copy = unique_icao_addresses.copy()

        for icao_address in icao_addresses_copy:
            # Get the latest position timestamp for the ICAO address
            latest_position_timestamp = get_latest_position_timestamp(icao_address)
            # If position older than 5 minutes, remove the ICAO address from the set
            if latest_position_timestamp is not None:
                if current_time - float(latest_position_timestamp) > stale_threshold:
                    unique_icao_addresses.remove(icao_address)
            # If position data is not available, check for trip timestamp
            else:
                latest_trip_timestamp = get_latest_trip_timestamp(icao_address)
                # If trip data is available and older than 5 minutes, remove the ICAO address from the set
                if latest_trip_timestamp is not None:
                    if current_time - int(latest_trip_timestamp) > stale_threshold:
                        unique_icao_addresses.remove(icao_address)      

        # Wait for 1 minute before checking again
        time.sleep(60)

def calculate_TDoA(signal_arrival_times):
    time_diffs = {}
    processed_pairs = set()
    
    for sensor1, time1 in signal_arrival_times.items():
        for sensor2, time2 in signal_arrival_times.items():
            if sensor1 != sensor2 and (sensor1, sensor2) not in processed_pairs and (sensor2, sensor1) not in processed_pairs:
                time_diff_seconds = abs((time1 - time2))
                time_diffs[(sensor1, sensor2)] = time_diff_seconds
                processed_pairs.add((sensor1, sensor2))
    
    top_three_diffs = dict(sorted(time_diffs.items(), key=lambda item: item[1], reverse=True)[:3])
    
    return top_three_diffs




"""
This function will be used for continously checking for spoofing and updating table in real time

"""
def check_for_spoofing_continously():
    icao_delta_tdoa = {}
    cursor = conn.cursor()
    hex_value_groups = {}
    update_statement = """
        UPDATE TimestampedHexvalues 
        SET isprocessed = 1 
        WHERE HexValue = %s AND DeviceID = %s AND HexTimestamp = %s
    """

    while True:
        new_timestamped_hex_values = get_new_timestamped_hex_values()
        cursor = conn.cursor()
        if new_timestamped_hex_values:
            batch_updates = []
            for row in new_timestamped_hex_values:
                hex_value, device_id, arrival_time = row
                batch_updates.append((hex_value, device_id, arrival_time))
                if hex_value not in hex_value_groups:
                    hex_value_groups[hex_value] = {'arrival_times': {}}
                hex_value_groups[hex_value]['arrival_times'][device_id] = arrival_time
            try:
                with conn.cursor() as cursor:
                    cursor.executemany(update_statement, batch_updates)
                    conn.commit()
            except Exception as e:
                conn.rollback()
                print("Error:", e)

            icao_and_hex_values = {}
            for hex_value, group_data in hex_value_groups.items():
                icao_address = mps.adsb.icao(hex_value)
                if icao_address:
                    icao_and_hex_values.setdefault(icao_address, []).append(group_data)

            hex_values_data = []
            for icao_address, hex_values in icao_and_hex_values.items():
                for hex_value_data in hex_values:
                    group_data = hex_value_data['arrival_times']
                    time_diffs = []
                    if len(group_data) >= 2:
                        for _, time_diff in calculate_TDoA(group_data).items():
                            time_diffs.append(time_diff)
                        if time_diffs:
                            average_tdoa = round(sum(time_diffs) / len(time_diffs))
                            hex_values_data.append({'icao_address': icao_address, 'average_tdoa': average_tdoa})
                        if icao_address in icao_delta_tdoa:
                            icao_delta_tdoa[icao_address].append(average_tdoa)
                        else:
                            icao_delta_tdoa[icao_address] = [average_tdoa]

            for icao_address, average_tdoa_values in icao_delta_tdoa.items():
                if icao_address not in unique_icao_addresses:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO dbo.FlightTrips (ICAO, TripTimestamp) VALUES (%s, %s)", (icao_address, time.time()))
                    unique_icao_addresses.add(icao_address) 
                    conn.commit()
                
                for average_tdoa in average_tdoa_values:
                    print(len(average_tdoa_values))
                    if len(average_tdoa_values) >= 2:
                        cursor.execute("""
                        INSERT INTO dbo.TDOAValues (icao_address, average_tdoa, timestamp, TripID)
                        SELECT %s, %s, %s, ft.TripID
                        FROM dbo.FlightTrips ft
                        WHERE ft.ICAO = %s
                        AND ft.TripTimestamp = (SELECT MAX(TripTimestamp) FROM dbo.FlightTrips WHERE ICAO = %s)
                        UNION ALL
                        SELECT %s, %s, %s, NULL
                        WHERE NOT EXISTS (SELECT 1 FROM dbo.FlightTrips WHERE ICAO = %s)
                        """, (icao_address, average_tdoa, datetime.datetime.now(), icao_address, icao_address,
                        icao_address, average_tdoa, datetime.datetime.now(), icao_address))
                        conn.commit()
                        socketio.emit('new_tdoa_data', {
                        'icao_address': icao_address,
                        'average_tdoa': average_tdoa
                    })
                    
            for icao_address, average_tdoa_values in icao_delta_tdoa.items():
                if len(average_tdoa_values) >= 2:
                    if check_for_spoofing(tdoa_values=average_tdoa_values):
                        timestamp = datetime.datetime.now()
                        cursor.execute("INSERT INTO dbo.TDOAAlerts (icao_address, timestamp) VALUES (%s, %s)", (icao_address, timestamp))
                        socketio.emit('spoofing_alert', {'icao_address': icao_address})
                        
                        socketio.emit('new_tdoa_alarm', {
                        'icao_address': icao_address,
                        'timstamp': timestamp
                    })

        else:
            try:
                unassigned_icao_addresses = get_icao_positions_with_unassigned_trip_id()
                if unassigned_icao_addresses:
                    for icao_address in unassigned_icao_addresses:
                        insert_trip_id_to_flight_position(icao_address[0])
            except:
                continue

        socketio.sleep(15)


def get_new_timestamped_hex_values():
    cursor = conn.cursor()
    cursor.execute("""
    SELECT th.HexValue, th.DeviceID, th.HexTimestamp
    FROM TimestampedHexvalues th
    JOIN (
        SELECT HexValue
        FROM TimestampedHexvalues
        GROUP BY HexValue
        HAVING COUNT(DISTINCT DeviceID) = 2
    ) subquery ON th.HexValue = subquery.HexValue WHERE th.isprocessed = 0;
    """)
    rows = cursor.fetchall()
    cursor.close()
    return rows

@app.route("/TDOA")
def tdoa_table():
    cursor = conn.cursor()    
    hex_values_data = retrieve_delta_tdoa()
    formatted_hex_values_data = [{'ID': icao_and_tdoa[0], 'icao_address': icao_and_tdoa[1], 'average_tdoa': icao_and_tdoa[2]} for icao_and_tdoa in hex_values_data]
    cursor.close()
    return render_template('tdoa_table.html', hex_values_data=formatted_hex_values_data)

def check_for_spoofing(tdoa_values):
    tdoa_array = np.array(tdoa_values)
    mean_value = np.mean(tdoa_array)
    std_dev = np.std(tdoa_array)
    coefficient_of_variation = std_dev / mean_value
    
    if coefficient_of_variation < 50:
        return True
    else:
        return False

def retrieve_delta_tdoa():
    cursor = db.cursor()
    cursor.execute("SELECT id, icao_address, average_tdoa FROM TDOAValues order by id desc")
    rows = cursor.fetchall()
    icao_and_delta_tdoa_values = [(row[0], row[1], row[2]) for row in rows]
    return icao_and_delta_tdoa_values

def get_tdoa_alerts():
    cursor = conn.cursor()
    cursor.execute("SELECT id, icao_address, timestamp FROM TDOAAlerts order by id desc")
    rows = cursor.fetchall()
    tdoa_alerts = [(row[0], row[1], row[2]) for row in rows]

    return tdoa_alerts

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/TDOA-Alerts")
def tdoa_alerts():
    tdoa_alerts = get_tdoa_alerts()
    tdoa_alerts = [{'id': alert[0], 'icao_address': alert[1], 'timestamp': alert[2]} for alert in tdoa_alerts]
    return render_template('tdoa_alerts.html', tdoa_alerts = tdoa_alerts)

@app.route("/ads-b")
def ads_b():
    cursor4 = db.cursor()
    cursor4.execute("SELECT ID, ICAO, Callsign, NACp, CurrentDate FROM dbo.FlightDataNew order by ID DESC")

    rows = cursor4.fetchall()

    flight_data_list = []
    for row in rows:
        flight_data = FlightDataClass(*row)  # Unpack the tuple and create an instance of FlightData
        flight_data_list.append(flight_data)
    numberOfItems = len(flight_data_list)
    cursor4.close()

    return render_template('ads-b.html', flight_data_list = flight_data_list, numberOfItems = numberOfItems)

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
    try:
        cursor7.execute("SELECT TripID FROM FlightDataNew WHERE ID = ?", (flight_id,))
    except:
        pass

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
        return jsonify({'success': False, 'message': 'No available flight trip for this airplane'})

# Route to retrieve the status of all sensors
@app.route('/get_status_sensors')
async def get_status_sensors():
    sensor_status = {}  # Dictionary to hold device statuses

    # Create a list of asynchronous tasks to retrieve the status of each device
    tasks = [get_sensor_status(device_id) for device_id in devices.keys()]
    
    # Gather the results of asynchronous tasks
    results = await asyncio.gather(*tasks)
    
    # Update the sensor_status dictionary with device statuses
    sensor_status.update(zip(devices.keys(), results))
    
    # Return the device statuses as JSON
    return jsonify(sensor_status)

# Route to show the sensor statuses
@app.route('/status_sensors')
def status_sensors():
    return render_template('sensor_status.html')

thread_for_nacp_threshold = None
thread_for_stale_entries = None
thread_for_spoofing_check = None

"""
Decorator for connect
"""
@socketio.on('connect')
def connect():
    global thread_for_nacp_threshold
    global thread_for_stale_entries
    global thread_for_spoofing_check
    print('Client connected')

    with thread_lock:
        if thread_for_nacp_threshold is None:
            thread_for_nacp_threshold = socketio.start_background_task(check_nacp_threshold)
        if thread_for_stale_entries is None:
            thread_for_stale_entries = socketio.start_background_task(check_stale_entries)         
        if thread_for_spoofing_check is None:
            thread_for_spoofing_check = socketio.start_background_task(check_for_spoofing_continously)

if __name__=="__main__":
    if first_time_startup:
        initialize_flight_trips_overview()
        first_time_startup = False
    socketio.run(app, debug=True)
    db.close()