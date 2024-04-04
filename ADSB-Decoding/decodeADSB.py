import time
import subprocess
import pyModeS as mps
import threading
import json
from azure.iot.device import IoTHubDeviceClient, Message
from fetch_airplane_position import fetch_airplane_data

hex_values_dict = {}

CONNECTION_STRING = "HostName=RaspberryPiSDRHub.azure-devices.net;DeviceId=RaspberryPi;SharedAccessKey=Z3FE1PNea9Oz/xo8ofj4vMRpMDlwJCUmJAIoTN1a+QY="
MSG_SND = ''
client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING) 
 
def read_dump1090_raw():
    process = subprocess.Popen(['/home/admin/dump1090/./dump1090', '--raw', '--net'], stdout=subprocess.PIPE, universal_newlines=True)
    
    for line in process.stdout:
        hex_value = line.strip()
        hex_value = hex_value.replace("*", "")
        hex_value = hex_value.replace(";", "")
        print("Received ADS-B signal:", hex_value)
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
        
        try:
            nac_p = mps.decoder.adsb.nac_p(hex_value)
            if nac_p[0] < 8:
                print(f"Potential jamming detected. NACp is: {nac_p[0]}")
        except RuntimeError:
            pass
        
        try:
            flight_callsign = mps.adsb.callsign(hex_value)
        except RuntimeError:
            pass


        # Continuously fetches airplane data every 5 seconds using the fetch_airplane_data() function.
        # For each retrieved aircraft position, it constructs a message containing the ICAO address, latitude, 
        # and longitude, converts it to JSON format, and sends it to Azure IoT Hub using an Azure IoT Hub client.
        # The process repeats every 15 seconds.
        time.sleep(1)
        flight_positions = fetch_airplane_data()  # Call the function to fetch airplane data
        print(flight_positions)
        for icao_address, positions in flight_positions.items():
        # Extract ICAO address from the dictionary
            icao = icao_address

            # Iterate over positions for each ICAO address
            for position in positions:
                # Extract latitude and longitude
                latitude, longitude = position

                # Create message data
                message_data = {
                    "Type": "FlightPosition",
                    "Icao": icao,
                    "Longitude": longitude,
                    "Latitude": latitude
                }

                # Convert message data to JSON
                message = json.dumps(message_data)

                # Send message to Azure IoT Hub
                client.send_message(message)

                    # Print sent message for debugging (optional)
                print(f"Message sent: {message}")
                time.sleep(0.5)  # Sleep for 10 seconds before fetching again
        
    if flight_callsign and nac_p:
        print(f"Flight {flight_callsign} with icao {icao_address} has NACp value: {nac_p}")
        message_data = {
            "Type": "FlightData",
            "ICAO": icao_address,
            "Callsign": flight_callsign,
            "NACp": nac_p[0]
        }
        message = json.dumps(message_data)
        print(f"Message: {message}")
        # Send message to Azure IoT Hub
        client.send_message(message)

        if nac_p[0] < 10:
            print(f"Potential jamming of flight {flight_callsign} detected. NACp is: {nac_p[0]}")
        setattr(process_hex_values, f"last_index_{icao_address}", len(hex_values))  # Update last processed index

if __name__ == "__main__":
    dump_thread = threading.Thread(target=read_dump1090_raw)
    dump_thread.start()
    #dump_thread.join()

    # Continuously fetches airplane data every 5 seconds using the fetch_airplane_data() function.
    # For each retrieved aircraft position, it constructs a message containing the ICAO address, latitude, 
    # and longitude, converts it to JSON format, and sends it to Azure IoT Hub using an Azure IoT Hub client.
    # The process repeats every 15 seconds.
    # while True:
    #     time.sleep(5)
    #     flight_positions = fetch_airplane_data()  # Call the function to fetch airplane data
    #     print(flight_positions)
    #     for icao_address, positions in flight_positions.items():
    #     # Extract ICAO address from the dictionary
    #         icao = icao_address

    #         # Iterate over positions for each ICAO address
    #         for position in positions:
    #             # Extract latitude and longitude
    #             latitude, longitude = position

    #             # Create message data
    #             message_data = {
    #                 "Type": "FlightPosition",
    #                 "Icao": icao,
    #                 "Longitude": longitude,
    #                 "Latitude": latitude
    #             }

    #             # Convert message data to JSON
    #             message = json.dumps(message_data)

    #             # Send message to Azure IoT Hub
    #             client.send_message(message)

    #             # Print sent message for debugging (optional)
    #             print(f"Message sent: {message}")
    #     time.sleep(10)  # Sleep for 10 seconds before fetching again
