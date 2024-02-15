import subprocess

def read_dump1090_raw():
    # Run the dump1090 command and capture its output
    process = subprocess.Popen(['/home/admin/dump1090', '--raw'], stdout=subprocess.PIPE, universal_newlines=True)
    
    # Read output line by line
    for line in process.stdout:
        # Process each line as needed
        hex_value = line.strip()  # Assuming each line contains one hexadecimal value
        process_hex_value(hex_value)

def process_hex_value(hex_value):
    # Process each hexadecimal value here
    print("Received ADS-B signal:", hex_value)

if __name__ == "__main__":
    read_dump1090_raw()