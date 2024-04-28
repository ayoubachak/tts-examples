import requests
import json
import gradio as gr
import os
import warnings
from dotenv import load_dotenv
load_dotenv()
# call https://api.elevenlabs.io/v1/voices to list the voice IDs with Xi-Api-Key in the header with value 4d02f07f1aa0ff0b5c12e208a9f69571

# Get the values of the variables from the environment
api_key = os.getenv("11labs_api_key")
cert_path = os.getenv("cert_path")

# Check if api_key is present
if not api_key:
    raise ValueError("API key not found in the .env file")

# Check if cert_path is present
if not cert_path:
    warnings.warn("Certificate path not found in the .env file")
    cert_path = False
    
CHUNK_SIZE = 1024
voice_settings_dir = "11labs/voice_settings"

models = []
voices = []
voice_settings_dict = {}
output_formats = [
                ("mp3_22050_32", "mp3_22050_32 - output format, mp3 with 22.05kHz sample rate at 32kbps"),
                ("mp3_44100_32", "mp3_44100_32 - output format, mp3 with 44.1kHz sample rate at 32kbps"),
                ("mp3_44100_64", "mp3_44100_64 - output format, mp3 with 44.1kHz sample rate at 64kbps"),
                ("mp3_44100_96", "mp3_44100_96 - output format, mp3 with 44.1kHz sample rate at 96kbps"),
                ("mp3_44100_128", "mp3_44100_128 - default output format, mp3 with 44.1kHz sample rate at 128kbps"),
                ("mp3_44100_192", "mp3_44100_192 - output format, mp3 with 44.1kHz sample rate at 192kbps. Requires you to be subscribed to Creator tier or above."),
                ("pcm_16000", "pcm_16000 - PCM format (S16LE) with 16kHz sample rate"),
                ("pcm_22050", "pcm_22050 - PCM format (S16LE) with 22.05kHz sample rate"),
                ("pcm_24000", "pcm_24000 - PCM format (S16LE) with 24kHz sample rate"),
                ("pcm_44100", "pcm_44100 - PCM format (S16LE) with 44.1kHz sample rate. Requires you to be subscribed to Pro tier or above."),
                ("ulaw_8000", "ulaw_8000 - μ-law format (sometimes written mu-law, often approximated as u-law) with 8kHz sample rate. Note that this format is commonly used for Twilio")
            ]
try :
    with open("11labs/voices.json", "r") as file:
        voices = json.load(file)
    voices = voices["voices"] 
except Exception as e:
    print(f"Warning : voices aren't loaded")
    


def load_models():
    global models
    try :
        with open("11labs/models.json", "r") as file:
            models = json.load(file)
    except Exception as e:
        print(f"Warning : models aren't loaded")    

load_models()
def load_voices():
    global voices
    try :
        with open("11labs/voices.json", "r") as file:
            voices = json.load(file)
            voices = voices["voices"]
    except Exception as e:
        print(f"Warning : voices aren't loaded")
load_voices()

# load the voice settings
for filename in os.listdir(voice_settings_dir):
    file_path = os.path.join(voice_settings_dir, filename)
    with open(file_path, "r") as file:
        voice_content = file.read()
        voice_settings_dict[filename]= voice_content
        
def get_voice_ids():
    headers = {
        "Xi-Api-Key": api_key
    }

    response = requests.get("https://api.elevenlabs.io/v1/voices", headers=headers, verify=cert_path)

    if response.status_code == 200:
        voice_ids = response.json()
        # Process the voice IDs as needed
        return voice_ids
    else:
        print(f"Error: {response.text}")

def save_voices():
    voice_ids = get_voice_ids()
    with open("11labs/voices.json", "w") as file:
        json.dump(voice_ids, file)
    load_voices() # will load them to the global variable
    return voice_ids

def save_models():
    headers = {
        "Xi-Api-Key": api_key
    }

    response = requests.get("https://api.elevenlabs.io/v1/models", headers=headers, verify=cert_path)

    if response.status_code == 200:
        models = response.json()
        with open("11labs/models.json", "w") as file:
            json.dump(models, file)
        load_models() # will load them to the global variable
        # Process the models as needed
        return models
    else:
        print(f"Error: {response.text}")

