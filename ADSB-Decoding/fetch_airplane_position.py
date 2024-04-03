import requests

# Fetches airplane data from a specified URL and parses it into a dictionary 
# where each entry represents an airplane identified by its hex value, 
# with corresponding latitude and longitude coordinates.
# Returns:
#   - If successful, returns a dictionary containing flight positions data.
#   - If unsuccessful, returns an error message indicating the failure reason.
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

                flight_positions[hex_value] = [(lat, lon)]
                
            return flight_positions
        else:
            return f"Failed to fetch data: {response.status_code}"
    except Exception as e:
        f"An error occurred while fetching data: {e}"