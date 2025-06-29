import streamlit as st
import os
import subprocess
import logging

from engine.alchymist_ai import generate_video
from engine.retry_loop import fix_manim_code
from services.video_creation import create_manim_video
from services.elevenlabs_service import generate_audio


# Doing this once at the top of the script
st.set_page_config(
    layout="wide",
    page_title="AlcheAnimyst",
    page_icon="🎬"
)

# Configuration 
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    # - UI
    st.title("🎬 AlcheAnimyst")
    st.markdown("Turn your ideas into animated videos with AI. Just describe the concept, and let the magic happen!")

    # --- Session State Initialization ---
    # To store results and prevent them from disappearing on reruns
    if "video_path" not in st.session_state:
        st.session_state.video_path = None
    if "script" not in st.session_state:
        st.session_state.script = None
    if "manim_code" not in st.session_state:
        st.session_state.manim_code = None
    if "error_message" not in st.session_state:
        st.session_state.error_message = None


    # input section 
    with st.form(key="idea_form"):
        idea = st.text_area(
            "✨ What do you want to animate?",
            height=150,
            placeholder="e.g., 'Explain the Pythagorean theorem with a right-angled triangle and squares on each side.'"
        )
        submitted = st.form_submit_button("Generate Video")

    # logic 
    if submitted:
        # Reset state for new generation
        st.session_state.video_path = None
        st.session_state.script = None
        st.session_state.manim_code = None
        st.session_state.error_message = None

        if not idea.strip():
            st.error("Please enter an idea to generate a video.")
            return

        # Declare file paths to ensure they are available in the 'finally' block for cleanup
        audio_file = None
        current_audio_file = None
        final_video = None
        max_retries = 1

        try:
            # code gen 
            with st.spinner("🧠 Step 1/4: Generating script and Manim code..."):
                video_data, script = generate_video(idea=idea)
                if not video_data or not script:
                    st.error("Failed to generate initial script/code from Gemini.")
                    return

            # audio gen 
            with st.spinner("🎙️ Step 2/4: Generating narration..."):
                try:
                    # Use a unique name to avoid caching issues between runs
                    audio_file = generate_audio(script, f"initial_audio_{hash(script)}.mp3")
                except Exception as e:
                    st.warning(f"Could not generate audio: {e}. Proceeding without audio.")
                    audio_file = None

            current_manim_code = video_data["manim_code"]
            current_script = script
            current_audio_file = audio_file

            # video gen with retery loop 
            for attempt in range(max_retries + 1):
                try:
                    spinner_text = f"🎬 Step 3/4: Rendering video (Attempt {attempt + 1})..."
                    with st.spinner(spinner_text):
                        logging.info(f"Attempt {attempt + 1} to create Manim video.")
                        final_video = create_manim_video(
                            {"manim_code": current_manim_code, "output_file": "output.mp4"},
                            current_manim_code,
                            audio_file=current_audio_file
                        )
                    logging.info("Manim video creation successful.")
                    break  # Exit the loop on success

                except subprocess.CalledProcessError as e:
                    logging.error(f"Manim execution failed on attempt {attempt + 1}.")
                    stderr_output = e.stderr.decode() if e.stderr else 'No stderr captured.'
                    st.warning(f"Attempt {attempt + 1} failed. Manim error detected.")

                    if attempt < max_retries:
                        st.info("🤖 Step 4/4: AI is attempting to fix the code...")
                        with st.spinner("Fixing code with fallback model..."):
                            fixed_video_data, fixed_script = fix_manim_code(
                                faulty_code=current_manim_code,
                                error_message=stderr_output,
                                original_context=idea
                            )

                        if fixed_video_data and fixed_script:
                            st.info("Code fixed! Retrying video generation...")
                            current_manim_code = fixed_video_data["manim_code"]

                            if fixed_script.strip() != current_script.strip():
                                st.info("Narration was updated. Regenerating audio...")
                                current_script = fixed_script
                                try:
                                    # Use a unique name for the fixed audio file
                                    current_audio_file = generate_audio(current_script, f"fixed_audio_{attempt}.mp3")
                                except Exception as audio_err:
                                    st.warning(f"Could not regenerate audio: {audio_err}. Retrying with previous audio.")
                        else:
                            st.error("AI fallback failed to fix the code. Stopping.")
                            st.session_state.error_message = f"Manim Error:\n```\n{stderr_output}\n```"
                            final_video = None
                            break
                    else:
                        st.error(f"Manim failed after {max_retries + 1} attempts. The final error was:")
                        st.code(stderr_output, language='bash')
                        st.session_state.error_message = "Video generation failed after multiple attempts."
                        final_video = None

                except Exception as e:
                    st.error(f"An unexpected error occurred during video creation: {str(e)}")
                    logging.exception("Unexpected error in video creation loop.")
                    st.session_state.error_message = f"An unexpected error occurred: {str(e)}"
                    final_video = None
                    break

            # store data 
            if final_video and os.path.exists(final_video):
                st.session_state.video_path = final_video
                st.session_state.script = current_script
                st.session_state.manim_code = current_manim_code
            else:
                if not st.session_state.error_message:
                    st.session_state.error_message = "Could not generate the final video file for an unknown reason."

        except Exception as e:
            st.error(f"An unexpected critical error occurred: {str(e)}")
            logging.exception("Unhandled exception in main generation block.")
            st.session_state.error_message = f"An unexpected critical error occurred: {str(e)}"
        finally:
            # deleting temporary files
            if audio_file and os.path.exists(audio_file):
                os.remove(audio_file)
            if current_audio_file and os.path.exists(current_audio_file) and current_audio_file != audio_file:
                os.remove(current_audio_file)


    # showing output 
    # This section reads from st.session_state 
    if st.session_state.video_path:
        st.success("🎉 Video generated successfully!")
        st.video(st.session_state.video_path)

        st.markdown("### Generation Details")
        tab1, tab2 = st.tabs(["📜 Narration Script", "💻 Manim Code"])

        with tab1:
            st.text_area(
                "Final Narration",
                st.session_state.script,
                height=250,
                key="narration_output",
                help="The final narration script used for the video's audio."
            )

        with tab2:
            st.code(st.session_state.manim_code, language='python', line_numbers=True)

    elif st.session_state.error_message:
        st.error(f"Could not generate the video. {st.session_state.error_message}")


    
    st.markdown("---")
    st.write("Made with ❤️ by rick")

if __name__ == "__main__":
    main()