def model_exists(model_id, returnit = True):
    global models
    for model in models:
        if model["model_id"] == model_id:
            if returnit:
                return model
            return True
    return False

def voice_exists(voice_id, returnit = True) -> dict | bool:
    global voices
    for voice in voices:
        if voice["voice_id"] == voice_id:
            if returnit:
                return voice
            return True
    return False

def load_voice_settings(voice_id, use_cache=True):
    global voice_settings_dict
    # Check if voice settings are cached and use_cache is True
    voice_settings_cache_path = os.path.join(voice_settings_dir, f"{voice_id}.json")
    if use_cache: # the voice settings are all loaded when the platform starts
        if voice_id in voice_settings_dict.keys(): return voice_settings_dict[voice_id] # load from the ram first
        if os.path.exists(voice_settings_cache_path):
            with open(voice_settings_cache_path, "r") as file:
                return json.load(file)
    
    # Fetch voice settings from the API if not found in cache or use_cache is False
    url = f"https://api.elevenlabs.io/v1/voices/{voice_id}/settings"
    headers = {"xi-api-key": api_key}
    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        voice_settings = response.json()
        
        # Save voice settings to cache
        
        os.makedirs(voice_settings_dir, exist_ok=True)
        with open(voice_settings_cache_path, "w") as file:
            json.dump(voice_settings, file)
        voice_settings_dict[voice_id] = voice_settings
        return voice_settings
    else:
        print(f"Failed to fetch voice settings for voice ID {voice_id}. Error: {response.text}")
        return None
    

class VoiceLabels:
    def __init__(self, voice_labels : dict) -> None:
        if not isinstance(voice_labels, dict):
            raise ValueError("voice_labels must be a dictionary")
        self.accent = voice_labels.get("accent", None)
        self.description = voice_labels.get("description", None)
        self.age = voice_labels.get("age", None)
        self.gender = voice_labels.get("gender", None)
        self.use_case = voice_labels.get("use case", None)


class Voice:
    def __init__(self, voice_id):
        self.voice : dict = voice_exists(voice_id, returnit=True)
        self.voice_id = voice_id
        self.id = voice_id
        if self.voice :
            self.name = self.voice.get("name", None)
            self.preview_url = self.voice.get("preview_url", None)
            
            self.labels = VoiceLabels(self.voice.get("labels", None))
            self.accent = self.labels.accent
            self.description = self.labels.description
            self.age = self.labels.age
            self.gender = self.labels.gender
            self.use_case = self.labels.use_case
            
            self.fine_tuning : dict | None = self.voice.get("fine_tuning", None)
            self.fine_tuning_state =self.fine_tuning.get("fine_tuning_state", None) if self.fine_tuning else None
            self.fine_tuning_language =self.fine_tuning.get("fine_tuning_state", None) if self.fine_tuning else None
            self.high_quality_base_model_ids : list = self.voice.get("high_quality_base_model_ids", [])
        else :
            raise ValueError(f"Voice with ID {voice_id} doesn't exist")
        
def get_voice_info_and_preview(voice_id):
    try:
        voice = Voice(voice_id=voice_id)
        info_text = f"Name: {voice.name}\n"
        info_text += f"Preview URL: {voice.preview_url}\n"
        info_text += f"Accent: {voice.accent}\n"
        info_text += f"Description: {voice.description}\n"
        info_text += f"Age: {voice.age}\n"
        info_text += f"Gender: {voice.gender}\n"
        info_text += f"Use Case: {voice.use_case}\n"
        info_text += f"Fine Tuning State: {voice.fine_tuning_state}\n"
        info_text += f"Fine Tuning Language: {voice.fine_tuning_language}\n"
        info_text += f"High Quality Base Model IDs: {voice.high_quality_base_model_ids}\n"
        best_fit_model = voice.high_quality_base_model_ids[0] if len(voice.high_quality_base_model_ids) > 0 else None
        return info_text, voice.preview_url,  best_fit_model
    except ValueError as e:
        return str(e), "", None   
            
