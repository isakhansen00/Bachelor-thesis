import subprocess
import pyModeS as mps
import threading
import json
from azure.iot.device import IoTHubDeviceClient, Message

hex_values_dict = {}
CONNECTION_STRING = "HostName=RaspberryPiSDRHub.azure-devices.net;DeviceId=RaspberryPi;SharedAccessKey=Z3FE1PNea9Oz/xo8ofj4vMRpMDlwJCUmJAIoTN1a+QY="
MSG_SND = ''
client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)  

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
                
                # Check message types
                if mps.adsb.message_type(msg0) == 9 and mps.adsb.message_type(msg1) == 9:
                    position = mps.decoder.adsb.position(msg0, msg1, 0, 0)  # Assuming timestamps are not used here
                    if position is not None:
                        latitude, longitude = position
                        print("Latitude:", latitude)
                        print("Longitude:", longitude)
                else:
                    print("Invalid message types for position decoding")
    
    print(hex_values_dict)

if __name__ == "__main__":
    dump_thread = threading.Thread(target=read_dump1090_raw)
    dump_thread.start()
    dump_thread.join()

