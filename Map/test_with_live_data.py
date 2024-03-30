import subprocess
import pyModeS as mps
import threading
import time
import sys
sys.path.insert(0, './Map')
from map import generate_map

hex_values_dict = {}
flight_positions = {}
flight_data = {}
 
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
    # msg_even = None
    # msg_odd = None
    # t_even = None
    # t_odd = None
    
    for hex_value in new_hex_values:

        try:
            nac_p = mps.decoder.adsb.nac_p(hex_value)
        except RuntimeError:
            pass
        
        try:
            flight_callsign = mps.adsb.callsign(hex_value)
        except RuntimeError:
            pass

        type_code_msg0 = mps.typecode(hex_value)

        if icao_address not in flight_data:
                        flight_data[icao_address] = [None, None, None, None]
        
        if type_code_msg0 in [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22]:
            binary_msg = bin(int(hex_value, 16))[2:].zfill(112)  # Convert hex to binary
            if binary_msg[55] == '0':
                # msg_even = hex_value
                # t_even = int(time.time())
                flight_data[icao_address][0] = hex_value
                flight_data[icao_address][1] = int(time.time())
            elif binary_msg[55] == '1':
                # msg_odd = hex_value
                # t_odd = int(time.time())
                flight_data[icao_address][2] = hex_value
                flight_data[icao_address][3] = int(time.time())
                
        #if flight_callsign and msg_even and msg_odd and t_even and t_odd:
        if flight_callsign is not None and None not in flight_data[icao_address]:
            even_timestamp = flight_data[icao_address][1]
            odd_timestamp = flight_data[icao_address][3]
            time_difference = abs(even_timestamp - odd_timestamp)
            if time_difference < 15:
                try:
                    # position = mps.adsb.airborne_position(msg_even, msg_odd, t_even, t_odd)
                    position = mps.adsb.airborne_position(flight_data[icao_address][0], flight_data[icao_address][2], flight_data[icao_address][1], flight_data[icao_address][3])
                    if position:
                        longitude, latitude = position
                        if icao_address not in flight_positions:
                            flight_positions[icao_address] = [flight_callsign, ]
                        positions_for_icao = flight_positions[icao_address]
                        # Checking if latitude and longitude is already in the position dictionary
                        if (longitude, latitude) not in positions_for_icao:
                            flight_positions[icao_address].append((longitude, latitude))
                        #print(flight_positions)
                        print(f"NACp {nac_p}")
                        print(f"Flight {flight_callsign} with icao {icao_address} has position: LO: {longitude}, LA: {latitude}")
                        # msg_even = None
                        # msg_odd = None
                        # t_even = None
                        # t_odd = None
                        print(len(flight_data))
                        if icao_address in flight_data:
                            del flight_data[icao_address]
                        if icao_address.upper() in flight_data:
                            del flight_data[icao_address.upper()]
                        print(len(flight_data))
                except RuntimeError:
                    pass
            else:
                del flight_data[icao_address]

# Function to periodically check and remove stale entries from flight_data
def check_stale_entries():
    while True:
        current_time = time.time()
        stale_threshold = 300  # 5 minutes (300 seconds)

        for icao_address, data in list(flight_data.items()):  # Use list() to avoid modifying dictionary during iteration
            # Check if both even and odd messages are None and the last update time is older than the stale threshold
            if data[2] is None or data[3] is None and current_time - data[1] > stale_threshold:
                del flight_data[icao_address]  # Remove stale entry
                print("DONE")

        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    dump_thread = threading.Thread(target=read_dump1090_raw)
    stale_entries_thread = threading.Thread(target=check_stale_entries)
    dump_thread.start()
    stale_entries_thread.start()

    while True:
        if len(flight_positions) > 0:
            generate_map(flight_positions)
            time.sleep(5)