def test():
    
    url = "https://api.elevenlabs.io/v1/text-to-speech/onwK4e9ZLuTAKqWW03F9"

    querystring = {
        "optimize_streaming_latency":"1",
        "output_format":"mp3_44100_128"
        }

    payload = {
        "text": "Did you know that honeybees, a vital part of our agricultural ecosystem, are responsible for pollinating approximately one-third of the food crops we consume? These industrious insects play a crucial role in the growth of many fruits, vegetables, and nuts, contributing to both biodiversity and food security. Interestingly, a single bee colony can pollinate up to 300 million flowers each day. As they transfer pollen from one bloom to another, bees not only help in the reproduction of plants but also enhance the quality and size of the crops. Protecting these essential pollinators is critical for sustaining our natural food sources.",
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0,
            "use_speaker_boost": True
        }
    }
    headers = {
        "Accept": "audio/mpeg",
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, params=querystring, verify=False)
        response.raise_for_status()  # This will raise an exception for HTTP error codes

        # Assuming response is fine, save the file
        with open('output.mp3', 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print("File has been written successfully.")

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # Python 3.6
        print(f"Response status code: {response.status_code}")
        print(f"Response text: {response.text}")

    except requests.exceptions.RequestException as err:
        print(f"Error occurred: {err}")

    except Exception as e:
        print(f"An error occurred: {e}")
    
def text_to_speech(
    text,
    model_id,
    voice_id,
    voice_settings,
    optimize_streaming_latency,
    output_format
    ):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    querystring = {
        "optimize_streaming_latency":optimize_streaming_latency,
        "output_format":output_format
        }
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": voice_settings
    }
    headers = {
        "Accept": "audio/mpeg",
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    if not model_id or not voice_id:
        print("Model ID or Voice ID not selected.")
        return None, "Model ID or Voice ID not selected."
    try:
        response = requests.post(url, json=payload, headers=headers, params=querystring, verify=False)
        response.raise_for_status()  # This will raise an exception for HTTP error codes
        save_path = f'output.mp3'
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print("File has been written successfully.")
        return save_path, "TTS Successfull."

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # Python 3.6
        print(f"Response status code: {response.status_code}")
        print(f"Response text: {response.text}")
        return None, f"HTTP error occurred: {http_err}"

    except requests.exceptions.RequestException as err:
        print(f"Error occurred: {err}")
        return None, f"Error occurred: {err}"

    except Exception as e:
        print(f"An error occurred: {e}")
        return None, f"An error occurred: {e}"
    
    
def get_models_drop_down(new_models=[]):
    global models
    if len(new_models) > 0:
        models = new_models
    models_list = []
    for model in models:
        models_list.append((model["name"], model["model_id"]))
    return gr.Dropdown(choices=models_list, label="Select Model", allow_custom_value=True, scale=9, interactive=True)
    
def get_voices_drop_down(new_voices=[]):
    global voices
    if len(new_voices) > 0:
        voices = new_voices
    voice_list = []
    for voice in voices:
        voice_list.append((voice["name"], voice["voice_id"]))
    return gr.Dropdown(choices=voice_list, label="Select Voice", allow_custom_value=True, scale=9, interactive=True)    
    
with gr.Blocks() as demo:
    with gr.Row():
        api_key_input = gr.Textbox(label="API Key", value=api_key, scale=8)
        update_api_key = gr.Button("Update API Key")
        def update_api_key_value(new_api_key):
            global api_key
            api_key = new_api_key
            print("API Key updated successfully.")
        update_api_key.click(
            update_api_key_value,
            inputs=[api_key_input],
            outputs=[],
            )
    with gr.Row():
        use_cache_checkbox = gr.Checkbox(label="Use Cache", value=True)
    with gr.Row():
        text = gr.Textbox(label="Enter your text", lines=5, value="Hello there!")
    with gr.Row():
        with gr.Column(scale=5):
            with gr.Accordion(label="Models / Voices",open=True) as acc:
                with gr.Row():
                    models_list = get_models_drop_down()
                    get_models_btn = gr.Button("Get Models", scale=1)
                    def get_models(use_cache):
                        global models
                        if use_cache :
                            return models
                        save_models() # will change the global voices variable
                        return models

                    get_models_btn.click(
                        get_models,
                        inputs=[use_cache_checkbox],
                        outputs=[models_list],
                        )
                with gr.Row():
                    voice_list = get_voices_drop_down()
                    get_voices_btn = gr.Button("Get Voices", scale=1)
                    def get_voices(use_cache):
                        global voices
                        if use_cache :
                            return voices
                        save_voices() # will change the global voices variable
                        return voices
                    
                    get_voices_btn.click(
                        get_voices,
                        inputs=[use_cache_checkbox],
                        outputs=[voice_list],
                        )
                with gr.Row():
                    voice_information_display = gr.Textbox(value="Select a voice to view information", label="Voice Information", interactive=False)
                    voice_audio_preview = gr.Audio( label="Voice Preview", interactive=False)
                voice_list.change(
                    get_voice_info_and_preview,
                    inputs=[voice_list],
                    outputs=[voice_information_display, voice_audio_preview, models_list],
                    )
                with gr.Row():
                    with gr.Accordion(label="Voice Settings", open=True):
                        load_voice_settings_btn = gr.Button("Load Voice Settings")
                        stability_input = gr.Slider(label="Stability", minimum=0, maximum=5, step=0.1, value=0.5, interactive=True)
                        similarity_boost_input = gr.Slider(label="Similarity Boost", minimum=0, maximum=5, step=0.1, value=0.75, interactive=True)
                        style_input = gr.Slider(label="Style", minimum=0, maximum=5, step=0.1, value=0, interactive=True)
                        use_speaker_boost_checkbox = gr.Checkbox(label="Use Speaker Boost", value=True)
                        def load_voice_settings_values(voice_id, use_cache):
                            voice_settings : dict | None= load_voice_settings(voice_id=voice_id, use_cache=use_cache)
                            if voice_settings :
                                return (
                                    voice_settings.get("stability", None), 
                                    voice_settings.get("similarity_boost", None), 
                                    voice_settings.get("style", None), 
                                    voice_settings.get("use_speaker_boost", None)
                                )
                            print("Couldn't load voice settings")
                            return (None, None, None, None)
                        load_voice_settings_btn.click(
                            load_voice_settings_values,
                            inputs=[voice_list, use_cache_checkbox],
                            outputs=[stability_input, similarity_boost_input, style_input, use_speaker_boost_checkbox],
                        )
                     
            with gr.Accordion(label="Text-to-Speech", open=True):
                with gr.Row():
                    optimize_streaming_latency_input = gr.Slider(label="Optimize Streaming Latency", minimum=0, maximum=4, step=1, value=1, interactive=True)
                    output_format = gr.Dropdown(choices=[(name, key) for key, name in output_formats], value="mp3_44100_128", label="Output Format", interactive=True)
                
        with gr.Column(scale=5):
            voice_output = gr.Audio(label="Voice Output")
            voice_output_status = gr.Textbox(label="Voice Output Status", interactive=False)
            generate_tts_btn = gr.Button("Generate TTS")
            def generate_tts_wrapper(
                    text,
                    model_id,
                    voice_id,
                    stability_input,
                    similarity_boost_input,
                    style_input,
                    use_speaker_boost_checkbox,
                    optimize_streaming_latency,
                    output_format
                ):
                voice_settings = {
                    "stability": stability_input,
                    "similarity_boost": similarity_boost_input,
                    "style": style_input,
                    "use_speaker_boost": use_speaker_boost_checkbox,
                }
                return text_to_speech(
                    text=text,
                    model_id=model_id,
                    voice_id=voice_id,
                    voice_settings=voice_settings,
                    optimize_streaming_latency=optimize_streaming_latency,
                    output_format=output_format
                    )
                
            generate_tts_btn.click(
                generate_tts_wrapper,
                inputs=[
                    text, 
                    models_list, 
                    voice_list, 
                    stability_input, 
                    similarity_boost_input, 
                    style_input, 
                    use_speaker_boost_checkbox, 
                    optimize_streaming_latency_input, 
                    output_format
                    ],
                outputs=[voice_output, voice_output_status],
            )
    
def main():
    demo.queue(default_concurrency_limit=None).launch()
    
if __name__ == "__main__":
    main()