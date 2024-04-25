import asyncio
from azure.iot.device.aio import IoTHubDeviceClient
import time

async def update_device_twin(status, device_client):
    twin_patch = {
        "properties": {
            "reported": {
                "status": status
            }
        }
    }
    await device_client.patch_twin_reported_properties(twin_patch)

async def send_heartbeat(device_client):
    while True:
        status = "Online"
        await update_device_twin(status, device_client)
        print("Heartbeat sent")
        await asyncio.sleep(10)  # Send heartbeat every 10 seconds

async def main():
    conn_str = "HostName=RaspberryPiHubGruppe24.azure-devices.net;DeviceId=RaspberryPiFauskeISE;SharedAccessKey=1q1iFmmcHsWgfhR7WaSKODew3PIHBjI/YAIoTDtYz1s="
    
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)
    await device_client.connect()  # Connect to IoT Hub
    
    try:
        # Start sending heartbeat
        asyncio.create_task(send_heartbeat(device_client))
        
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        pass
    finally:
        await device_client.disconnect()  # Disconnect from IoT Hub

if __name__ == '__main__':
    asyncio.run(main())
