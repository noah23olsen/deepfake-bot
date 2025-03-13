# deepfake-bot

## Overview
This project is a "Zoom Bot" that takes your place when your WiFi drops. It monitors your internet connection and automatically switches to a backup video feed when your connection becomes unstable, playing an "um" sound effect to make the transition less jarring. When your connection stabilizes, it switches back to your live feed.

The application features:
- Live webcam video feed
- Automatic connection monitoring
- Seamless switching between live and backup feeds
- Zoom-like interface
- Simulation mode for testing

## Installation
To get started, you'll need to install the required dependencies. You can do this using pip. Make sure you have Python installed on your machine.

1. Clone the repository:
   ```bash
   git clone https://github.com/noah23olsen/deepfake-bot.git
   cd deepfake-bot
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application
To run the application, execute the following command:
   ```
   python3 main.py
   ```

   After running the application, open up the web page in your browser by navigating to `http://127.0.0.1:5000/`.

   <small>If using Chrome, you may need to flush your sockets at <a href="chrome://net-internals/#sockets">chrome://net-internals/#sockets</a>.</small>
   

---
   **Note:** This application is currently in beta and may exhibit some bugs. This product works well enough to half-demo, but it is super buggy. 
