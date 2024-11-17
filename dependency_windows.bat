@echo off

:: Ensure Python 3 and pip are installed
echo "Make sure Python 3.x and pip are installed."

:: Upgrade pip to the latest version
python -m pip install --upgrade pip

:: Install required Python libraries
pip install RPi.GPIO gpiozero flask paho-mqtt freenove-dht

:: Install Flask web server dependencies
pip install Flask

:: Message to inform user
echo Installation complete. You can now run the project.
pause
