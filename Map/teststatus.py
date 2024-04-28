import asyncio
from azure.iot.device.aio import IoTHubDeviceClient
from datetime import datetime

"""
Sends a heartbeat to update the device twin.

Args:
    device_client (IoTHubDeviceClient): The IoT Hub device client.
    device_id (str): The ID of the device.
"""
async def send_heartbeat(device_client, device_id):
    while True:
        # Get the current time in ISO 8601 format
        last_reported_time = datetime.utcnow().isoformat() + 'Z'
        # Create a twin patch to update the device twin with the current time
        twin_patch = {
            "properties": {
                "reported": {
                    "last_reported_time_" + device_id: last_reported_time
                }
            }
        }
        # Send the twin patch to update the device twin
        await device_client.patch_twin_reported_properties(twin_patch)
        print(f"Heartbeat sent from {device_id}")
        await asyncio.sleep(10)  # Send heartbeat every 10 seconds

"""
Main function to connect to IoT Hub and send heartbeat.

Args:
    conn_str (str): The connection string for the IoT Hub.
    device_id (str): The ID of the device.
"""
async def main(conn_str, device_id):
    # Create an IoT Hub device client from the connection string
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)
    # Connect to the IoT Hub
    await device_client.connect()
    
    try:
        # Start sending heartbeat in a background task
        asyncio.create_task(send_heartbeat(device_client, device_id))
        
        # Keep the main coroutine running
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        pass
    finally:
        # Disconnect from the IoT Hub when the program terminates
        await device_client.disconnect()

if __name__ == '__main__':
    # Replace the connection string with the respective Pi's connection string
    conn_str = "HostName=RaspberryPiHubGruppe24.azure-devices.net;DeviceId=RaspberryPiFauskeISE;SharedAccessKey=1q1iFmmcHsWgfhR7WaSKODew3PIHBjI/YAIoTDtYz1s="
    # Insert the device ID (e.g., RaspberryPiMorkved, RaspberryPiFauskeISE, RaspberryPiBodo
    device_id = "RaspberryPiFauskeISE"
    
    asyncio.run(main(conn_str, device_id))
