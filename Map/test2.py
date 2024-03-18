import subprocess
import pyModeS as mps
import threading
import time

# Position antenna: LO:67.28299 LA: 14.38518

flight_positions = {}  # Dictionary to store latest position for each flight

def read_dump1090_raw():
    process = subprocess.Popen(['/home/admin/dump1090/./dump1090', '--raw'], stdout=subprocess.PIPE, universal_newlines=True)
    
    for line in process.stdout:
        hex_value = line.strip().replace("*", "").replace(";", "")
        time.sleep(0.5)
        icao_address = mps.adsb.icao(hex_value)  # Extract ICAO address
        if icao_address is not None:
            process_hex_values(icao_address, hex_value)  # Process the hex value for the ICAO address

def process_hex_values(icao_address, hex_value):
    flight_callsign = None
    
    try:
        flight_callsign = mps.adsb.callsign(hex_value)
    except RuntimeError:
        pass

    if flight_callsign:
        if icao_address not in flight_positions:
            # If this is the first position message for this aircraft, use the reference location
            lat_ref, lon_ref = 14.38518, 67.28299  # Ground station reference location
        else:
            # Otherwise, use the latest known position as reference
            lat_ref, lon_ref = flight_positions[icao_address]

        try:
            position = mps.adsb.airborne_position_with_ref(hex_value, lat_ref, lon_ref)
            if position:
                latitude, longitude = position
                flight_positions[icao_address] = (latitude, longitude)  # Update latest position
                print(f"Flight {flight_callsign} with ICAO {icao_address} has position: LO: {longitude}, LA: {latitude}")
                # Save longitude and latitude to the database along with other information
        except RuntimeError:
            pass

if __name__ == "__main__":
    dump_thread = threading.Thread(target=read_dump1090_raw)
    dump_thread.start()
    # Remove the join() call to allow the main thread to continue running
    # dump_thread.join()
