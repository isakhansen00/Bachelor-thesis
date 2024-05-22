import pyodbc
from credentials import *
import pyModeS as mps
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import numpy as np
import datetime
import pymssql
import time
conn = pymssql.connect(server, username, password, database)




def detect_spoofing(average_tdoa_values, threshold_percent):
    # Convert the list to a NumPy array
    tdoa_array = np.array(average_tdoa_values)
    
    # Calculate the absolute differences between each pair of values
    diff_matrix = np.abs(tdoa_array[:, None] - tdoa_array)
    
    # Calculate the maximum value between each pair of values
    max_matrix = np.maximum(tdoa_array[:, None], tdoa_array)
    
    # Calculate the percentage differences
    percentage_diff_matrix = diff_matrix / max_matrix
    
    # Set the diagonal elements to a value greater than the threshold to exclude them from consideration
    np.fill_diagonal(percentage_diff_matrix, threshold_percent + 1)
    
    # Check if any percentage difference exceeds the threshold
    if np.any(percentage_diff_matrix > threshold_percent):
        return False
    else:
        return True

# # Function to retrieve delta_tdoa values for a given icao_id from the Delta_TDOA table
def retrieve_delta_tdoa(icao_id):
    cursor = conn.cursor()
    cursor.execute("SELECT icao_address, average_tdoa FROM TDOAValues WHERE icao_address = %s", (icao_id,))
    rows = cursor.fetchall()
    icao_and_delta_tdoa_values = {}
    
    for row in rows:
        icao_address = row[0]
        tdoa_value = row[1]
        if icao_address not in icao_and_delta_tdoa_values:
            icao_and_delta_tdoa_values[icao_address] = [tdoa_value]
        else:
            icao_and_delta_tdoa_values[icao_address].append(tdoa_value)
            
    return icao_and_delta_tdoa_values



def calculate_TDoA(signal_arrival_times):
    # Calculate time differences between sensors
    time_diffs = {}
    processed_pairs = set()  # Keep track of processed sensor pairs
    
    for sensor1, time1 in signal_arrival_times.items():
        for sensor2, time2 in signal_arrival_times.items():
            if sensor1 != sensor2 and (sensor1, sensor2) not in processed_pairs and (sensor2, sensor1) not in processed_pairs:
                # Convert nanoseconds to seconds with decimals
                time_diff_seconds = abs((time1 - time2))
                # Ensure positive time difference
                time_diffs[(sensor1, sensor2)] = time_diff_seconds
                processed_pairs.add((sensor1, sensor2))
    
    # Sort and select the top three time differences
    top_three_diffs = dict(sorted(time_diffs.items(), key=lambda item: item[1], reverse=True)[:3])
    
    return top_three_diffs


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
    ) subquery ON th.HexValue = subquery.HexValue;
    """)
    rows = cursor.fetchall()
    cursor.close()
    return rows

cursor = conn.cursor()
new_data = get_new_timestamped_hex_values()
icao_delta_tdoa = {}
hex_value_groups = {}  # Dictionary to store groups of records by hex value
if new_data:
    for row in new_data:
        hex_value, device_id, arrival_time = row
        #print(row)
        #print(hex_value)
        #cursor.execute("UPDATE TimestampedHexvalues SET isprocessed = 1 WHERE HexValue = %s AND DeviceID = %s AND HexTimestamp = %s", (hex_value, device_id, arrival_time))
        if hex_value not in hex_value_groups:
            hex_value_groups[hex_value] = {'arrival_times': {}}
        hex_value_groups[hex_value]['arrival_times'][device_id] = arrival_time
    #print(hex_value_groups)

    icao_hex_values = {}  # Dictionary to store hex values for each ICAO address
    for hex_value, group_data in hex_value_groups.items():
        icao_address = mps.adsb.icao(hex_value)
        print(icao_address)
        if icao_address:
            icao_hex_values.setdefault(icao_address, []).append(group_data)
    #print(icao_hex_values)
    hex_values_data = []
    for icao_address, hex_values in icao_hex_values.items():
        for hex_value_data in hex_values:
            group_data = hex_value_data['arrival_times']
            time_diffs = []
            if len(group_data) >= 2:  # Only process groups with at least 3 different device IDs
                #print(hex_value)
                for _, time_diff in calculate_TDoA(group_data).items():
                    time_diffs.append(time_diff)
                if time_diffs:  # Only calculate average TDoA if there are time differences
                    average_tdoa = round(sum(time_diffs) / len(time_diffs))
                    hex_values_data.append({'icao_address': icao_address, 'average_tdoa': average_tdoa})

                    # Store delta_tdoa values for each icao_address
                if icao_address in icao_delta_tdoa:
                    icao_delta_tdoa[icao_address].append(average_tdoa)
                else:
                    icao_delta_tdoa[icao_address] = [average_tdoa]
                    # Retrieve delta_tdoa values for the current ICAO address from Delta_TDOA table
                

#     # #Insert data into the ICAO and Delta_TDOA tables
#     for icao_address, delta_tdoa_values in icao_delta_tdoa.items():
#         for average_tdoa in delta_tdoa_values:
#             # Insert the data into the Delta_TDOA table
#             cursor.execute("""
#             INSERT INTO dbo.TDOAValues (icao_address, average_tdoa, timestamp, TripID)
#             SELECT %s, %s, %s, ft.TripID
#             FROM dbo.FlightTrips ft
#             WHERE ft.ICAO = %s
#             AND ft.TripTimestamp = (SELECT MAX(TripTimestamp) FROM dbo.FlightTrips WHERE ICAO = %s)
#             UNION ALL
#             SELECT %s, %s, %s, NULL
#             WHERE NOT EXISTS (SELECT 1 FROM dbo.FlightTrips WHERE ICAO = %s)
#             """, (icao_address, average_tdoa, datetime.datetime.now(), icao_address, icao_address,
#             icao_address, average_tdoa, datetime.datetime.now(), icao_address))
#             conn.commit()
#             print(f"ICAO Address: {icao_address} Average TDOA: {average_tdoa} ")
#             time.sleep(0.01)
#             threshold = 0.1  # Define the threshold for similarity

