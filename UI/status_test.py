from azure.iot.device.aio import IoTHubDeviceClient
from flask import Flask, jsonify, render_template
import asyncio
from datetime import datetime, timedelta

app = Flask(__name__)

# Dictionary to hold device information
devices = {
    "RaspberryPiMorkved": {
        "connection_string": "HostName=RaspberryPiHubGruppe24.azure-devices.net;DeviceId=RaspberryPiMorkved;SharedAccessKey=xlXcAKxRMl5zAQRp58IQlSwPY9f1qFIovAIoTAT3hP0="
    },
    "RaspberryPiFauskeISE": {
        "connection_string": "HostName=RaspberryPiHubGruppe24.azure-devices.net;DeviceId=RaspberryPiFauskeISE;SharedAccessKey=1q1iFmmcHsWgfhR7WaSKODew3PIHBjI/YAIoTDtYz1s="
    },
    "RaspberryPiBodo": {
        "connection_string": "HostName=RaspberryPiHubGruppe24.azure-devices.net;DeviceId=RaspberryPiBodo;SharedAccessKey=iZVIbvZjXqyrVhD18veLT363Fgp5luN5OAIoTPV3kls="
    }
}

"""
Function to get the status of a device (online or offline)
"""
async def get_device_status(device_client, device_id):
    try:
        # Get device twin
        twin = await device_client.get_twin()
        # Extract last reported time from twin
        last_reported_time_str = twin['reported']['properties']['reported']['last_reported_time_' + device_id]
        last_reported_time = datetime.strptime(last_reported_time_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        # Check if the device hasn't reported for more than 15 seconds
        if datetime.utcnow() - last_reported_time > timedelta(seconds=15):
            return "Offline"
        return "Online"
    # If an exception occurs, consider device as offline
    except Exception as e:
        return "Offline"

@app.route('/status')
async def status():

    sensor_status = {}  # Dictionary to hold device statuses
    device_clients = []  # List to hold device clients
    tasks = []  # List to hold tasks
    
    # Loop through each device and create a client for it
    for device_id, device_info in devices.items():
        device_client = IoTHubDeviceClient.create_from_connection_string(device_info["connection_string"])
        device_clients.append(device_client)
        await device_client.connect()
        tasks.append(get_device_status(device_client, device_id))
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)
    
    # Populate sensor_status dictionary with device statuses
    for device_id, status in zip(devices.keys(), results):
        sensor_status[device_id] = status
    
    # Disconnect all device clients
    for device_client in device_clients:
         await device_client.disconnect()
    
    # Return device statuses as JSON
    return jsonify(sensor_status)

@app.route('/')
def index():
    return render_template('status.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
