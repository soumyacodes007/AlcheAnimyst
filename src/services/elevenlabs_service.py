import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import save
import logging

# This line loads the environment variables from your .env file
load_dotenv()

# Initialize the ElevenLabs client. This part is still correct.
client = ElevenLabs(
  api_key=os.environ.get("ELEVENLABS_API_KEY"),
)

# In services/elevenlabs_service.py

# ... (imports and client initialization are correct) ...

# In services/elevenlabs_service.py

# ... (imports and client initialization are assumed correct) ...

def generate_audio(script: str, output_filename: str = "narration.mp3") -> str:
    """
    Generates audio using the ElevenLabs API and saves it to a file.
    Returns the path to the generated audio file if successful.
    Raises an exception if it fails.
    """
    if not script or not script.strip():
        logging.warning("Text for audio generation is empty. Skipping audio.")
        raise ValueError("Script cannot be empty for audio generation.")

    logging.info(f"Generating audio with ElevenLabs for script: '{script[:50]}...'")
    try:
        # Corrected voice ID for "Rachel"
        voice_id_string = "21m00Tcm4TlvDq8ikWAM"

        # Generate audio stream using the ElevenLabs API
        audio_stream = client.text_to_speech.stream(
            text=script,
            voice_id=voice_id_string,
        )

        # Save the audio stream to the specified file
        save(audio_stream, output_filename)
        
        logging.info(f"Audio successfully generated and saved to {output_filename}")
        return output_filename

    except Exception as e:
        logging.error(f"Failed to generate audio with ElevenLabs: {e}")
        raise