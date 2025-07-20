import vosk
import sounddevice as sd
import queue
import json

# --- Setup ---
# This queue will hold the audio data
q = queue.Queue()

# This function is called by the sounddevice stream for each audio chunk
def audio_callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, flush=True)
    q.put(bytes(indata))

# --- Model Loading ---
# The path to your Vosk model folder
# Ensure this folder name matches the one you downloaded and unzipped.
MODEL_PATH = "vosk-model-small-en-us-0.15" 

try:
    model = vosk.Model(MODEL_PATH)
except Exception as e:
    print(f"Error loading model from '{MODEL_PATH}'.")
    print("Please make sure the model folder is in the same directory as the script and the path is correct.")
    print(e)
    exit(1)

# The sample rate must match the model's expected rate (usually 16000 or 44100)
# Check the model's documentation if unsure. Most small models use 16000.
SAMPLE_RATE = 16000
DEVICE_INFO = sd.query_devices(None, 'input')
# If your microphone's default sample rate isn't what the model expects, you can set it here
# SAMPLE_RATE = int(DEVICE_INFO['default_samplerate'])


# Create the main recognizer object
recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE)
recognizer.SetWords(True) # To get word-level timestamps

print("Starting live recognition. Press Ctrl+C to stop.")

# --- Main Recognition Loop ---
try:
    # Open the microphone stream
    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, device=None, 
                           dtype='int16', channels=1, callback=audio_callback):
        
        while True:
            # Get audio data from the queue
            data = q.get()
            
            # Feed the data to the recognizer
            if recognizer.AcceptWaveform(data):
                # When a full phrase is detected, get the final result
                result_json = recognizer.Result()
                result = json.loads(result_json)
                if result.get("text"):
                    print("Final Command:", result["text"])
            else:
                # As you speak, get partial results for a "live" feel
                partial_result_json = recognizer.PartialResult()
                partial_result = json.loads(partial_result_json)
                if partial_result.get("partial"):
                    # Print on the same line to create a live-updating effect
                    print("Partial:", partial_result["partial"], end='\r')

except KeyboardInterrupt:
    print("\nRecognition stopped.")
except Exception as e:
    print(f"An error occurred: {e}")