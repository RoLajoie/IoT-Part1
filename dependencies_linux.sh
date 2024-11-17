#!/bin/bash

# Update and upgrade system packages
sudo apt update && sudo apt upgrade -y

# Install Python 3 and pip
sudo apt install -y python3 python3-pip

# Install required Python libraries
pip3 install RPi.GPIO gpiozero flask paho-mqtt smtplib email imaplib

# Install DHT sensor library
pip3 install freenove-dht

# Install MQTT broker (optional, for testing locally)
sudo apt install -y mosquitto mosquitto-clients

# Install Flask web server dependencies
pip3 install Flask

# Enable and start Mosquitto service (optional)
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# Confirmation message
echo "Installation complete. You can now run the project."
