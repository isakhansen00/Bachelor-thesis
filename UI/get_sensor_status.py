from azure.iot.hub import IoTHubRegistryManager

# Connection string for the IoT Hub service shared access policy
CONNECTION_STRING = "HostName=RaspberryPiHubGruppe24.azure-devices.net;SharedAccessKeyName=service;SharedAccessKey=5R/rIBxvhyOJVoJ+rg2xsklVz8GrZAvK0AIoTHUDvKQ="

# Asynchronous function to get the status of a device
async def get_sensor_status(device_id):
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

