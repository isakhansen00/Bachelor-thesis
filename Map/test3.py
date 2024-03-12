import subprocess
import pyModeS as mps
import threading
import json
from azure.iot.device import IoTHubDeviceClient, Message
import time
from geopy.distance import great_circle

hex_values_dict = {}
planes_dict = {}

def extract_lat_lon_from_adsb(adsb_message):
    # Extract relevant bits from the ADS-B message
    cpr_format = int(adsb_message[0:2], 16)  # CPR format (odd or even)
    cpr_latitude = int(adsb_message[2:20], 2)  # CPR latitude in CPR format
    cpr_longitude = int(adsb_message[20:38], 2)  # CPR longitude in CPR format
    
    # Decode CPR coordinates
    even_cpr_latitude = cpr_latitude / (2**17)
    odd_cpr_latitude = cpr_latitude / (2**17) + 1 / 131072
    
    even_cpr_longitude = cpr_longitude / (2**17)
    odd_cpr_longitude = cpr_longitude / (2**17) + 1 / 131072
    
    # Determine if the position is even or odd
    if cpr_format == 0:
        latitude = even_cpr_latitude
        longitude = even_cpr_longitude
    else:
        latitude = odd_cpr_latitude
        longitude = odd_cpr_longitude
    
    return latitude, longitude

def read_dump1090_raw():

    process = subprocess.Popen(['/home/admin/dump1090/./dump1090', '--interactive'], stdout=subprocess.PIPE, universal_newlines=True)

    for line in process.stdout:
        if line.startswith("MSG,"):
            fields = line.split(",")  # Split the line by comma
            msg_type = fields[1]       # Message type
            if msg_type in ["3", "4", "5", "6", "7", "8", "9"]:  # ADS-B messages
                adsb_message = fields[5]  # ADS-B message is at index 5
                latitude, longitude = extract_lat_lon_from_adsb(adsb_message)
                print("Latitude:", latitude, "Longitude:", longitude)

if __name__ == "__main__":
    dump_thread = threading.Thread(target=read_dump1090_raw)
    dump_thread.start()
    dump_thread.join()
