import subprocess
import pyModeS as mps


hex_values_dict = {}

def read_dump1090_raw():
    process = subprocess.Popen(['/home/admin/dump1090/./dump1090', '--raw'], stdout=subprocess.PIPE, universal_newlines=True)
    
    for line in process.stdout:
        hex_value = line.strip()
        print("Received ADS-B signal:", hex_value)
        icao_address = mps.adsb.icao(hex_value)  # Extract ICAO address
        
        if icao_address is not None:
            hex_values_dict.setdefault(icao_address, []).append(hex_value)  # Accumulate hex values for the ICAO address

    # Process accumulated hex values for each ICAO address
    for icao_address, hex_values in hex_values_dict.items():
        process_hex_values(icao_address, hex_values)

def process_hex_values(icao_address, hex_values):
    print(f"Processing hex values for ICAO address {icao_address}")
    flight_callsign = None
    nac_p = None
    
    for hex_value in hex_values:
        hex_value = hex_value.strip("*;")
        
        try:
            nac_p = mps.decoder.adsb.nac_p(hex_value)
            print(nac_p)
            if nac_p[0] < 4:
                print(f"Might be currently jammed. NACp is: {nac_p[0]}")
        except RuntimeError:
            pass
        
        try:
            flight_callsign = mps.adsb.callsign(hex_value)
            print(flight_callsign)
        except RuntimeError:
            pass

        if flight_callsign and nac_p:
            print(f"Flight {flight_callsign} with icao {icao_address} has NACp value: {nac_p}")
            flight_callsign = None
            nac_p = None
        else:
            pass

if __name__ == "__main__":
    read_dump1090_raw()