from flask import Flask, render_template, Response, jsonify, send_from_directory
import cv2
import time
import threading
import os
import random  # Add this import at the top
import math  # Add this import at the top
import requests
import socket
import speech_recognition as sr  # Import the SpeechRecognition library

app = Flask(__name__)

# Global variables
connection_status = "stable"  # "stable" or "unstable"
current_feed = "live"  # Start with live feed
is_monitoring = True  # Start monitoring by default
backup_video_path = "static/videos/backup_video.mp4"
is_simulating = False
simulation_thread = None
monitor_thread = None
is_transcribing = True
transcription_buffer = []  # Store the last transcriptions

# Mock function to check connection status (in a real app, this would check actual network quality)
def check_connection():
    """
    Check actual internet connectivity with a shorter timeout for faster detection.
    """
    global connection_status
    
    try:
        # Try to connect to Google's DNS server with a shorter timeout (0.5 seconds)
        socket.create_connection(("8.8.8.8", 53), timeout=0.5)
        
        # If we get here, we have internet
        if connection_status != "stable":
            print("Internet connection detected, switching to stable")
            connection_status = "stable"
    except OSError:
        # If we get an error, we don't have internet
        if connection_status != "unstable":
            print("Internet connection lost, switching to unstable")
            connection_status = "unstable"
    
    return connection_status

# Function to monitor connection in a separate thread
def connection_monitor():
    global is_monitoring, connection_status, current_feed
    while is_monitoring:
        status = check_connection()
        if status == "unstable" and current_feed == "live":
            current_feed = "backup"
            print("Connection unstable, switching to backup feed")
        elif status == "stable" and current_feed == "backup":
            current_feed = "live"
            print("Connection stable, switching to live feed")
        time.sleep(0.5)  # Check every 0.5 seconds for faster response

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

@app.route('/live_feed')
def live_feed():
    return Response(generate_live_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/backup_feed')
def backup_feed():
    return Response(generate_backup_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed')
def video_feed():
    if current_feed == "live":
        return Response(generate_live_frames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return Response(generate_backup_frames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_monitoring')
def start_monitoring():
    global is_monitoring
    if not is_monitoring:
        is_monitoring = True
        threading.Thread(target=connection_monitor).start()
        return jsonify({"status": "success", "message": "Connection monitoring started"})
    return jsonify({"status": "info", "message": "Monitoring already running"})

@app.route('/stop_monitoring')
def stop_monitoring():
    global is_monitoring
    is_monitoring = False
    return jsonify({"status": "success", "message": "Connection monitoring stopped"})

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
        "simulating": is_simulating,
        "internet_accessible": internet_accessible,
        "transcription": transcription_buffer[-1] if transcription_buffer else "",
        "full_transcript": transcription_buffer
    })

@app.route('/toggle_feed')
def toggle_feed():
    global current_feed
    current_feed = "backup" if current_feed == "live" else "live"
    return jsonify({"status": "success", "current_feed": current_feed})

@app.route('/simulate_poor_connection')
def simulate_poor_connection():
    global connection_status, current_feed
    connection_status = "unstable"
    
    # If monitoring is active and we're on live feed, switch to backup
    if is_monitoring and current_feed == "live":
        current_feed = "backup"
    
    return jsonify({
        "status": "success", 
        "message": "Connection set to unstable",
        "connection": connection_status,
        "current_feed": current_feed
    })

@app.route('/reset_connection')
def reset_connection():
    global connection_status, current_feed
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

@app.route('/simulate_rapid_switching')
def simulate_rapid_switching():
    global is_simulating, simulation_thread
    
    if is_simulating:
        # Stop the simulation if it's already running
        is_simulating = False
        if simulation_thread and simulation_thread.is_alive():
            simulation_thread.join(timeout=1.0)
        return jsonify({
            "status": "success", 
            "message": "Simulation stopped",
            "simulating": False
        })
    else:
        # Start the simulation
        is_simulating = True
        simulation_thread = threading.Thread(target=simulate_wifi_fluctuations)
        simulation_thread.daemon = True
        simulation_thread.start()
        return jsonify({
            "status": "success", 
            "message": "Simulation started - simulating Wi-Fi fluctuations",
            "simulating": True
        })

def simulate_wifi_fluctuations():
    """Simulate realistic Wi-Fi signal fluctuations with a wave pattern and random elements"""
    global is_simulating, current_feed, connection_status
    
    start_time = time.time()
    duration = 20  # Total duration in seconds
    
    while is_simulating and (time.time() - start_time) < duration:
        # Calculate a wave pattern based on time
        elapsed = time.time() - start_time
        # Wave function with period of ~5 seconds
        wave_value = math.sin(elapsed * 0.6) 
        
        # Add random noise to the wave
        noise = random.uniform(-0.3, 0.3)
        signal_quality = wave_value + noise
        
        # Determine if we should switch based on signal quality
        if signal_quality < -0.5:  # Poor signal
            if current_feed == "live":
                current_feed = "backup"
                connection_status = "unstable"
                print(f"Simulation: Signal quality low ({signal_quality:.2f}), switched to backup feed")
        elif signal_quality > 0.5:  # Good signal
            if current_feed == "backup":
                current_feed = "live"
                connection_status = "stable"
                print(f"Simulation: Signal quality good ({signal_quality:.2f}), switched to live feed")
        
        # Random sleep between 0.5 and 2 seconds
        time.sleep(random.uniform(0.5, 2.0))
    
    # Reset at the end
    is_simulating = False
    print("Simulation completed")

@app.route('/backup_video')
def backup_video():
    return send_from_directory('static/videos', 'backup_video.mp4')

@app.route('/backup_video_file')
def backup_video_file():
    return send_from_directory('static/videos', 'backup_video.mp4')

@app.route('/start_transcription')
def start_transcription_route():
    """Start the transcription process in a separate thread."""
    threading.Thread(target=transcribe_microphone).start()
    return jsonify({"status": "success", "message": "Transcription started"})

def start_transcription():
    """Start the transcription process directly (without HTTP request)."""
    threading.Thread(target=transcribe_microphone).start()
    print("Transcription started")

def transcribe_microphone():
    """Transcribe audio from microphone in real-time."""
    global transcription_buffer
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        print("Listening...")
        
        while True:
            try:
                audio = recognizer.listen(source, timeout=5)  # Listen for audio
                print("Recognizing...")
                transcription = recognizer.recognize_google(audio)  
                print(f"Transcribed: {transcription}")
                transcription_buffer.append(transcription)  # Store the transcription
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
            except Exception as e:
                print(f"An error occurred: {e}")

def main():
    """
    Main function that serves as the entry point of the program.
    """
    # Create the static/videos directory if it doesn't exist
    os.makedirs("static/videos", exist_ok=True)
    
    # Check if backup video exists, if not, print a warning
    if not os.path.exists(backup_video_path):
        print(f"Warning: Backup video not found at {backup_video_path}")
        print("Please place your backup video at this location.")
    
    # Start the monitoring thread
    global monitor_thread
    if monitor_thread is None:
        monitor_thread = threading.Thread(target=connection_monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        print("Connection monitoring started automatically")
    
    # Start transcription directly (not through a route)
    start_transcription()
    
    app.run(debug=True, threaded=True)

if __name__ == "__main__":
    main()

    #test: python main.py
    #test2: python -m main