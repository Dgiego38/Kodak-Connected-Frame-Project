Kodak Connected Frame Project
This project allows you to turn a digital photo frame into a smart, connected device that displays local weather updates and live news feeds, powered by a local Python server.

🚀 Features
Automatic Weather: Fetches real-time weather data for your location using Open-Meteo.

Live News: Displays the latest headlines from a configured RSS feed.

Automatic Setup: Automatically detects your local network IP and coordinates based on your city.

Customizable: Personalize the footer of your display with your name.

🛠 Prerequisites
Python 3.x installed on your machine.

A digital photo frame capable of displaying images via an RSS/XML feed.

📦 Installation
Clone the repository:

Bash
git clone https://github.com/yourusername/kodak-frame.git
cd kodak-frame
Install dependencies:
It is recommended to install the required libraries using the provided requirements.txt:

Bash
python -m pip install -r requirements.txt
⚙️ Configuration
Before running the project for the first time, you must configure your local environment (IP address, location, etc.). Run the setup script:

Bash
python setup.py
City: Enter your city name (e.g., Strasbourg).

Footer: Enter your name to appear at the bottom of the weather images.

Server IP: The script will automatically detect your local IP. Press Enter to confirm or type a specific one if needed.

The script will automatically update app.py, module_meteo.py, and feed.xml with your specific settings.

🚀 Usage
To start the server and begin generating the image feeds, run:

Bash
python app.py
Once running, your frame can pull the data from your local server using the URL: http://<YOUR_IP>:8000/feed.xml.

📂 Project Structure
app.py: The main web server (Flask) that hosts the images and the RSS feed.

module_meteo.py: Logic to generate the weather images.

module_news.py: Logic to fetch RSS feeds and generate news images.

setup.py: Configuration script to automate settings.

requirements.txt: List of required Python packages.

feed.xml: The RSS template your frame uses to find the images.

📝 License
This project is for personal use. Feel free to modify and expand upon it!

Created by Diego Grenados
# Kodak-Connected-Frame-Project
Kodak Connected Frame Project
