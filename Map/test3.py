import subprocess
import pyModeS as mps
import threading
import time
import sys
sys.path.insert(0, './Map')
from map import generate_map

hex_values_dict = {}
flight_positions = {}
 
def read_dump1090_raw():
    process = subprocess.Popen(['/home/admin/dump1090/./dump1090', '--raw'], stdout=subprocess.PIPE, universal_newlines=True)
    
    for line in process.stdout:
        hex_value = line.strip()
        hex_value = hex_value.replace("*", "")
        hex_value = hex_value.replace(";", "")
        # print("Received ADS-B signal:", hex_value)
        icao_address = mps.adsb.icao(hex_value)  # Extract ICAO address
        if icao_address is not None:
            hex_values_dict.setdefault(icao_address, []).append(hex_value)  # Accumulate hex values for the ICAO address
            process_hex_values(icao_address)  # Process newly appended hex values for the ICAO address

def process_hex_values(icao_address):
    hex_values = hex_values_dict.get(icao_address, [])
    # print(f"Processing hex values for ICAO address {icao_address}")
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
        
        if type_code_msg0 in [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22]:
            binary_msg = bin(int(hex_value, 16))[2:].zfill(112)  # Convert hex to binary
            if binary_msg[55] == '0':
                msg_even = hex_value
                t_even = int(time.time())
            elif binary_msg[55] == '1':
                msg_odd = hex_value
                t_odd = int(time.time())
                
        if flight_callsign and msg_even and msg_odd and t_even and t_odd:
            try:
                position = mps.adsb.airborne_position(msg_even, msg_odd, t_even, t_odd)
                if position:
                    longitude, latitude = position
                    if icao_address not in flight_positions:
                        flight_positions[icao_address] = [flight_callsign, ]
                    flight_positions[icao_address].append((longitude, latitude))
                    #print(flight_positions)
                    print(f"Flight {flight_callsign} with icao {icao_address} has position: LO: {longitude}, LA: {latitude}")
                    msg_even = None
                    msg_odd = None
                    t_even = None
                    t_odd = None
            except RuntimeError:
                pass

if __name__ == "__main__":
    dump_thread = threading.Thread(target=read_dump1090_raw)
    dump_thread.start()
    dump_thread.join()

    while True:
        if len(flight_positions) > 1:
            generate_map(flight_positions)
            time.sleep(20)
