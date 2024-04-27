import asyncio
from azure.iot.device.aio import IoTHubDeviceClient
from datetime import datetime

async def send_timestamp(device_client, conn_str):
    while True:
        try:
            current_time = datetime.utcnow().isoformat() + 'Z'
            twin_patch = {
                "properties": {
                    "reported": {
                        "last_reported_time": current_time
                    }
                }
            }
            await device_client.patch_twin_reported_properties(twin_patch)
            print("Timestamp sent:", current_time)
        except Exception as e:
            print("Error:", e)
        finally:
            await asyncio.sleep(10)  # Send timestamp every 10 seconds

async def main(conn_str):
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)
    await device_client.connect()  # Connect to IoT Hub
    
    try:
        # Start sending timestamp
        await send_timestamp(device_client, conn_str)
        
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        pass
    finally:
        await device_client.disconnect()  # Disconnect from IoT Hub

if __name__ == '__main__':
    # Replace conn_str with the appropriate connection string for each Raspberry Pi
    conn_str = "HostName=RaspberryPiHubGruppe24.azure-devices.net;DeviceId=RaspberryPiFauskeISE;SharedAccessKey=1q1iFmmcHsWgfhR7WaSKODew3PIHBjI/YAIoTDtYz1s="
    asyncio.run(main(conn_str))
