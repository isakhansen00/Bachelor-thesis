import subprocess
from azure.iot.device import IoTHubDeviceClient
import pyModeS as mps
import time
import json
import os

# Read device identifier from environment variable
DEVICE_ID = os.getenv("DEVICE_ID")

#CONNECTION_STRING = f"HostName=RaspberryPiSDRHub.azure-devices.net;DeviceId={DEVICE_ID};SharedAccessKey=Z3FE1PNea9Oz/xo8ofj4vMRpMDlwJCUmJAIoTN1a+QY="
CONNECTION_STRING = os.getenv("CONNECTION_STRING")
print(CONNECTION_STRING)
client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)

def process_signal(hex_value, timestamp):
    icao_address = mps.adsb.icao(hex_value)
    if icao_address is not None:
        #print(f"Received ADS-B signal: {hex_value}, ICAO address: {icao_address}")
        send_to_iot_hub(hex_value, icao_address, timestamp)


def send_to_iot_hub(hex_value, icao_address, timestamp):
    message_data = {
        "hex_value": hex_value,
        "icao_address": icao_address,
        "hex_timestamp": timestamp,
        "device_id": DEVICE_ID  # Include device identifier in the message
    }
    message = json.dumps(message_data)
    #print(f"Sending message to Azure IoT Hub: {hex_value}, {timestamp}")
    client.send_message(message)

def read_dump1090_raw():
    process = subprocess.Popen(['/home/admin/dump1090/./dump1090', '--raw'], stdout=subprocess.PIPE, universal_newlines=True)
    
    last_line = None  # Variable to store the last line read
    
    try:
        while True:
            line = process.stdout.readline().strip()
            if line:
                last_line = line
                
    except KeyboardInterrupt:
        # Handle Ctrl+C to exit gracefully
        pass
    
    # Process the last line
    if last_line:
        timestamp = time.time_ns()
        hex_value = last_line.replace("*", "").replace(";", "")
        print(hex_value)
        process_signal(hex_value, timestamp)

if __name__ == "__main__":
    read_dump1090_raw()