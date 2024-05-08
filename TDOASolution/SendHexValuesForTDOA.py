
import subprocess
from azure.iot.device import IoTHubDeviceClient
import pyModeS as mps
import time
import json
import os
import threading
import fetch_airplane_data

hex_values_dict = {}

# Read device identifier from environment variable
DEVICE_ID = os.getenv("DEVICE_ID")

#CONNECTION_STRING = f"HostName=RaspberryPiSDRHub.azure-devices.net;DeviceId={DEVICE_ID};SharedAccessKey=Z3FE1PNea9Oz/xo8ofj4vMRpMDlwJCUmJAIoTN1a+QY="
CONNECTION_STRING = os.getenv("CONNECTION_STRING")
print(CONNECTION_STRING)
client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)

def read_dump1090_raw():
    process = subprocess.Popen(['/home/admin/dump1090/./dump1090', '--raw', '--net'], stdout=subprocess.PIPE, universal_newlines=True)
    
    for line in process.stdout: 
        timestamp = time.time_ns()
        hex_value = line.strip()
        hex_value = hex_value.replace("*", "")
        hex_value = hex_value.replace(";", "")
        icao_address = mps.adsb.icao(hex_value)
        if icao_address is not None:
            
            timestamp2 = time.time_ns()
            print((timestamp2-timestamp)/1e9)
        send_to_iot_hub(hex_value, timestamp)


def send_to_iot_hub(hex_value, timestamp):
    print("test")
    message_data = {
        "hex_value": hex_value,
        "icao_address": 123,
        "hex_timestamp": timestamp,
        "device_id": DEVICE_ID  # Include device identifier in the message
    }
    message = json.dumps(message_data)
    print(f"Sending message to Azure IoT Hub: {hex_value}, {timestamp}")
    client.send_message(message)



if __name__ == "__main__":
    dump_thread = threading.Thread(target=read_dump1090_raw)
    dump_thread.start()
    #dump_thread.join()



    # Continuously fetches airplane data every 15 seconds using the fetch_airplane_data() function.
    # For each retrieved aircraft position, it constructs a message containing the ICAO address, latitude, 
    # longitude and a timestamp, converts it to JSON format, and sends it to Azure IoT Hub using an Azure IoT Hub client.
    while True:
        time.sleep(5)
        flight_positions = fetch_airplane_data()  # Call the function to fetch airplane data
        print(flight_positions)
        for icao_address, positions in flight_positions.items():
        # Extract ICAO address from the dictionary
            icao = icao_address

            # Iterate over positions for each ICAO address
            for position in positions:
                # Extract latitude and longitude
                latitude, longitude = position
                positiontimestamp = time.time()

                # Create message data
                message_data = {
                    "Type": "FlightPosition",
                    "Icao": icao,
                    "Longitude": longitude,
                    "Latitude": latitude,
                    "PositionTimestamp": positiontimestamp
                }

                # Convert message data to JSON
                message = json.dumps(message_data)

                # Send message to Azure IoT Hub
                client.send_message(message)

                # Print sent message for debugging (optional)
                print(f"Message sent: {message}")
        time.sleep(10)  # Sleep for 10 seconds before fetching again