import subprocess
import pyModeS as mps
from collections import defaultdict

# Dictionary to store accumulated hex values for each ICAO address
hex_values_dict = defaultdict(list)

adsb_signals = [
    "5d47873a1d4f3c", "8d47808f584900aea9d0a23717b2", "8d47808f990c6d94404c9437b450", "8d47808f584b40aba9cfa4dea4ad",
    "8d47873a5823540dc1c6972abf93", "8d47873a990c3c9320608e7934f1", "8d47873a582d1405efc4d538999d", "a0000596001917154004580e21c6",
    "8c4ac9e9234c14f4c70de015458a", "8d47873a5833540071c3bc1936af", "8c4aca4239dda3638b582526eaa5",
    "a9000103204c14f4c70de0a81a7a", "a0000690c5a9400021942e6d5dbe", "a90001038db00030180000d8c9ee",
    "a8001691c5a93e00218c2f4c86f9", "8d47873a990c4194405c92771d9e", "8c4ac9e9e1010300000000e7777d",
    "8d47873a990c4194606892d4cbbe", "8d47873a5835a7fde3c3400734a4", "8d47873a990c4194606892d4cbbe",
    "8d47873a5835e0bc5fd7af11b36a", "8c4ac9e9e1010300000000e7777d", "8c4ac9e9381a0466630592422f11",
    "8d47873a583bc0b6e9d69bbef792", "8d47873a583db7f687c1d65e6dde", "8d47873a583f20b48bd623c97f1a",
    "8d47873a990c4394a0709422b2f0", "8d47873a990c4394a06c948a30f0", "5d47873a1d4f3c", "5d47873a1d4f3c",
    "8d47873a990c4394a06c948a30f0", "a00007b7c6293e0021d434e109be", "02c187b8a83242", "02c187b8a83242",
    "8d47873a990c4394c068947d828b", "a00007ba0018fb1640045dd2d50f", "8d47873a583fc7f4a5c17928da66",
    "8d47873a990c4494c064943cece1", "8d47873a583ff0b311d5d9c795c2", "8d47873a990c4494e064958664c1",
    "8d47873a584100b2f1d5d2092359", "8d47873a990c4494e064958664c1", "8d47873af8200002004ab82ab1e9",
    "8d47873a990c4495006095b02f44", "a90001038db00030180000d8c9ee", "8d47873ae1169100000000123339",
    "8d47873a584317f1f3c0f595662a", "8d47873a990c46954060953cc28a", "8c4ac9e9f9002603034938ce0a4f",
    "a8001691c6e9420021742e33438c", "8d47873a990c469560609579bea3", "8d47873a584370afd7d5358713ea",
    "8d47873a990c4595c05c96baf76e", "8c4ac9e9401a046657059ca69811", "8d47873a990c4f98000495f38af3",
    "5d47873a1d4f3c", "5d47873a1d4f3c"
]


def read_dump1090_raw():
    for line in adsb_signals:
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
            if nac_p[0] < 4:
                print(f"Might be currently jammed. NACp is: {nac_p[0]}")
        except RuntimeError:
            pass
        
        try:
            flight_callsign = mps.adsb.callsign(hex_value)
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



# import subprocess
# import pyModeS as mps

# # Dictionary to store accumulated hex values for each ICAO address
# hex_values_dict = {}

# def read_dump1090_raw():
#     process = subprocess.Popen(['/home/admin/dump1090/./dump1090', '--raw'], stdout=subprocess.PIPE, universal_newlines=True)
    
#     for line in process.stdout:
#         hex_value = line.strip()
#         print("Received ADS-B signal:", hex_value)
#         icao_address = mps.adsb.icao(hex_value)  # Extract ICAO address
        
#         if icao_address is not None:
#             hex_values_dict.setdefault(icao_address, []).append(hex_value)  # Accumulate hex values for the ICAO address
#             process_hex_values(icao_address)

# def process_hex_values(icao_address):
#     if icao_address in hex_values_dict:
#         hex_values = hex_values_dict.pop(icao_address)  # Get accumulated hex values for the ICAO address
        
#         for hex_value in hex_values:
#             hex_value = hex_value.strip("*;")
#             print("Received ADS-B signal:", hex_value)
            
#             try:
#                 nac_p = mps.decoder.adsb.nac_p(hex_value)
#                 print(f"Flight has NACp value: {nac_p}")
#                 if nac_p[0] < 4:
#                     print(f"Might be currently jammed. NACp is: {nac_p[0]}")
#             except RuntimeError:
#                 pass
            
#             try:
#                 flight_callsign = mps.adsb.callsign(hex_value)
#                 print(f"Flight callsign: {flight_callsign}")
#             except RuntimeError:
#                 pass

# if __name__ == "__main__":
#     read_dump1090_raw()