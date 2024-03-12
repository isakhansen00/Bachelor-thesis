import subprocess
import pyModeS as mps
import threading
import json
from azure.iot.device import IoTHubDeviceClient, Message
import time
from geopy.distance import great_circle

hex_values_dict = {}
planes_dict = {}

def read_dump1090_raw():
    process = subprocess.Popen(['/home/admin/dump1090/./dump1090', '--raw'], stdout=subprocess.PIPE, universal_newlines=True)

    for line in process.stdout:
        hex_value = line.strip()
        hex_value = hex_value.replace("*", "")
        hex_value = hex_value.replace(";", "")
        icao_address = mps.adsb.icao(hex_value)  # Extract ICAO address
        if icao_address is not None:
            hex_values_dict.setdefault(icao_address, []).append(hex_value)  # Accumulate hex values for the ICAO address
            process_hex_values(icao_address)  # Process newly appended hex values for the ICAO address

def process_hex_values(icao_address):
    hex_values = hex_values_dict.get(icao_address, [])
    last_processed_index = getattr(process_hex_values, f"last_index_{icao_address}", 0)
    new_hex_values = hex_values[last_processed_index:]

    for hex_value in new_hex_values:
        try:
            flight_callsign = mps.adsb.callsign(hex_value)
        except RuntimeError:
            continue

        type_code_msg0 = mps.typecode(hex_value)

        if type_code_msg0 in [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22]:
            binary_msg = bin(int(hex_value, 16))[2:].zfill(112)  # Convert hex to binary
            if binary_msg[54] == '0':
                planes_dict.setdefault(icao_address, {}).setdefault("even", []).append(hex_value)
            elif binary_msg[54] == '1':
                planes_dict.setdefault(icao_address, {}).setdefault("odd", []).append(hex_value)

    for icao, plane_data in planes_dict.items():
        if "even" in plane_data and "odd" in plane_data:
            process_airborne_position(icao, plane_data["even"], plane_data["odd"])

def process_airborne_position(icao_address, even_msgs, odd_msgs):
    for even_msg in even_msgs:
        for odd_msg in odd_msgs:
            try:
                t_even = int(time.time())
                t_odd = int(time.time())
                position = mps.adsb.airborne_position(even_msg, odd_msg, t_even, t_odd)
                if position:
                    longitude, latitude = position
                    if last_position and last_position_time:
                        distance = great_circle(last_position, position).nautical
                        time_difference = t_even - last_position_time
                        if distance <= 3 and time_difference <= 15:
                            print(f"Flight {icao_address} has position: LO: {longitude}, LA: {latitude}")
                            # Save longitude and latitude to the database along with other information
                    last_position = position
                    last_position_time = t_even
            except RuntimeError:
                continue

if __name__ == "__main__":
    dump_thread = threading.Thread(target=read_dump1090_raw)
    dump_thread.start()
    dump_thread.join()
