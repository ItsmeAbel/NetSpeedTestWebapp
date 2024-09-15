import speedtest
import matplotlib.pyplot as plt
import subprocess
import time
import os
import numpy as np
from flask import Flask, jsonify, render_template

app = Flask(__name__)
interval = 5
lat_pre = 0
lat_dur = 0
lat_aft = 0

def measure_network():
    """Measure download and upload speeds using speedtest-cli."""
    try:
        st = speedtest.Speedtest()
        st.get_best_server()  # Automatically pick the best server
        download_speed = st.download() / 1_000_000  # Convert from bps to Mbps
        upload_speed = st.upload() / 1_000_000      # Convert from bps to Mbps
        return {
            'download_speed': download_speed,
            'upload_speed': upload_speed
        }
    except Exception as e:
        print(f"Error during speed test: {e}")
        return None, None

def ping_latency(host='8.8.8.8', count=1):
    """Attempt to ping and return latency or None if ping fails."""
    try:
        # Determine the correct ping command for the OS
        ping_command = ['ping', '-c', str(count), host] if os.name != 'nt' else ['ping', '-n', str(count), host]
        
        print(f"Running command: {' '.join(ping_command)}")
        
        # Execute the ping command
        result = subprocess.run(ping_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        
        # Debugging output
        print("Ping output:", output)
        
        if result.returncode != 0:
            print("Ping failed, return code:", result.returncode)
            return None
        
        # Parse the output to find the latency
        if 'time=' in output:
            latency_line = output.split('time=')[-1].strip()
            latency_value = latency_line.split('ms')[0].strip()  # Remove 'ms' and extra spaces
            latency = float(latency_value)  # Extract the time in ms
            return latency
        else:
            print("Ping failed to retrieve latency")
            return None
    except Exception as e:
        print(f"Ping command failed: {e}")
        return None

def lat_calc():
    lat_pre = ping_latency()

    # Measure download and upload speeds (this causes network load)
    measure_network()
    lat_dur = ping_latency()

    time.sleep(interval)
    lat_aft = ping_latency()

    bufferbloat = lat_dur - lat_pre

    if bufferbloat <= 5:
        Grade = 'S'
    elif bufferbloat <= 30:
        Grade = 'A'
    elif bufferbloat <= 60:
        Grade = 'B'
    elif bufferbloat <= 200:
        Grade = 'C'
    elif bufferbloat <= 400:
        Grade = 'D'
    elif bufferbloat > 400:
        Grade = 'F'

    return {
        'lat_pre': lat_pre,
        'lat_dur': lat_dur,
        'lat_aft': lat_aft,
        'Grade': Grade
    }

@app.route('/')
def home():
    return render_template('5test.html')

#measuring speed
@app.route('/network_test', methods=['GET'])
def network_test():
    print("measuring network...")
    result = measure_network()
    return jsonify(result)

#measuring latency
@app.route('/latency_test', methods =['GET'])
def latency_test():
    print("measuring latency...")
    ping = lat_calc()
    return jsonify(ping)

    

if __name__ == 'main':
    print("Starting the Flask server...")
    # Get the port from the environment variable or default to 5000
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)