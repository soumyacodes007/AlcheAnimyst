import re
import os
import pathlib
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import pypdf  

# This line reads your .env file
load_dotenv()


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


SYSTEM_PROMPT = """CRITICAL MANIM INSTRUCTIONS: You are an expert programmer for Manim Community version v0.19.0 and later. Your code must strictly adhere to the modern API. DO NOT USE DEPRECATED FUNCTIONS. Specifically, for coordinate transformations on Axes, you must use axes.c2p(x, y) and axes.p2c(point); avoid old methods like i2gp, n2p, and p2n entirely. For creating animations that dynamically change based on a ValueTracker, you must use always_redraw to regenerate the object each frame, for example: dynamic_plot = always_redraw(lambda: axes.plot(...)). NEVER use add_updater to modify a plot's shape, and do not invent attributes like .unknowndimension. All configuration should be done directly in object constructors, not with a CONFIG dictionary. Finally, do not use outdated scene types like GraphScene; instead, create an Axes object within a standard Scene
Core Requirements:
- **API Version:** Use only Manim Community v0.19.0 API.
- **Vectors & Math:** Use 3D vectors (`np.array([x, y, 0])`) and ensure correct math operations.
- **Allowed Methods:** Strictly use the verified list of Manim methods provided in the detailed instructions. No external images.
- **        "\n   - self.play(), self.wait(), Create(), Write(), Transform(), FadeIn(), FadeOut(), Add(), Remove(), MoveAlongPath(), Rotating(), Circumscribe(), Indicate(), FocusOn(), Shift(), Scale(), MoveTo(), NextTo(), Axes(), Plot(), LineGraph(), BarChart(), Dot(), Line(), Arrow(), Text(), Tex(), MathTex(), VGroup(), Mobject.animate, self.camera.frame.animate"
- **Matrix Visualization:** Use `MathTex` for displaying matrices in the format `r'\\begin{bmatrix} a & b \\\\ c & d \\end{bmatrix}'`.
- **Duration:** The total animation duration MUST be exactly 30 seconds.
-**Error handling**:"An unexpected error occurred during video creation: No Scene class found in generated code, This error SHOULD NEVER occur. Make sure to validate the code before returning it. If this error occurs, please log the error and return None for both manim_code and narration.Make sure you don't do 3Dscene coz that gives this error"
- **Engagement:** Create visually stunning and crazy animations that push creative boundaries. Use vibrant colors, dynamic movements, and unexpected transformations.
- **Text Handling:** Fade out text and other elements as soon as they are no longer needed, ensuring a smooth transition.
- **Synchronization:** Align animation pacing (`run_time`, `wait`) roughly with the narration segments.
- **Output Format:** Return *only* the Python code and narration script, separated by '### MANIM CODE:' and '### NARRATION:' delimiters. Adhere strictly to this format.
- **Code Quality:** Generate error-free, runnable code with necessary imports (`from manim import *`, `import numpy as np`) and exactly one Scene class. Validate objects and animation calls.
"""


base_prompt_instructions = (
        "\nFollow these requirements strictly:"
        "\n1. Use only Manim Community v0.19.0 API"
        "\n2. Vector operations:"
        "\n   - All vectors must be 3D: np.array([x, y, 0])"
        "\n   - Matrix multiplication: result = np.dot(matrix, vector[:2])"
        "\n   - Append 0 for Z: np.append(result, 0)"
        "\n3. Matrix visualization:"
        "\n   - Use MathTex for display"
        "\n   - Format: r'\\begin{bmatrix} a & b \\\\ c & d \\end{bmatrix}'"
        "\n4. Use only verified Manim methods:"
        "\n   - self.play(), self.wait(), Create(), Write(), Transform(), FadeIn(), FadeOut(), Add(), Remove(), MoveAlongPath(), Rotating(), Circumscribe(), Indicate(), FocusOn(), Shift(), Scale(), MoveTo(), NextTo(), Axes(), Plot(), LineGraph(), BarChart(), Dot(), Line(), Arrow(), Text(), Tex(), MathTex(), VGroup(), Mobject.animate, self.camera.frame.animate"
        "\n5. DO NOT USE IMAGES IMPORTS."
        "\n6. Make the video crazy and innovative by:"
        "\n   - Fading out text and other elements gracefully once they are no longer needed"
        "\n   - Adding creative interactive elements like arrows, labels, and transitions"
        "\n   - Incorporating graphs/plots (Axes, Plot, LineGraph, BarChart) where appropriate"
        "\n   - Leveraging smooth transitions and varied pacing to keep the viewer engaged."
        "\n7. Ensure the video is error-free by:"
        "\n   - Validating all objects before animations"
        "\n   - Handling exceptions gracefully (in generated code if applicable)"
        "\n   - Ensuring operands for vector operations match in shape to avoid broadcasting errors"
        "\n8. Validate that every arrow creation ensures its start and end points are distinct to prevent normalization errors."
        "\n9. Use longer scenes (e.g., 5-6 seconds per major step) for complex transformations and shorter scenes for simple animations, with a total duration of exactly 30 seconds."
        "\n10. Align the narration script with the animation pace for seamless storytelling."
        "\n11. Ensure all objects in self.play() are valid animations (e.g., `Create(obj)`, `obj.animate.shift(UP)`)."
        "\n12. Use Mobject.animate for animations involving Mobject methods."
        "\n13. CRITICAL: DO NOT USE BARCHATS, LINEGRAPHS, OR PLOTTING WITHOUT EXPLICIT INSTRUCTIONS."
        "\n14. Provide creative and sometimes crazy Manim video scripts that push the conventional boundaries."
        "\n15. **Synchronization:** Structure the narration and Manim code for better synchronization:"
        "\n    - Keep narration segments concise and directly tied to the visual elements."
        "\n    - Use `self.wait(duration)` in the Manim code to match natural pauses in narration."
        "\n    - Adjust `run_time` in `self.play()` calls to match the speaking duration of the associated narration."
        "\n    - Ensure the animation and narration sum to exactly 30 seconds."
        "\n### MANIM CODE:\n"
        "Provide only valid Python code using Manim Community v0.19.0 to generate the video animation.\n\n"
        "### NARRATION:\n"
        "Provide a concise narration script for the video that aligns with the Manim code's pacing and visuals.DO NOT give timestamps.\n\n"
    )


