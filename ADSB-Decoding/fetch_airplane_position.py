import requests

def fetch_airplane_data():
    flight_positions = {}
    try:
        response = requests.get("http://localhost:8080/data.json")
        if response.status_code == 200:
            data = response.json()
            for airplane in data:
                hex_value = airplane["hex"]
                lat = airplane["lat"]
                lon = airplane["lon"]

                # If ICAO address already exists in dictionary, append new coordinates if they are unique
                if hex_value in flight_positions:
                    if (lat, lon) not in flight_positions[hex_value]:
                        flight_positions[hex_value].append((lat, lon))
                else:
                    flight_positions[hex_value] = [(lat, lon)]
                
            return flight_positions
        else:
            return f"Failed to fetch data: {response.status_code}"
    except Exception as e:
        f"An error occurred while fetching data: {e}"