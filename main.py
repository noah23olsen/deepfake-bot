from flask import Flask, render_template, Response, jsonify, send_from_directory
import cv2
import time
import threading
import os
import socket
import subprocess  # For playing audio without pygame

app = Flask(__name__)

# Global variables
connection_status = "stable"  # "stable" or "unstable"
current_feed = "live"  # Start with live feed
is_monitoring = True  # Start monitoring by default
backup_video_path = "static/videos/backup_video.mp4"
um_audio_path = "static/audio/um_filler.mp3"  # Path to pre-recorded um file
last_connection_change = 0  # Track when connection status last changed
is_playing_um = False  # Flag to prevent multiple simultaneous playbacks
is_simulation_active = False  # New flag to track if a simulation is in progress

# Function to check connection status
def check_connection():
    """
    Check actual internet connectivity with a shorter timeout for faster detection.
    """
    global connection_status, last_connection_change, is_playing_um, current_feed
    
    # Skip connection check if a simulation is active
    if is_simulation_active:
        return connection_status
    
    try:
        # Try to connect to Google's DNS server with a shorter timeout (0.5 seconds)
        socket.create_connection(("8.8.8.8", 53), timeout=0.5)
        
        # If we get here, we have internet
        if connection_status != "stable":
            print("Internet connection detected, switching to stable")
            connection_status = "stable"
            last_connection_change = time.time()
            
            # If we were on backup feed due to connection issues, switch back to live
            if current_feed == "backup":
                current_feed = "live"
    except OSError:
        # If we get an error, we don't have internet
        if connection_status != "unstable":
            print("Internet connection lost, switching to unstable")
            connection_status = "unstable"
            current_feed = "backup"
            last_connection_change = time.time()
            
            # Play the "um" sound when connection drops
            if not is_playing_um and os.path.exists(um_audio_path):
                threading.Thread(target=play_um_sound).start()
    
    return connection_status

# Function to play the "um" sound using system commands
def play_um_sound():
    """Play the um filler sound when connection drops using system commands"""
    global is_playing_um
    
    try:
        is_playing_um = True
        print("Playing um sound...")
        
        # Determine the OS and use appropriate command to play audio
        if os.name == 'nt':  # Windows
            os.system(f'start {um_audio_path}')
        elif os.name == 'posix':  # macOS or Linux
            # Check if we're on macOS
            if os.path.exists('/usr/bin/afplay'):  # macOS
                subprocess.run(['afplay', um_audio_path])
            else:  # Linux
                # Try different players
                players = ['aplay', 'paplay', 'mplayer', 'mpg123']
                for player in players:
                    try:
                        subprocess.run([player, um_audio_path], check=False)
                        break
                    except FileNotFoundError:
                        continue
        
        time.sleep(2)  # Give some time for the audio to play
        is_playing_um = False
        print("Um sound finished")
    except Exception as e:
        print(f"Error playing um sound: {e}")
        is_playing_um = False

# Function to monitor connection in a separate thread
def connection_monitor():
    global is_monitoring, connection_status, current_feed
    while is_monitoring:
        try:
            status = check_connection()
            
            # The check_connection function now handles the simulation,
            # so we don't need to do anything else here
            
            time.sleep(0.5)  # Check every 0.5 seconds for faster response
        except Exception as e:
            print(f"Error in connection monitor: {e}")
            time.sleep(1)  # Wait a bit longer if there's an error

# Function to generate frames from the live camera
def generate_live_frames():
    camera = cv2.VideoCapture(0)  # 0 is usually the default webcam
    if not camera.isOpened():
        print("Error: Could not open webcam")
        return
    
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    camera.release()

