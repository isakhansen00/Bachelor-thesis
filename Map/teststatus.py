import asyncio
from azure.iot.device.aio import IoTHubDeviceClient
import os

# Main function to connect to IoT Hub and send heartbeat messages.
# Args:
#     conn_str (str): The connection string for the IoT Hub.
#     device_id (str): The ID of the device.
async def main(conn_str, device_id):
    # Create an IoT Hub device client from the connection string
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)
    # Connect to the IoT Hub
    await device_client.connect()
    
    try:
        # Main loop to continuously send heartbeat messages
        while True:
            # Send a heartbeat message to indicate the connection status
            print(f"Heartbeat sent from {device_id}")
            # Wait for 10 seconds before sending the next heartbeat
            await asyncio.sleep(10)
    
    except KeyboardInterrupt:
        pass
    finally:
        # Disconnect from the IoT Hub when the program terminates
        await device_client.disconnect()

if __name__ == '__main__':
    # Retrieve the connection string and device ID from environment variables
    conn_str = str(os.getenv("CONNECTION_STRING"))
    device_id = str(os.getenv("DEVICE_ID"))
    
    # Run the main coroutine
    asyncio.run(main(conn_str, device_id))
