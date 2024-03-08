import subprocess
import pyModeS as mps
import threading
import json
from azure.iot.device import IoTHubDeviceClient, Message
import time

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
        # print("Received ADS-B signal:", hex_value)
        icao_address = mps.adsb.icao(hex_value)  # Extract ICAO address
        if icao_address is not None:
            hex_values_dict.setdefault(icao_address, []).append(hex_value)  # Accumulate hex values for the ICAO address
            process_hex_values(icao_address)  # Process newly appended hex values for the ICAO address

def process_hex_values(icao_address):
    hex_values = hex_values_dict.get(icao_address, [])
    # print(f"Processing hex values for ICAO address {icao_address}")
    last_processed_index = getattr(process_hex_values, f"last_index_{icao_address}", 0)
    new_hex_values = hex_values[last_processed_index:]
    
    flight_callsign = None
    nac_p = None
    msg_even = None
    msg_odd = None
    t_even = None
    t_odd = None
    type_code_msg0 = None
    
    for hex_value in new_hex_values:
        
        try:
            nac_p = mps.decoder.adsb.nac_p(hex_value)
            """
            if nac_p[0] < 10:
                print(f"Potential jamming detected. NACp is: {nac_p[0]}")
                """
        except RuntimeError:
            pass
        
        try:
            flight_callsign = mps.adsb.callsign(hex_value)
        except RuntimeError:
            pass

        type_code_msg0 = mps.typecode(hex_value)
        
        if type_code_msg0 in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22]:
            binary_msg = bin(int(hex_value, 16))[2:].zfill(112)  # Convert hex to binary
            if binary_msg[54] == '0':
                msg_even = hex_value
                t_even = int(time.time())
            elif binary_msg[54] == '1':
                msg_odd = hex_value
                t_odd = int(time.time())
                
        if flight_callsign and msg_even and msg_odd and t_even and t_odd:
            try:
                position = mps.adsb.position(msg_even, msg_odd, t_even, t_odd)
                if position:
                    longitude, latitude = position
                    # print(f"Longitude: {longitude}, Latitude: {latitude}")
                    print(f"Flight {flight_callsign} with icao {icao_address} has position: LO: {longitude}, LA: {latitude}")
                    # Save longitude and latitude to the database along with other information
                    msg_even = None
                    msg_odd = None
                    t_even = None
                    t_odd = None
            except RuntimeError:
                print("HEIA")
    """
    if flight_callsign and nac_p:
        print(f"Flight {flight_callsign} with icao {icao_address} has NACp value: {nac_p}")
        message_data = {
            "ICAO": icao_address,
            "Callsign": flight_callsign,
            "NACp": nac_p
        }
        message = json.dumps(message_data)
        print(f"Message: {message}")
        # Send message to Azure IoT Hub
        client.send_message(message)
        if nac_p[0] < 10:
            print(f"Potential jamming of flight {flight_callsign} detected. NACp is: {nac_p[0]}")
        setattr(process_hex_values, f"last_index_{icao_address}", len(hex_values))  # Update last processed index
    """
if __name__ == "__main__":
    dump_thread = threading.Thread(target=read_dump1090_raw)
    dump_thread.start()
    dump_thread.join()
