import subprocess
import  pyModeS as mps

def read_dump1090_raw():

    process = subprocess.Popen(['/home/admin/dump1090/./dump1090', '--raw'], stdout=subprocess.PIPE, universal_newlines=True)
    
    for line in process.stdout:
        hex_value = line.strip()
        process_hex_value(hex_value)

def process_hex_value(hex_value):
    hex_value = hex_value.strip("*;")
    print("Received ADS-B signal:", hex_value)
    try:
        nac_p = mps.decoder.adsb.nac_p(hex_value)
        flight_callsign = mps.adsb.callsign(hex_value)
        print(f"Flight {flight_callsign} \nHas NACp value: {nac_p}")
        if nac_p[0] < 4:
            print(f"Flight {flight_callsign} Might be currently jammed \n NACp is: {nac_p[0]}")
    except RuntimeError:
        pass

if __name__ == "__main__":
    read_dump1090_raw()