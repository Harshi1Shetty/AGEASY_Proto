from flask import Flask, request, jsonify
from pydub import AudioSegment
import speech_recognition as sr
import requests
import os

app = Flask(__name__)

# WATI API credentials
WATI_API_KEY = "
WATI_API_URL = "https://api"

# Define keywords and associated responses
keyword_responses = {
    ("StomachAche", "Tummy Ache", "Tummy Pain", "Stomach cake", "pet dard", "peth dard" ,"Peith Dard"): "Medical advice for stomach ache.",
    ("Headache", "Head Pain", "Migraine", "Sir Dard", "Sar Dard", "SUr dard"): "Medical advice for headache.",
    
    # Add more keywords and responses as needed
}

def convert_ogg_to_wav(ogg_file_path, wav_file_path):
    """Convert an OGG file to WAV format."""
    audio = AudioSegment.from_ogg(ogg_file_path)
    audio.export(wav_file_path, format="wav")

def transcribe_audio_and_detect_keywords(file_path):
    """Transcribe audio from a file and detect keywords."""
    recognizer = sr.Recognizer()
    transcription = ""

    wav_file_path = "converted_audio.wav"
    convert_ogg_to_wav(file_path, wav_file_path)

    with sr.AudioFile(wav_file_path) as source:
        audio_data = recognizer.record(source)
        transcription = recognizer.recognize_google(audio_data)
        print(f"Transcription: {transcription}")

    detected_responses = []
    for keywords, response in keyword_responses.items():
        if any(keyword.lower() in transcription.lower() for keyword in keywords):
            detected_responses.append(response)

    os.remove(wav_file_path)  # Clean up converted file
    return transcription, detected_responses

def send_message_via_wati(to_number, message):
    """Send message back to the user via WATI API."""
    headers = {
        "Content-Type": "application/json",
        "apikey": WATI_API_KEY
    }
    payload = {
        "channel": "whatsapp",
        "source": "919769155860",
        "destination": 919321073262,
        "message": {"text": message}
    }
    response = requests.post(WATI_API_URL, headers=headers, json=payload)
    print("WATI response:", response.json())
    return response.json()

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    message_type = data.get("type")
    from_number = data.get("payload", {}).get("source")

    if message_type == "audio":
        media_url = data.get("payload", {}).get("media", {}).get("url")
        
        # Download the OGG file
        ogg_file_path = "incoming_audio.ogg"
        response = requests.get(media_url)

        with open(ogg_file_path, "wb") as f:
            f.write(response.content)

        # Process the audio and detect keywords
        transcription, responses = transcribe_audio_and_detect_keywords(ogg_file_path)

        # Compose the response message based on detected keywords
        if responses:
            response_text = " ".join(responses)
        else:
            response_text = "No specific advice detected from the audio."

        # Send the response back via WATI
        send_message_via_wati(from_number, response_text)

        # Clean up
        os.remove(ogg_file_path)

    return jsonify({"status": "Processed"}), 200

if __name__ == "__main__":
    app.run( )
