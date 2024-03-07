import subprocess
import pyModeS as mps
import threading
import json
from azure.iot.device import IoTHubDeviceClient, Message
import time
import folium

hex_values_dict = {}
plane_positions = {}  # Dictionary to store plane positions

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
    global plane_positions
    hex_values = hex_values_dict.get(icao_address, [])
    last_processed_index = getattr(process_hex_values, f"last_index_{icao_address}", 0)
    new_hex_values = hex_values[last_processed_index:]

    flight_callsign = None
    msg_even = None
    msg_odd = None
    t_even = None
    t_odd = None
    
    for hex_value in new_hex_values:
        try:
            flight_callsign = mps.adsb.callsign(hex_value)
        except RuntimeError:
            pass

        type_code_msg0 = mps.typecode(hex_value)
        
        if type_code_msg0 in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22]:
            binary_msg = bin(int(hex_value, 16))[2:].zfill(112)  # Convert hex to binary
            if binary_msg[54] == '0':
                msg_even = hex_value
                t_even = int(time.time())
            elif binary_msg[54] == '1':
                msg_odd = hex_value
                t_odd = int(time.time())
                
        if flight_callsign and msg_even and msg_odd and t_even and t_odd:
            try:
                position = mps.adsb.position(msg_even, msg_odd, t_even, t_odd)
                if position:
                    longitude, latitude = position
                    print(f"Flight {flight_callsign} with icao {icao_address} has position: LO: {longitude}, LA: {latitude}")
                    if icao_address not in plane_positions:
                        plane_positions[icao_address] = []
                    plane_positions[icao_address].append((latitude, longitude))
                    msg_even = None
                    msg_odd = None
                    t_even = None
                    t_odd = None
            except RuntimeError:
                pass
    
    setattr(process_hex_values, f"last_index_{icao_address}", len(hex_values))  # Update last processed index


def generate_map():
    global plane_positions
    while True:
        map_obj = folium.Map(location=[0, 0], zoom_start=2)
        for icao_address, positions in plane_positions.items():
            for position in positions:
                folium.Marker(position, tooltip=f"ICAO: {icao_address}").add_to(map_obj)
        map_obj.save("map.html")
        time.sleep(10)  # Update map every 10 seconds


if __name__ == "__main__":
    dump_thread = threading.Thread(target=read_dump1090_raw)
    map_thread = threading.Thread(target=generate_map)
    dump_thread.start()
    map_thread.start()
    dump_thread.join()
    map_thread.join()
