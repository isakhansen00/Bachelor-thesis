import subprocess
import pyModeS as mps
import threading
import time

hex_values_dict = {}

def read_dump1090_raw():
    process = subprocess.Popen(['python', 'Testing/signals.py'], stdout=subprocess.PIPE, universal_newlines=True)
    
    for line in process.stdout:
        hex_value = line.strip()
        hex_value = hex_value.replace("*", "")
        hex_value = hex_value.replace(";", "")
        print("Received ADS-B signal:", hex_value)
        time.sleep(0.5)
        icao_address = mps.adsb.icao(hex_value)  # Extract ICAO address
        if icao_address is not None:
            hex_values_dict.setdefault(icao_address, []).append(hex_value)  # Accumulate hex values for the ICAO address
            process_hex_values(icao_address)  # Process newly appended hex values for the ICAO address

def process_hex_values(icao_address):
    hex_values = hex_values_dict.get(icao_address, [])
    print(f"Processing hex values for ICAO address {icao_address}")
    last_processed_index = getattr(process_hex_values, f"last_index_{icao_address}", 0)
    new_hex_values = hex_values[last_processed_index:]
    
    flight_callsign = None
    nac_p = None
    
    for hex_value in new_hex_values:
        hex_value = hex_value.strip("*;")
        
        try:
            nac_p = mps.decoder.adsb.nac_p(hex_value)
            if nac_p[0] < 10:
                print(f"Potential jamming detected. NACp is: {nac_p[0]}")
        except RuntimeError:
            pass
        
        try:
            flight_callsign = mps.adsb.callsign(hex_value)
        except RuntimeError:
            pass
    
    if flight_callsign and nac_p:
        print(f"Flight {flight_callsign} with icao {icao_address} has NACp value: {nac_p}")
        if nac_p[0] < 10:
            print(f"Potential jamming of flight {flight_callsign} detected. NACp is: {nac_p[0]}")
        setattr(process_hex_values, f"last_index_{icao_address}", len(hex_values))  # Update last processed index

if __name__ == "__main__":
    dump_thread = threading.Thread(target=read_dump1090_raw)
    dump_thread.start()
    dump_thread.join()
