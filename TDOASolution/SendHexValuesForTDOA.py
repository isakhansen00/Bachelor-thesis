# import asyncio
# import json
# import os
# import pyModeS as mps
# import subprocess
# import time
# from azure.iot.device import IoTHubDeviceClient

# hex_values_dict = {}

# # Read device identifier and connection string from environment variables
# DEVICE_ID = os.getenv("DEVICE_ID")
# CONNECTION_STRING = os.getenv("CONNECTION_STRING")

# client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)

# async def read_dump1090_raw():
#     process = await asyncio.create_subprocess_exec(
#         '/home/admin/dump1090/./dump1090', '--raw',
#         stdout=subprocess.PIPE, stderr=subprocess.PIPE
#     )
#     while True:
#         line = await process.stdout.readline()
#         if not line:
#             break
#         await process_line(line.decode().strip())

# async def process_line(line):
#     timestamp = time.time_ns()
#     hex_value = line.replace("*", "").replace(";", "")
#     icao_address = mps.adsb.icao(hex_value)
#     if icao_address is not None:
#         hex_values_dict.setdefault(icao_address, []).append(hex_value)
#         await process_signal(icao_address, timestamp)

# async def process_signal(icao_address, timestamp):
#     hex_values = hex_values_dict.get(icao_address, [])
#     last_processed_index = getattr(process_signal, f"last_index_{icao_address}", 0)
#     new_hex_values = hex_values[last_processed_index:]

#     for hex_value in new_hex_values:
#         icao_address = mps.adsb.icao(hex_value)
#         if icao_address is not None:
#             try:

#                 await send_to_iot_hub(hex_value, icao_address, timestamp)
#             except:
#                 pass
#     setattr(process_signal, f"last_index_{icao_address}", len(hex_values))

# async def send_to_iot_hub(hex_value, icao_address, timestamp):
#     message_data = {
#         "hex_value": hex_value,
#         "icao_address": icao_address,
#         "hex_timestamp": timestamp,
#         "device_id": DEVICE_ID
#     }
#     message = json.dumps(message_data)
#     print(f"Sending message to Azure IoT Hub: {hex_value}, {timestamp}")
#     try:
#         await client.send_message(message)
#     except Exception as e:
#         print(f"Error sending message: {e}")

# async def main():
#     await read_dump1090_raw()

# if __name__ == "__main__":
#     asyncio.run(main())



import subprocess
from azure.iot.device import IoTHubDeviceClient
import pyModeS as mps
import time
import json
import os
import threading

hex_values_dict = {}

# Read device identifier from environment variable
DEVICE_ID = os.getenv("DEVICE_ID")

#CONNECTION_STRING = f"HostName=RaspberryPiSDRHub.azure-devices.net;DeviceId={DEVICE_ID};SharedAccessKey=Z3FE1PNea9Oz/xo8ofj4vMRpMDlwJCUmJAIoTN1a+QY="
CONNECTION_STRING = os.getenv("CONNECTION_STRING")
print(CONNECTION_STRING)
client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)

def read_dump1090_raw():
    process = subprocess.Popen(['/home/admin/dump1090/./dump1090', '--raw'], stdout=subprocess.PIPE, universal_newlines=True)
    
    for line in process.stdout: 
        timestamp = time.time_ns()
        hex_value = line.strip()
        hex_value = hex_value.replace("*", "")
        hex_value = hex_value.replace(";", "")
        icao_address = mps.adsb.icao(hex_value)
        if icao_address is not None:
            hex_values_dict.setdefault(icao_address, []).append(hex_value)   
            print(hex_value)
            process_signal(icao_address, timestamp)
            timestamp2 = time.time_ns()
            print((timestamp2-timestamp)/1e9)

def process_signal(icao_address, timestamp):
    hex_values = hex_values_dict.get(icao_address, [])
    last_processed_index = getattr(process_signal, f"last_index_{icao_address}", 0)
    new_hex_values = hex_values[last_processed_index:]

    for hex_value in new_hex_values:

        icao_address = mps.adsb.icao(hex_value)
        if icao_address is not None:
            pass
            #print(f"Received ADS-B signal: {hex_value}, ICAO address: {icao_address}")
            #send_to_iot_hub(hex_value, icao_address, timestamp)
    setattr(process_signal, f"last_index_{icao_address}", len(hex_values))


def send_to_iot_hub(hex_value, icao_address, timestamp):
    message_data = {
        "hex_value": hex_value,
        "icao_address": icao_address,
        "hex_timestamp": timestamp,
        "device_id": DEVICE_ID  # Include device identifier in the message
    }
    message = json.dumps(message_data)
    print(f"Sending message to Azure IoT Hub: {hex_value}, {timestamp}")
    client.send_message(message)



if __name__ == "__main__":
    dump_thread = threading.Thread(target=read_dump1090_raw)
    dump_thread.start()
    dump_thread.join()