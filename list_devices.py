"""List every device on your Nest Device Access project, with its ID.

Run this after nest_setup.py has written NEST_PROJECT_ID / NEST_CLIENT_ID /
NEST_CLIENT_SECRET / NEST_REFRESH_TOKEN into .env:

    python3 list_devices.py

Copy the device_id of your thermostat into NEST_DEVICE_ID in .env.
"""

from dotenv import load_dotenv

from nest import NestThermostat

load_dotenv()

for d in NestThermostat().list_devices():
    print(f"device_id:    {d.device_id}")
    print(f"room:         {d.room_name or '(not set)'}")
    print(f"display name: {d.display_name or '(not set)'}")
    print("-" * 40)
