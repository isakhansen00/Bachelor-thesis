import asyncio
from azure.iot.device.aio import IoTHubDeviceClient

async def update_device_twin(status, device_client):
    twin_patch = {
        "properties": {
            "reported": {
                "status": status
            }
        }
    }
    await device_client.patch_twin_reported_properties(twin_patch)

async def main():
    conn_str = "HostName=RaspberryPiHubGruppe24.azure-devices.net;DeviceId=RaspberryPiFauskeISE;SharedAccessKey=1q1iFmmcHsWgfhR7WaSKODew3PIHBjI/YAIoTDtYz1s="
    
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)
    await device_client.connect()  # Connect to IoT Hub
    
    status = "Online"
    await update_device_twin(status, device_client)
    
    await device_client.disconnect()  # Disconnect from IoT Hub

if __name__ == '__main__':
    asyncio.run(main())
