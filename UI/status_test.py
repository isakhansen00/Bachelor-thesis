from flask import Flask, jsonify, render_template
import asyncio
from datetime import datetime, timedelta
from azure.iot.hub import IoTHubRegistryManager
import json
app = Flask(__name__)

# Dictionary to hold device information
devices = {
    "RaspberryPiMorkved": {
        "device_id": "RaspberryPiMorkved"
    },
    "RaspberryPiFauskeISE": {
        "device_id": "RaspberryPiFauskeISE"
    },
    "RaspberryPiBodo": {
        "device_id": "RaspberryPiBodo"
    }
}

# Connection string for the IoT Hub service shared access policy
CONNECTION_STRING = "HostName=RaspberryPiHubGruppe24.azure-devices.net;SharedAccessKeyName=service;SharedAccessKey=5R/rIBxvhyOJVoJ+rg2xsklVz8GrZAvK0AIoTHUDvKQ="

async def get_device_status(device_id):
    try:
        # Create an instance of the IoTHubRegistryManager
        registry_manager = IoTHubRegistryManager.from_connection_string(CONNECTION_STRING)
        
        # Get the device twin
        twin = (registry_manager.get_twin(device_id)).as_dict()
        #twin = jsonify(twin)
        print((twin['connection_state']))
        #print(twin)
        # Extract last reported time from twin
        #last_reported_time_str = twin['reported']['properties']['reported']['last_reported_time' + device_id]

        print(twin['connection_state'])
        # Check if the device hasn't reported for more than 15 seconds
        return twin['connection_state']
    
    except Exception as e:
        return f"Disconnected"

@app.route('/status')
async def status():
    sensor_status = {}  # Dictionary to hold device statuses
    tasks = []  # List to hold tasks
    
    for device_id, _ in devices.items():
        tasks.append(get_device_status(device_id))
    
    results = await asyncio.gather(*tasks)
    
    for device_id, status in zip(devices.keys(), results):
        sensor_status[device_id] = status
    
    return jsonify(sensor_status)

@app.route('/')
def index():
    return render_template('status.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)