# Function to generate frames from the backup video
def generate_backup_frames():
    video = cv2.VideoCapture('static/videos/backup_video.mp4')
    if not video.isOpened():
        print("Error: Could not open backup video")
        return
    
    while True:
        success, frame = video.read()
        if not success:
            # Loop the video when it ends
            video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    video.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    if current_feed == "live":
        return Response(generate_live_frames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return Response(generate_backup_frames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/live_feed')
def live_feed():
    """Route for live feed - redirects to video_feed"""
    return Response(generate_live_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/backup_feed')
def backup_feed():
    """Route for backup feed - redirects to video_feed"""
    return Response(generate_backup_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/backup_video')
def backup_video():
    """Route to serve the backup video file"""
    return send_from_directory('static/videos', 'backup_video.mp4')

@app.route('/backup_video_file')
def backup_video_file():
    """Alternative route to serve the backup video file"""
    return send_from_directory('static/videos', 'backup_video.mp4')

@app.route('/vc_video')
def vc_video():
    """Serve the VC video file"""
    return send_from_directory('static/videos', 'vc_video.mp4')

@app.route('/get_status')
def get_status():
    # Check if we can access a known website
    internet_accessible = False
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=1)
        internet_accessible = True
    except:
        pass
    
    return jsonify({
        "connection": connection_status,
        "current_feed": current_feed,
        "monitoring": is_monitoring,
        "internet_accessible": internet_accessible
    })

@app.route('/simulate_poor_connection')
def simulate_poor_connection():
    global connection_status, current_feed, is_simulation_active
    
    # Set simulation active to prevent monitoring thread from interfering
    is_simulation_active = True
    
    connection_status = "unstable"
    
    # Always switch to backup feed when simulating poor connection
    current_feed = "backup"
    
    # Play the "um" sound when simulating connection drop
    if os.path.exists(um_audio_path):
        threading.Thread(target=play_um_sound).start()
    
    # Schedule switching back after 6 seconds
    def switch_back():
        time.sleep(6)
        global connection_status, current_feed, is_simulation_active
        connection_status = "stable"
        current_feed = "live"
        # Reset simulation flag
        is_simulation_active = False
        print("Connection set back to stable after simulation")
    
    # Start the timer in a separate thread
    t = threading.Thread(target=switch_back)
    t.daemon = True
    t.start()
    
    return jsonify({
        "status": "success", 
        "message": "Connection set to unstable",
        "connection": connection_status,
        "current_feed": current_feed
    })

@app.route('/reset_connection')
def reset_connection():
    global connection_status, current_feed, is_simulation_active
    
    # Clear simulation flag
    is_simulation_active = False
    
    connection_status = "stable"
    
    # If monitoring is active and we're on backup feed, switch to live
    if is_monitoring and current_feed == "backup":
        current_feed = "live"
    
    return jsonify({
        "status": "success", 
        "message": "Connection reset to stable",
        "connection": connection_status,
        "current_feed": current_feed
    })

# Add this function to create the um filler audio if it doesn't exist
def create_um_filler_audio():
    """Create a filler audio file with 'um...' sounds if it doesn't exist"""
    if os.path.exists(um_audio_path):
        return
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(um_audio_path), exist_ok=True)
    
    print(f"Warning: Um filler audio not found at {um_audio_path}")
    print("Please place your um filler audio at this location.")

@app.route('/toggle_feed')
def toggle_feed():
    global current_feed
    current_feed = "backup" if current_feed == "live" else "live"
    return jsonify({"status": "success", "current_feed": current_feed})

@app.route('/start_monitoring')
def start_monitoring():
    global is_monitoring, monitor_thread
    if not is_monitoring:
        is_monitoring = True
        monitor_thread = threading.Thread(target=connection_monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        return jsonify({"status": "success", "message": "Connection monitoring started"})
    return jsonify({"status": "info", "message": "Monitoring already running"})

@app.route('/stop_monitoring')
def stop_monitoring():
    global is_monitoring
    is_monitoring = False
    return jsonify({"status": "success", "message": "Connection monitoring stopped"})

# Shared function for both real and simulated connection issues
def simulate_connection_issue(trigger_reason="Manually triggered"):
    """
    Handles both real and simulated connection issues:
    1. Switches to unstable connection
    2. Plays the "um" sound
    3. Switches to backup feed
    4. For simulated issues only: switches back after 6 seconds
    """
    global connection_status, current_feed, is_playing_um
    
    # Switch to unstable connection right away
    connection_status = "unstable"
    current_feed = "backup"  # Make sure to switch to backup feed
    print(f"Connection set to unstable - {trigger_reason}")
    
    # Play the "um" sound if not already playing
    if not is_playing_um and os.path.exists(um_audio_path):
        threading.Thread(target=play_um_sound).start()
    
    # For simulated issues (not real outages), switch back after a delay
    if "Real" not in trigger_reason:
        # Schedule switching back after 6 seconds
        def switch_back():
            time.sleep(6)
            global connection_status, current_feed
            connection_status = "stable"
            current_feed = "live"  # Switch back to live feed
            print(f"Connection set back to stable after simulation ({trigger_reason})")
        
        # Start the timer in a separate thread
        t = threading.Thread(target=switch_back)
        t.daemon = True
        t.start()
    
    return {"status": "success", "message": f"Simulating unstable connection - {trigger_reason}"}

@app.route('/simulate_rapid_switching')
def simulate_rapid_switching():
    """Route handler for the simulation button"""
    global connection_status, current_feed, is_playing_um, is_simulation_active
    
    # Set simulation active to prevent monitoring thread from interfering
    is_simulation_active = True
    
    # Set connection to unstable
    connection_status = "unstable"
    
    # Switch to backup feed
    current_feed = "backup"
    
    # Play the "um" sound if not already playing
    if not is_playing_um and os.path.exists(um_audio_path):
        threading.Thread(target=play_um_sound).start()
    
    # Schedule switching back after 6 seconds
    def switch_back():
        time.sleep(6)
        global connection_status, current_feed, is_simulation_active
        connection_status = "stable"
        current_feed = "live"
        # Reset simulation flag
        is_simulation_active = False
        print("Connection set back to stable after simulation")
    
    # Start the timer in a separate thread
    t = threading.Thread(target=switch_back)
    t.daemon = True
    t.start()
    
    return jsonify({
        "status": "success", 
        "message": "Simulating unstable connection",
        "connection": connection_status,
        "current_feed": current_feed
    })

@app.route('/zoom')
def zoom_interface():
    """Render the Zoom-like interface"""
    return render_template('zoom.html')

@app.route('/toggle_monitoring')
def toggle_monitoring():
    """Toggle the connection monitoring on/off"""
    global is_monitoring, monitor_thread
    
    if is_monitoring:
        is_monitoring = False
        return jsonify({"status": "success", "message": "Monitoring stopped", "monitoring": False})
    else:
        is_monitoring = True
        if not monitor_thread or not monitor_thread.is_alive():
            monitor_thread = threading.Thread(target=connection_monitor)
            monitor_thread.daemon = True
            monitor_thread.start()
        return jsonify({"status": "success", "message": "Monitoring started", "monitoring": True})

def main():
    """
    Main function to run the application.
    """
    # Create the static directories if they don't exist
    os.makedirs("static/videos", exist_ok=True)
    os.makedirs("static/audio", exist_ok=True)
    
    # Create the um filler audio if it doesn't exist
    create_um_filler_audio()
    
    # Check if backup video exists, if not, print a warning
    if not os.path.exists(backup_video_path):
        print(f"Warning: Backup video not found at {backup_video_path}")
        print("Please place your backup video at this location.")
    
    # Start the monitoring thread
    global monitor_thread
    monitor_thread = threading.Thread(target=connection_monitor)
    monitor_thread.daemon = True
    monitor_thread.start()
    print("Connection monitoring started automatically")
    
    app.run(debug=True, threaded=True)

if __name__ == "__main__":
    main()

    #test: python main.py
    #test2: python -m main