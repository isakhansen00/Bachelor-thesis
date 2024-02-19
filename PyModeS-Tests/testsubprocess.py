# import subprocess
# import  pyModeS as mps

# def read_dump1090_raw():

#     process = subprocess.Popen(['/home/admin/dump1090/./dump1090', '--raw'], stdout=subprocess.PIPE, universal_newlines=True)
    
#     for line in process.stdout:
#         hex_value = line.strip()
#         process_hex_value(hex_value)

# def process_hex_value(hex_value):
#     hex_value = hex_value.strip("*;")
#     print("Received ADS-B signal:", hex_value)
#     try:
#         nac_p = mps.decoder.adsb.nac_p(hex_value)
#         print(f"Flight wassup my G \nHas NACp value: {nac_p}")
#         if nac_p[0] < 4:
#             print(f"Flight wassup my G Might be currently jammed \n NACp is: {nac_p[0]}")
#     except RuntimeError:
#         pass

#     try:
#         flight_callsign = mps.adsb.callsign(hex_value)
#     except RuntimeError:
#         pass


# if __name__ == "__main__":
#     read_dump1090_raw()

import subprocess
import pyModeS as mps

# Dictionary to store accumulated hex values for each ICAO address
hex_values_dict = {}

def read_dump1090_raw():
    process = subprocess.Popen(['/home/admin/dump1090/./dump1090', '--raw'], stdout=subprocess.PIPE, universal_newlines=True)
    
    for line in process.stdout:
        hex_value = line.strip()
        icao_address = mps.adsb.icao(hex_value)  # Extract ICAO address
        
        if icao_address is not None:
            hex_values_dict.setdefault(icao_address, []).append(hex_value)  # Accumulate hex values for the ICAO address
            process_hex_values(icao_address)

def process_hex_values(icao_address):
    if icao_address in hex_values_dict:
        hex_values = hex_values_dict.pop(icao_address)  # Get accumulated hex values for the ICAO address
        
        for hex_value in hex_values:
            hex_value = hex_value.strip("*;")
            print("Received ADS-B signal:", hex_value)
            
            try:
                nac_p = mps.decoder.adsb.nac_p(hex_value)
                print(f"Flight has NACp value: {nac_p}")
                if nac_p[0] < 4:
                    print(f"Might be currently jammed. NACp is: {nac_p[0]}")
            except RuntimeError:
                pass
            
            try:
                flight_callsign = mps.adsb.callsign(hex_value)
                print(f"Flight callsign: {flight_callsign}")
            except RuntimeError:
                pass

if __name__ == "__main__":
    read_dump1090_raw()