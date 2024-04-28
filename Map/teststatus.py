import asyncio
from azure.iot.device.aio import IoTHubDeviceClient
from datetime import datetime

async def send_heartbeat(device_client, device_id):
    """
    Sends a heartbeat to update the device twin.
    """
    while True:
        last_reported_time = datetime.utcnow().isoformat() + 'Z'
        twin_patch = {
            "properties": {
                "reported": {
                    "last_reported_time_" + device_id: last_reported_time
                }
            }
        }
        await device_client.patch_twin_reported_properties(twin_patch)
        print(f"Heartbeat sent from {device_id}")
        await asyncio.sleep(10)  # Send heartbeat every 10 seconds

async def main(conn_str, device_id):
    """
    Main function to connect to IoT Hub and send heartbeat.
    """
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)
    await device_client.connect()  # Connect to IoT Hub
    
    try:
        # Start sending heartbeat
        asyncio.create_task(send_heartbeat(device_client, device_id))
        
        # Keep the main coroutine running
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        pass
    finally:
        await device_client.disconnect()  # Disconnect from IoT Hub

if __name__ == '__main__':
    # Replace the connection string with the respective Pi's connection string
    conn_str = "HostName=RaspberryPiHubGruppe24.azure-devices.net;DeviceId=RaspberryPiFauskeISE;SharedAccessKey=1q1iFmmcHsWgfhR7WaSKODew3PIHBjI/YAIoTDtYz1s="
    # Replace the device_id with the respective Pi's device ID
    device_id = "RaspberryPiFauskeISE"
    
    asyncio.run(main(conn_str, device_id))
