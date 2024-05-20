from flask import Flask, jsonify, render_template
import asyncio
from datetime import datetime, timedelta
from azure.iot.hub import IoTHubRegistryManager


# twin = {'additional_properties': {'modelId': ''}, 'device_id': 'RaspberryPiBodo', 'module_id': None, 'tags': None, 
        # 'properties': "<azure.iot.hub.protocol.models.twin_properties_py3.TwinProperties object at 0x000001AB0DC2B4D0>", 'etag': 'AAAAAAAAAAE=', 'version': '65, de(2024, 4, 27, 15, 12, 21, 214301, tzinfo=<isodate.tzinfo.Utc object at 0x000001AB0DB3D5D0>)', 'cloud_to_device_message_count': 0, 'authentication_type': 'sas', 'x509_thumbprint': <azure.iot.hub.protocol.models.x509_thumbprint_py3.X509Thumbprint object at 0x000001AB0DC2AD50>, 'capabilities': <azure.iot.hub.protocol.models.device_capabilities_py3.DeviceCapabilities object at 0x000001AB0DC2B9D0>, 'device_scope': None, 'parent_scopes': None}}

data = {'additional_properties': {'modelId': ''}, 'device_id': 'RaspberryPiFauskeISE', 'module_id': None, 'tags': None, 'properties': "", 'etag': 'AAAAAAAAAAE=', 'version': 564, 'device_etag': 'NTkyNjI5ODM5', 'status': 'enabled', 'status_reason': None, 'status_update_time': "datetime.datetime(1, 1, 1, 0, 0, tzinfo=<isodate.tzinfo.Utc object at 0x000001AB0DB3D5D0>)", 'connection_state': 'Connected', 
        'last_activity_time':" datetime.datetime(2024, 4, 27, 15, 12, 18, 700540, tzinfo=<isodate.tzinfo.Utc object at 0x000001AB0DB3D5D0>)", 'cloud_to_device_message_count': 0, 'authentication_type': 'sas', 
        'x509_thumbprint': "<azure.iot.hub.protocol.models.x509_thumbprint_py3.X509Thumbprint object at 0x000001AB0DC60CD0>", 'capabilities': "<azure.iot.hub.protocol.models.device_capabilities_py3.DeviceCapabilities object at 0x000001AB0DC60F10>", 'device_scope': None, 'parent_scopes': None}

connection_state = data['connection_state']
print(connection_state)
