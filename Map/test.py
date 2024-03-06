import subprocess
import pyModeS as mps
import threading

hex_values_dict = {}

def read_dump1090_raw():
    process = subprocess.Popen(['/home/admin/dump1090/./dump1090', '--raw'], stdout=subprocess.PIPE, universal_newlines=True)
    
    for line in process.stdout:
        hex_value = line.strip()
        hex_value = hex_value.replace("*", "")
        hex_value = hex_value.replace(";", "")
        print("Received ADS-B signal:", hex_value)
        icao_address = mps.adsb.icao(hex_value)  # Extract ICAO address
        if icao_address is not None:
            hex_values_dict.setdefault(icao_address, []).append(hex_value)  # Accumulate hex values for the ICAO address
            
            # Decode ADS-B messages and extract position
            if len(hex_values_dict[icao_address]) >= 2:
                msg0 = hex_values_dict[icao_address][-2]
                msg1 = hex_values_dict[icao_address][-1]
                
                # Extract Type Codes from the messages
                type_code_msg0 = mps.util.typecode(msg0)
                type_code_msg1 = mps.util.typecode(msg1)
                
                # Check if Type Codes fall within the specified ranges (9-18 or 20-22)
                if 9 <= type_code_msg0 <= 18 and 9 <= type_code_msg1 <= 18:
                    # Extract Compact Position Reporting (CPR) format
                    lat_cpr = mps.adsb.cpr_latitude(msg0, msg1)
                    lon_cpr = mps.adsb.cpr_longitude(msg0, msg1)
                    if lat_cpr is not None and lon_cpr is not None:
                        # Decode latitude and longitude from CPR format
                        latitude, longitude = mps.adsb.cpr_decode(lat_cpr, lon_cpr)
                        print("Latitude:", latitude)
                        print("Longitude:", longitude)
                elif 20 <= type_code_msg0 <= 22 and 20 <= type_code_msg1 <= 22:
                    # Extract Compact Position Reporting (CPR) format for Type Codes 20-22
                    lat_cpr = mps.adsb.cpr_latitude(msg0, msg1)
                    lon_cpr = mps.adsb.cpr_longitude(msg0, msg1)
                    if lat_cpr is not None and lon_cpr is not None:
                        # Decode latitude and longitude from CPR format
                        latitude, longitude = mps.adsb.cpr_decode(lat_cpr, lon_cpr)
                        print("Latitude:", latitude)
                        print("Longitude:", longitude)
                else:
                    print("Invalid message types for position decoding")
    
    print(hex_values_dict)

if __name__ == "__main__":
    dump_thread = threading.Thread(target=read_dump1090_raw)
    dump_thread.start()
    dump_thread.join()

