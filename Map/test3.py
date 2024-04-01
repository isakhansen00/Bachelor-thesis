import subprocess
import pyModeS as mps
import threading
import time
import sys
sys.path.insert(0, './Map')
from map import generate_map
import requests

hex_values_dict = {}
flight_positions = {}
flight_data = {}
 
def read_dump1090_raw():
    process = subprocess.Popen(['/home/admin/dump1090/./dump1090', '--raw', '--net'], stdout=subprocess.PIPE, universal_newlines=True)
        
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
            nac_p = mps.decoder.adsb.nac_p(hex_value)
        except RuntimeError:
            pass
            
        try:
            flight_callsign = mps.adsb.callsign(hex_value)
        except RuntimeError:
            pass

def fetch_airplane_data():
    try:
        response = requests.get("http://localhost:8080/data.json")
        if response.status_code == 200:
            data = response.json()
            for airplane in data:
                hex_value = airplane["hex"]
                lat = airplane["lat"]
                lon = airplane["lon"]

                # If ICAO address already exists in dictionary, append new coordinates if they are unique
                if hex_value in flight_positions:
                    if (lat, lon) not in flight_positions[hex_value]:
                        flight_positions[hex_value].append((lat, lon))
                else:
                    flight_positions[hex_value] = [(lat, lon)]
                
                print(flight_positions)
        else:
            print("Failed to fetch data:", response.status_code)
    except Exception as e:
        print("An error occurred while fetching data:", e)

if __name__ == "__main__":
    dump_thread = threading.Thread(target=read_dump1090_raw)
    dump_thread.start()

    while True:
        time.sleep(5)
        # Fetch airplane data periodically
        fetch_airplane_data()
        time.sleep(15)
