import os
import time
import pyaudio
import wave
from google.cloud import speech

# Set up Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "your-credentials-file.json"

def record_audio(seconds=5, filename="test_recording.wav"):
    """Record audio from microphone for specified seconds"""
    chunk = 1024
    format = pyaudio.paInt16
    channels = 1
    rate = 16000
    
    p = pyaudio.PyAudio()
    
    print(f"Recording for {seconds} seconds...")
    
    stream = p.open(format=format,
                    channels=channels,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk)
    
    frames = []
    
    for i in range(0, int(rate / chunk * seconds)):
        data = stream.read(chunk)
        frames.append(data)
    
    print("Recording finished")
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    return filename

def transcribe_audio(file_path):
    """Transcribe audio file using Google Cloud Speech-to-Text"""
    client = speech.SpeechClient()
    
    with open(file_path, "rb") as audio_file:
        content = audio_file.read()
    
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
        enable_automatic_punctuation=True,
    )
    
    print("Transcribing audio...")
    response = client.recognize(config=config, audio=audio)
    
    transcription = ""
    for result in response.results:
        transcription += result.alternatives[0].transcript
    
    return transcription

if __name__ == "__main__":
    # Record audio from microphone
    audio_file = record_audio(5)  # Record for 5 seconds
    
    # Transcribe the recorded audio
    transcription = transcribe_audio(audio_file)
    
    print("Transcription result:")
    print(transcription) 