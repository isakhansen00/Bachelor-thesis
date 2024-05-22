import time
from azure.iot.device import IoTHubDeviceClient, Message

pin = 4
CONNECTION_STRING = "HostName=RaspberryPiSDRHub.azure-devices.net;DeviceId=RaspberryPi;SharedAccessKey=Z3FE1PNea9Oz/xo8ofj4vMRpMDlwJCUmJAIoTN1a+QY="
MSG_SND = '{{"temperature": {temperature},"humidity": {humidity}}}'

def iothub_client_init():  
    client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)  
    return client  

def iothub_client_telemetry_sample_run():  
    try:  
        client = iothub_client_init()  
        print("Sending data to IoT Hub, press Ctrl-C to exit")

        while True:  
            msg_txt_formatted = MSG_SND.format(temperature=81, humidity=27)  
            message = Message(msg_txt_formatted)  
            print("Sending message: {}".format(message))  
            client.send_message(message)  
            print("Message successfully sent")  
            time.sleep(3)
    except KeyboardInterrupt:  
        print("IoTHubClient stopped")

if __name__ == '__main__':  
    print("Press Ctrl-C to exit")  
    iothub_client_telemetry_sample_run()