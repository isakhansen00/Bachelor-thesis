import pyodbc
from credentials import *
import pyModeS as mps


db = pyodbc.connect('DRIVER=' + driver + ';SERVER=' +
    server + ';PORT=1433;DATABASE=' + database +
    ';UID=' + username + ';PWD=' + password + ";Mars_Connection=yes")

def calculate_TDoA(signal_arrival_times):
    # Calculate time differences between sensors
    time_diffs = {}
    processed_pairs = set()  # Keep track of processed sensor pairs
    
    for sensor1, time1 in signal_arrival_times.items():
        for sensor2, time2 in signal_arrival_times.items():
            if sensor1 != sensor2 and (sensor1, sensor2) not in processed_pairs and (sensor2, sensor1) not in processed_pairs:
                # Convert nanoseconds to seconds with decimals
                time_diff_seconds = abs((time1 - time2) / 1e9)  # Ensure positive time difference
                time_diffs[(sensor1, sensor2)] = time_diff_seconds
                processed_pairs.add((sensor1, sensor2))
    
    # Sort and select the top three time differences
    top_three_diffs = dict(sorted(time_diffs.items(), key=lambda item: item[1], reverse=True)[:3])
    
    return top_three_diffs


cursor = db.cursor()
cursor.execute("""
SELECT th.HexValue, th.DeviceID, th.HexTimestamp
FROM TimestampedHexvalues th
JOIN (
    SELECT HexValue
    FROM TimestampedHexvalues
    GROUP BY HexValue
    HAVING COUNT(DISTINCT DeviceID) = (SELECT COUNT(DISTINCT DeviceID) FROM TimestampedHexvalues)
) subquery ON th.HexValue = subquery.HexValue;
""")

hex_value_groups = {}  # Dictionary to store groups of records by hex value

for row in cursor.fetchall():
    hex_value, device_id, arrival_time = row
    #print(hex_value)
    if hex_value not in hex_value_groups:
        hex_value_groups[hex_value] = {'arrival_times': {}}
    hex_value_groups[hex_value]['arrival_times'][device_id] = arrival_time
#print(hex_value_groups)

icao_hex_values = {}  # Dictionary to store hex values for each ICAO address
for hex_value, group_data in hex_value_groups.items():
    icao_address = mps.adsb.icao(hex_value)
    #print(group_data)
    if icao_address:
        icao_hex_values.setdefault(icao_address, []).append(group_data)

hex_values_data = []
for icao_address, hex_values in icao_hex_values.items():
    time_diffs = {}
    print(hex_values)
    for hex_value_data in hex_values:
        group_data = hex_value_data['arrival_times']
        print(len(group_data))
        #if len(group_data) >= 3:  # Only process groups with at least 3 different device IDs
        time_diffs.update(calculate_TDoA(group_data))
            #print(icao_address)
    print(time_diffs)
    if time_diffs:  # Only calculate delta_tdoa if there are time differences
        delta_tdoa = max(time_diffs.values()) - min(time_diffs.values())
        hex_values_data.append({'icao_address': icao_address, 'delta_tdoa': delta_tdoa})


print(hex_values_data)