def load_manim_examples():
    """Loads Manim example code from rules.md."""
    guide_path = pathlib.Path(__file__).parent / "rules.md"
    if not guide_path.exists():
        logging.warning(f"Manim examples guide not found at {guide_path}")
        return ""
    
    logging.info(f"Loading Manim examples from {guide_path}")
    return guide_path.read_text(encoding="utf-8")


def generate_video(idea: str | None = None, pdf_path: str | None = None):
    """
    Generates a Manim script and narration using the Alchemyst AI API.
    """
    api_key = os.getenv("ALCHEMYST_API_KEY")
    if not api_key:
        logging.error("ALCHEMYST_API_KEY not found in environment variables. Please check your .env file.")
        raise Exception("ALCHEMYST_API_KEY not found in environment variables.")

    if not idea and not pdf_path:
        raise ValueError("Either an idea or a pdf_path must be provided.")
    if idea and pdf_path:
        logging.warning("Both idea and pdf_path provided. Using pdf_path as the primary source.")
        idea = None
    
    # --- Prompt Construction ---
    human_prompt_parts = []
    
    manim_examples = load_manim_examples()
    if manim_examples:
        examples_prompt = "Below are examples of Manim code that demonstrate proper usage patterns. Use these as a reference:\n\n" + manim_examples
        human_prompt_parts.append(examples_prompt)
        logging.info("Added Manim examples from rules.md to prime the model.")
    else:
        logging.warning("No Manim examples were loaded from rules.md.")
    
    user_request_text = ""

    if pdf_path:
        pdf_file_path = pathlib.Path(pdf_path)
        if not pdf_file_path.exists():
            logging.error(f"PDF file not found at: {pdf_path}")
            raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

        logging.info(f"Reading and extracting text from PDF: {pdf_path}")
        try:
            reader = pypdf.PdfReader(pdf_file_path)
            pdf_text = "".join(page.extract_text() or "" for page in reader.pages)
            
            if not pdf_text.strip():
                logging.error("Could not extract any text from the PDF. It might be image-based or corrupted.")
                raise ValueError("Could not extract any text from the provided PDF.")
            
            user_request_text = (
                "Create a 30-second Manim video script summarizing the key points or illustrating a core concept "
                f"from the document content below.\n\n--- DOCUMENT CONTENT ---\n{pdf_text}\n--- END DOCUMENT CONTENT ---\n\n"
                f"{base_prompt_instructions}"
            )
        except Exception as e:
            logging.error(f"Failed to read or process PDF file: {e}")
            raise

    elif idea:
        logging.info(f"Generating video based on idea: {idea[:50]}...")
        user_request_text = f"Create a 30-second Manim video script about '{idea}'. {base_prompt_instructions}"

    human_prompt_parts.append(user_request_text)
    final_human_prompt = "\n\n".join(human_prompt_parts)
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=final_human_prompt),
    ]

    # api call for alchemyst ai
    logging.info("Sending request to Alchemyst AI API...")
    try:
        llm = ChatOpenAI(
            api_key=api_key,
            model="alchemyst-ai/alchemyst-c1",
            base_url="https://platform-backend.getalchemystai.com/api/v1/proxy/default",
        )
        response = llm.invoke(messages)
        content = response.content
        logging.info("Received response from Alchemyst AI.")

    except Exception as e:
        logging.exception(f"An error occurred while calling the Alchemyst AI API: {e}")
        raise Exception(f"An error occurred while calling the Alchemyst AI API: {e}")

    if not content:
        logging.error("The API returned an empty response.")
        raise Exception("The API returned an empty response.")

    
    if "### NARRATION:" in content:
        manim_code, narration = content.split("### NARRATION:", 1)
        manim_code = re.sub(r"```python", "", manim_code).replace("```", "").strip()
        narration = narration.strip()
        logging.info("Successfully parsed code and narration using '### NARRATION:' delimiter.")
    else:
        logging.warning("Delimiter '### NARRATION:' not found. Attempting fallback extraction.")
        code_match = re.search(r'```python(.*?)```', content, re.DOTALL)
        if not code_match:
            logging.error("Fallback extraction failed: No Python code block found in response.")
            logging.debug(f"Content received from API:\n{content}")
            raise Exception("The response does not contain a valid Python code block.")
        
        manim_code = code_match.group(1).strip()
        # Assume text after the code block is narration
        narration_part = content.split(code_match.group(0), 1)[1]
        narration = narration_part.strip()
        if not narration:
            logging.warning("Fallback narration extraction resulted in empty text.")
        else:
            logging.info("Successfully parsed code and narration using fallback regex.")

    # clean up 
    if "from manim import *" not in manim_code:
        logging.warning("Adding missing 'from manim import *'.")
        manim_code = "from manim import *\nimport numpy as np\n" + manim_code
    elif "import numpy as np" not in manim_code:
        logging.warning("Adding missing 'import numpy as np'.")
        lines = manim_code.splitlines()
        for i, line in enumerate(lines):
            if "from manim import *" in line:
                lines.insert(i + 1, "import numpy as np")
                manim_code = "\n".join(lines)
                break
    
    return {"manim_code": manim_code, "output_file": "output.mp4"}, narration