from flask import Flask, jsonify, render_template
from azure.iot.hub import IoTHubRegistryManager
import asyncio

# Create a Flask app instance
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

# Asynchronous function to get the status of a device
async def get_device_status(device_id):
    try:
        # Create an instance of the IoTHubRegistryManager
        registry_manager = IoTHubRegistryManager.from_connection_string(CONNECTION_STRING)
        
        # Get the device twin and convert it to a dictionary
        twin = (registry_manager.get_twin(device_id)).as_dict()
        
        # Extract connection state from twin
        return twin['connection_state']
    
    except Exception as e:
        # If an exception occurs, return "Disconnected" status
        return "Disconnected"

# Route to retrieve the status of all devices
@app.route('/status_values')
async def status():
    sensor_status = {}  # Dictionary to hold device statuses

    # Create a list of asynchronous tasks to retrieve the status of each device
    tasks = [get_device_status(device_id) for device_id in devices.keys()]
    
    # Gather the results of asynchronous tasks
    results = await asyncio.gather(*tasks)
    
    # Update the sensor_status dictionary with device statuses
    sensor_status.update(zip(devices.keys(), results))
    
    # Return the device statuses as JSON
    return jsonify(sensor_status)

@app.route('/status')
def index():
    return render_template('status.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

