sys.path.insert(0, '../UI')
from credentials import *
import pyodbc

db = pyodbc.connect('DRIVER=' + driver + ';SERVER=' +
    server + ';PORT=1433;DATABASE=' + database +
    ';UID=' + username + ';PWD=' + password + ";Mars_Connection=yes")

def get_latest_trip_id(icao_address):
    cursor6 = db.cursor()
    cursor6.execute("""
        SELECT TripID 
        FROM FlightTrips 
        WHERE ICAO = ? 
        AND TripTimestamp = (
            SELECT MAX(TripTimestamp) 
            FROM FlightTrips 
            WHERE ICAO = ?
        )
    """, (icao_address, icao_address))
    trip_id = cursor6.fetchone()
    cursor6.close()
    return trip_id[0] if trip_id else None

def save_flight_positions(flight_positions):
    cursor5 = db.cursor()
    for icao_address, position_data in flight_positions.items():
        trip_id = get_latest_trip_id(icao_address)
        if trip_id is not None:
            for data in position_data[1:]:
                lat, lon = data
                cursor5.execute("INSERT INTO FlightTripPositions (ICAO, TripID, Latitude, Longitude) VALUES (?, ?, ?)", (icao_address, trip_id, lat, lon))
    db.commit()
    cursor5.close()