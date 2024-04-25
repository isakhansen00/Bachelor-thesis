import asyncio
from azure.iot.device.aio import IoTHubDeviceClient

async def update_device_twin(status, conn_str):
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)
    twin_patch = {
        "properties": {
            "reported": {
                "status": status
            }
        }
    }
    await device_client.patch_twin_reported_properties(twin_patch)

async def main():
    conn_str = "Your IoT Hub Device Connection String"
    status = "Online"
    await update_device_twin(status, conn_str)

if __name__ == '__main__':
    asyncio.run(main())