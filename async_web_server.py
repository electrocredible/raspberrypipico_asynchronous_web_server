# Full guide at: electrocredible.com, Langugage: MicroPython

# Import necessary libraries
import network  # Library for network communication
import socket   # Library for socket programming
import time     # Library for time-related functions

from machine import Pin, ADC 
import uasyncio as asyncio     # Asynchronous I/O library

# Initializing onboard LED and temperature sensor
onboard_led = Pin("LED", Pin.OUT, value=0)  # GPIO pin for onboard LED
temperature_sensor = ADC(4)                 # GPIO 4 - connected to the temperature sensor

# Wi-Fi credentials
ssid = 'YOUR_SSID'   # SSID of the Wi-Fi network
password = 'YOUR_PASSWORD'  # Password of the Wi-Fi network

# HTML + CSS for webpage
html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Raspberry Pi Pico Web Server</title>
  <style>
    html {
      font-family: Arial;
      display: inline-block;
      margin: 0px auto;
      text-align: center;
    }
    h1 {
      font-family: Arial;
      color: #2551cc;
    }
    .button1,
    .button2 {
      border: none;
      color: white;
      padding: 15px 32px;
      text-align: center;
      text-decoration: none;
      display: inline-block;
      font-size: 16px;
      margin: 4px 2px;
      cursor: pointer;
      border-radius: 10px;
    }
    .button1 {
      background: #339966;
    }
    .button2 {
      background: #993300;
    }
  </style>
</head>
<body>
  <h1>Raspberry Pi Pico Web Server</h1>
  <p>%s</p>
  <p>
    <a href="/led/on"><button class="button1">LED On</button></a>
  </p>
  <p>
    <a href="/led/off"><button class="button2">LED Off</button></a>
  </p>
  <p>Temperature: %s°C (%s°F)</p>
</body>
</html>
"""

# Initialize station interface
wlan = network.WLAN(network.STA_IF)

# Function to connect to Wi-Fi network
def connect_to_network():
    wlan.active(True)            # Activate the WLAN interface
    wlan.config(pm=0xa11140)     # Disable power-save mode
    wlan.connect(ssid, password) # Connect to the Wi-Fi network

    max_wait = 10                # Maximum wait time for connection (seconds)
    while max_wait > 0 and not wlan.isconnected():
        max_wait -= 1           # Decrement wait time
        print('waiting for connection...')
        time.sleep(1)           # Wait for 1 second       

    if not wlan.isconnected():
        print('Network Connection has failed')  # Print failure message if connection fails
    else:
        print('Connected to the network successfully.')  # Print success message if connection successful
        status = wlan.ifconfig()  # Get network interface configuration
        print('Enter this address in browser-> ' + status[0])  # Print IP address for accessing the web server

# Asynchronous function to handle client requests
async def serve_client(reader, writer):
    print("Client connected")  # Print message when client is connected
    request_line = await reader.readline()  # Read the HTTP request line
    print("Request:", request_line)         # Print the received request
    # Skip HTTP request headers
    while await reader.readline() != b"\r\n":
        pass

    request = str(request_line)        # Convert request to string
    led_on = request.find('/led/on')   # Check if LED ON request is received
    led_off = request.find('/led/off')  # Check if LED OFF request is received
    print('LED on =', led_on)           # Print LED ON request status
    print('LED off =', led_off)         # Print LED OFF request status

    state_message = ""  # Initialize state message
    if led_on == 6:
        print("LED on")          # Print LED ON message
        onboard_led.value(1)     # Turn LED on
        state_message = "LED Turned On"  # Update state message
    elif led_off == 6:
        print("LED off")         # Print LED OFF message
        onboard_led.value(0)     # Turn LED off
        state_message = "LED Turned Off"  # Update state message

    temperature_celsius = await read_temperature()  # Read temperature in Celsius
    temperature_fahrenheit = convert_to_fahrenheit(temperature_celsius)  # Convert to Fahrenheit

    # Generate HTML response with current state and temperature
    response = html % (state_message, "{:.2f}".format(temperature_celsius), "{:.2f}".format(temperature_fahrenheit))
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')  # Write HTTP response header
    writer.write(response)  # Write HTML response

    await writer.drain()     # Drain the writer buffer
    await writer.wait_closed()  # Wait until writer is closed
    print("Client disconnected")  # Print message when client is disconnected

# Asynchronous function to read temperature
async def read_temperature():
    temperature_reading = temperature_sensor.read_u16() * 3.3 / (65535)  # Convert ADC reading to voltage
    temperature_celsius = 27 - (temperature_reading - 0.706) / 0.001721  # Convert voltage to temperature
    return temperature_celsius  # Return temperature in Celsius

# Function to convert Celsius to Fahrenheit
def convert_to_fahrenheit(celsius):
    return celsius * 9/5 + 32  # Convert Celsius to Fahrenheit

# Asynchronous main function
async def main():
    print('Connecting to Network...')
    while not wlan.isconnected():  # Continue trying to connect until connected
        connect_to_network()       
    print('Setting up webserver...') 
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))  # Start the web server
    
    while True:  # Loop to continuously check Wi-Fi connection
        if not wlan.isconnected():  # If not connected to Wi-Fi
            wlan.disconnect()       # Disconnect from current Wi-Fi network
            connect_to_network()    # Reconnect to Wi-Fi network
        await asyncio.sleep(0.1)   # Sleep for 0.1 seconds

try:
    asyncio.run(main())  # Run the main asynchronous function
finally:
    asyncio.new_event_loop() #Create a new event loop
