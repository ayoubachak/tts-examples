import gradio as gr
import pyttsx3
import os
from datetime import datetime 
# Initialize the pyttsx3 engine
engine = pyttsx3.init()

def get_pyttsx3_voices():
    voices = engine.getProperty('voices')
    return {
        voice.name: {voice.id: voice.name} for voice in voices
    }
    
# Retrieve pyttsx3 voices
pytts_voices = get_pyttsx3_voices()

# Determine a default voice ID
default_lang = list(pytts_voices.keys())[0]
voice_dict = pytts_voices[default_lang]
voice_id = list(voice_dict.keys())[0]
print(f"Voice: {voice_id}")

# Sample text for TTS
text = '''
Update Gradio Interface to Use the Function Correctly
Make sure your Gradio output component for the audio is configured correctly to handle file paths. Here's an example of how you might set up the Gradio interface:
'''

def pyttsx3_tts(text, voice_id, output_dir="/tmp"):
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Generate a unique filename for the audio file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_file_path = os.path.join(output_dir, f"audio_{timestamp}.mp3")

    # Set the voice property
    engine.setProperty('voice', voice_id)

    # Save the audio to the specified file
    engine.save_to_file(text, temp_file_path)
    engine.runAndWait()
    engine.stop()
    # Return the path for Gradio to use
    return temp_file_path



# Example usage of pyttsx3_tts
audio_file_path = pyttsx3_tts(text, voice_id, "./tmp")  # Adjust './tmp' if needed based on your project structure
print(f"Audio file saved to: {audio_file_path}")
