import gradio as gr
from gtts import gTTS
from io import BytesIO
import json
import os
from gtts.lang import tts_langs
import pyttsx3
import tempfile
import re
from datetime import datetime
import time

engine = pyttsx3.init()
# List of available languages and their corresponding voices



def get_pyttsx3_voices():
    voices = engine.getProperty('voices')
    return {
        voice.name :{ voice.id : voice.name} for voice in voices
    }
    
gtts_voices = json.load(open(os.path.join( os.path.dirname(__file__), 'gtts_voices.json')) )
pytts_voices = get_pyttsx3_voices()

def google_tts(text, voice='en-us'):
    # Convert text to speech
    tts = gTTS(text=text, lang=voice)
    
    # Save speech to a BytesIO object
    with BytesIO() as audio_stream:
        tts.write_to_fp(audio_stream)
        audio_stream.seek(0)
        
        # Read audio data from BytesIO object
        audio_data = audio_stream.read()
        
        return audio_data
    

def pyttsx3_tts(text, voice_id, output_dir="./tmp"):

    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Initialize pyttsx3 engine inside the function to avoid issues in multi-threaded environments
    # engine = pyttsx3.init()
    engine.setProperty('voice', voice_id)
    
    # Generate a unique filename for the audio file within the specified output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_file_path = os.path.join(output_dir, f"audio_{timestamp}.mp3")

    # Save the audio to the temporary file
    engine.save_to_file(text, temp_file_path)
    engine.runAndWait()

    retries = 5
    while retries > 0:
        if os.path.exists(temp_file_path):
            with open(temp_file_path, 'rb') as audio_file:
                audio_data = BytesIO(audio_file.read())
            os.remove(temp_file_path)
            return audio_data
        time.sleep(1)  # Wait for 1 second before retrying
        retries -= 1

    # If the file is still not available, raise an exception or handle the error as appropriate
    raise FileNotFoundError(f"The audio file was not created: {temp_file_path}")

with gr.Blocks(
    title="Text-to-Speech with Gradio",
) as demo:
    with gr.Row():
        # Create Gradio interface
        with gr.Column(scale=5):
            text_input = gr.Textbox(lines=5, label="Enter your text")
            tts_provider = gr.Radio(choices=['gTTS', 'pyttsx3'], label="TTS Provider", value='gTTS')
            language_input = gr.Dropdown(choices=list(gtts_voices.keys()), label="Select Language")
            voice_input = gr.Dropdown(choices=[], label="Select Voice", allow_custom_value=True)
            
            def update_voice_choice(provider, language):
                if provider == 'gTTS':
                    voice_dict = gtts_voices[language]
                    voice_list = [(name, code) for code, name in voice_dict.items()]
                    return gr.Dropdown(choices=voice_list, value=voice_list[0][1])
                elif provider == 'pyttsx3':
                    voice_dict = pytts_voices[language]
                    voice_list = [(name, code) for code, name in voice_dict.items()]
                    return gr.Dropdown(choices=voice_list, value=voice_list[0][1])
                
            def update_provider_choice(provider):
                if provider == 'gTTS':
                    default_lang = "English"
                    voice_dict = gtts_voices[default_lang]
                    voice_list = [(name, code) for code, name in voice_dict.items()]
                    return gr.Dropdown(choices=list(gtts_voices.keys()), label="Select Language", value=default_lang) ,gr.Dropdown(choices=voice_list, value=voice_list[0][1])
                elif provider == 'pyttsx3':
                    # get the first language from the language dictionary
                    default_lang = list(pytts_voices.keys())[0]
                    voice_dict = pytts_voices[default_lang]
                    voice_list = [(name, code) for code, name in voice_dict.items()]
                    return gr.Dropdown(choices=list(pytts_voices.keys()), label="Select Language", value=default_lang), gr.Dropdown(choices=voice_list, label="Select Voice", value=voice_list[0][1])
                
            tts_provider.change(
                update_provider_choice,
                inputs=[tts_provider ],
                outputs=[language_input, voice_input]
                )
            # Update choices for voice dropdown based on the selected language
            language_input.change(
                update_voice_choice,
                inputs=[tts_provider, language_input],
                outputs=[voice_input]
                )

        with gr.Column(scale=5):
            # Update outputs to match Audio component parameters
            output_audio = gr.Audio(type='numpy', format='mp3')
    with gr.Row():
        def process_tts(text, provider, voice):
            if provider == 'gTTS':
                return google_tts(text, voice)
            elif provider == 'pyttsx3':
                return pyttsx3_tts(text, voice)
            
        submit_button = gr.Button("Submit")
        submit_button.click(
                process_tts,
                inputs=[text_input,tts_provider, voice_input],
                outputs=output_audio, 
            )
   
   
if __name__ == "__main__":
    demo.launch()