#     for icao_address, average_tdoa_values in icao_delta_tdoa.items():
#         #hei = retrieve_delta_tdoa(icao_address)
#         #print(f"ICAO: {hei[icao_address]}")
#         if len(average_tdoa_values) >= 2:
#             if detect_spoofing(average_tdoa_values, threshold_percent=0.01):
#                 print(f"Spoofing detected for ICAO address: {icao_address}")
#             else:
#                 print(f"No spoofing detected")
            # Perform further actions if spoofing is detected
#hei = retrieve_delta_tdoa(icao_address)
#print(hei)
# for icao_and_tdoa in hei:
#     print(f"ICAO: {icao_and_tdoa[icao_address]}  Average TDOA: {icao_and_tdoa['average_tdoa']}")

dicts = {('RaspberryPiFauskeISE', 'RaspberryPiMorkved'): 4.225672335, ('RaspberryPiMorkved', 'RaspberryPiBodo'): 1.369866671,
          ('RaspberryPiFauskeISE', 'RaspberryPiBodo'): 3.895534791, ('RaspberryPiBodo', 'RaspberryPiFauskeISE'): 14.95545792, 
         ('RaspberryPiBodo', 'RaspberryPiMorkved'): 10.729785585, ('RaspberryPiMorkved', 'RaspberryPiFauskeISE'): 0.372314123}




# # Example usage:
average_tdoa_values = [549244234, 500205401, 148178856, 297453083, 602504618, 604200218, 239044141,
                        456434157, 100613973, 829662463, 3824559857, 3781409585, 11043145028,
                          13975200327, 3199547847, 414789102, 149857001]

def check_for_spoofing(tdoa_values):
    tdoa_array = np.array(tdoa_values)
    mean_value = np.mean(tdoa_array)
    std_dev = np.std(tdoa_array)
    coefficient_of_variation = std_dev / mean_value
    
    # Check if the coefficient of variation is less than 10%
    if coefficient_of_variation < 10:
        return True
    else:
        return False

#average_tdoa_values = [549244234, 509244234, 589244233, 449244236, 549244235]
threshold_percent = 0.2  # 1% threshold
spoofing_detected = check_for_spoofing(average_tdoa_values)
if spoofing_detected:
    print("Potential spoofing detected!")
else:
    print("No potential spoofing detected.")

# values = [
#     -1.093e-02, -1.002e-02, -9.367e-03, -1.766e-03, -1.314e-03, 1.034e-03, 7.813e-05, -4.410e-05, 6.076e-04,
#     5.079e-04, -6.041e-04, -1.596e-03, -3.135e-03, 9.764e-04, 9.524e-04, -1.675e-02, -1.683e-02, -1.697e-02,
#     -1.550e-02, -7.484e-04, -1.114e-03, -1.007e-03, 1.215e-04, -1.633e-02, -1.741e-02, -1.737e-02, -1.725e-02,
#     -1.753e-02, -1.771e-02, -4.552e-04, -1.681e-04, 7.801e-05, -1.722e-02, -1.722e-02, -1.740e-02, -1.826e-02,
#     -1.873e-02, -1.866e-02, 5.765e-05, 6.414e-04, 6.081e-04, 3.950e-03, 9.307e-04, 6.177e-04, 1.550e-03, -2.740e-04,
#     7.180e-04, -2.537e-03, -1.207e-03, -2.048e-03, 2.002e-04, 4.828e-04, -2.108e-04, -2.477e-03, -3.709e-03,
#     -1.727e-02, -1.640e-02, -2.447e-04, 1.363e-03, -2.681e-04, 3.696e-04, -9.651e-05, 5.671e-04, -1.503e-02,
#     -2.088e-04, 3.629e-05, -3.269e-03, -6.864e-03, -1.097e-02, -1.305e-02, -7.085e-03, -9.760e-03, -1.854e-02,
#     -1.955e-02, -1.854e-02, -1.882e-02, -2.023e-02, -2.043e-02, -2.064e-02, -2.037e-02, -2.885e-02, -2.556e-02,
#     -2.727e-02, -2.771e-02, -2.875e-02, -2.932e-02, -2.203e-02, -2.296e-02, -2.106e-02, -1.949e-02, -1.798e-02,
#     -1.670e-02, -1.553e-02, -1.355e-02, -1.310e-02, -1.198e-02, -4.162e-04, -8.271e-04, -1.618e-03, -1.815e-03,
#     -8.066e-03, -9.706e-03, -1.100e-02, -1.127e-02, -2.245e-02, -2.273e-02, -2.204e-02, -1.916e-02, -1.719e-02,
#     -1.701e-02, -1.803e-02, -1.929e-02, -2.117e-02, -1.886e-02, -1.602e-02, -1.367e-02, -1.332e-02, -1.323e-02,
#     -1.351e-02, -1.491e-02, -1.472e-02, -1.476e-02, -1.418e-02, -1.381e-02, -1.374e-02, -1.408e-02, -1.348e-02,
#     -1.319e-03, -1.488e-02, -1.481e-02, -1.649e-02, -1.616e-02, -1.459e-02, -1.263e-02, -1.193e-02, -1.097e-02,
#     -1.155e-02
# ]

# average = sum(values) / len(values)
# print(average)