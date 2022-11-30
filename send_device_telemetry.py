import os
import glob
import asyncio
import uuid
import time
import sys
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message
import json

 
# Device variables
#os.system('modprobe w1-gpio')
#os.system('modprobe w1-therm')
device_id = "aquasensor01"
#conn_str = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")
conn_str = "HostName=aquanet.azure-devices.net;DeviceId=aquasensor01;SharedAccessKey={SASKeyHere}"
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

# IoT Hub variables
message_quota = 200
message_throughput = 60 #seconds


def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines
 
def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_f


async def send_recurring_telemetry(device_client):
    # Connect the client.
    await device_client.connect()

    # Send recurring telemetry
    i = 0
    while i < message_quota:
        i += 1
        body = json.dumps({"temperature_f": read_temp()})
        msg = Message(body)
        msg.message_id = uuid.uuid4()
        #msg.correlation_id = "correlation-1234"
        #msg.custom_properties["tornado-warning"] = "yes"
        msg.content_encoding = "utf-8"
        msg.content_type = "application/json"
        print("Sending message #" + str(i))
        print(msg)
        await device_client.send_message(msg)
        print("Done sending message #" + str(i))
        time.sleep(message_throughput)

    print("Message quota reached. Streaming complete for " + device_id)


def main():
    # Create instance of the device client using the connection string
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)

    print("Streaming started for " + device_id)
    print("Press Ctrl+C to exit")
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(send_recurring_telemetry(device_client))
    except KeyboardInterrupt:
        print("User initiated exit")
    except Exception:
        print("Unexpected exception!")
        raise
    finally:
        loop.run_until_complete(device_client.shutdown())
        loop.close()


if __name__ == "__main__":
    main()
