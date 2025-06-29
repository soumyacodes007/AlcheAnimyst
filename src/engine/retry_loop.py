

import os
import re
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


try:
    from .alchymist_ai import SYSTEM_PROMPT, base_prompt_instructions 
except ImportError:
    
    
    logging.warning("Could not perform relative import. Using placeholder prompts.")
    SYSTEM_PROMPT = "You are a Manim expert. Fix the user's code."
    base_prompt_instructions = "Follow all Manim Community v0.19.0 rules."


load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def fix_manim_code(faulty_code: str, error_message: str, original_context: str):
    """
    Attempts to fix faulty Manim code using the Alchemyst AI API.
    """
    
    api_key = os.getenv("ALCHEMYST_API_KEY")
    if not api_key:
        logging.error("ALCHEMYST_API_KEY not found in environment variables for fallback.")
        return None, None

    # Initialize Alchemyst AI
    llm = ChatOpenAI(
        api_key=api_key,
        model="alchemyst-ai/alchemyst-c1",
        base_url="https://platform-backend.getalchemystai.com/api/v1/proxy/default",
        temperature=0.4,  # Lower temperature for precise code fixing
    )

    # 
    fix_prompt_text = (
        f"The following Manim code, intended to '{original_context}', failed with an error.\n\n"
        "### FAULTY CODE:\n"
        f"```python\n{faulty_code}\n```\n\n"
        "### ERROR MESSAGE:\n"
        f"```\n{error_message}\n```\n\n"
        "### INSTRUCTIONS:\n"
        "1. Analyze the error message and the faulty code.\n"
        "2. Correct the code to fix the specific error reported.\n"
        "3. Ensure the corrected code still fulfills the original request and adheres strictly to *all* the requirements listed below.\n"
        "4. Pay close attention to vector dimensions, matrix operations, allowed Manim methods, and total duration (30 seconds).\n"
        "5. If the code logic changes significantly, update the narration accordingly.\n"
        "6. Return *only* the corrected code and narration using the '### MANIM CODE:' and '### NARRATION:' delimiters, just like the original request.\n\n"
        "### REQUIREMENTS (Apply these to the corrected code):\n"
        f"{base_prompt_instructions}"
    )

    
    logging.info("Attempting to fix Manim code via Alchemyst AI fallback...")
    try:
        # Structure the messages for the API call
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": fix_prompt_text}
        ]
        
        response = llm.invoke(messages)
        content = response.content
        logging.info("Received response from fallback attempt.")

    except Exception as e:
        logging.exception(f"Error calling Alchemyst AI API during fallback: {e}")
        return None, None

    
    if "### NARRATION:" in content:
        manim_code, narration = content.split("### NARRATION:", 1)
        manim_code = re.sub(r"```python", "", manim_code).replace("```", "").strip()
        narration = narration.strip()
        logging.info("Successfully parsed fixed code and narration from fallback.")
    else:
        logging.warning("Delimiter '### NARRATION:' not found in fallback response. Attempting regex extraction.")
        code_match = re.search(r'```python(.*?)```', content, re.DOTALL)
        if code_match:
            manim_code = code_match.group(1).strip()
            narration_part = content.split('```', 2)[-1].strip()
            narration = narration_part if len(narration_part) > 20 else ""
            if not narration:
                logging.warning("Fallback narration extraction resulted in empty or very short text.")
            logging.info("Successfully parsed fixed code using fallback regex extraction.")
        else:
            logging.error("Fallback extraction failed: No Python code block found in response.")
            logging.debug(f"Fallback content without code block:\n{content}")
            return None, None

    # Ensure necessary imports are present
    if "from manim import *" not in manim_code:
        logging.warning("Adding missing 'from manim import *' (fallback fix).")
        manim_code = "from manim import *\nimport numpy as np\n" + manim_code
    elif "import numpy as np" not in manim_code:
        logging.warning("Adding missing 'import numpy as np' (fallback fix).")
        lines = manim_code.splitlines()
        for i, line in enumerate(lines):
            if "from manim import *" in line:
                lines.insert(i + 1, "import numpy as np")
                manim_code = "\n".join(lines)
                break

    return {"manim_code": manim_code, "output_file": "output.mp4"}, narration



if __name__ == "__main__":
    # Define an example of faulty code and the error it produces
    example_faulty_code = """
from manim import *
class MyFaultyScene(Scene):
    def construct(self):
        # This is wrong, Text expects a string
        my_text = Text(12345) 
        self.play(Write(my_text))
        self.wait(2)
"""
    example_error = "TypeError: text must be a string, not <class 'int'>"
    example_context = "A simple animation to display text on the screen."

    try:
        # Attempt to fix the code
        fixed_data, fixed_narration = fix_manim_code(
            faulty_code=example_faulty_code,
            error_message=example_error,
            original_context=example_context
        )
        
        if fixed_data:
            print("\n" + "="*50)
            print("CODE FIX SUCCESSFUL!")
            print("="*50)
            print("\n--- CORRECTED MANIM CODE ---\n")
            print(fixed_data["manim_code"])
            print("\n--- CORRECTED NARRATION ---\n")
            print(fixed_narration)
            print("\n" + "="*50)
        else:
            print("\n" + "="*50)
            print("COULD NOT FIX THE CODE.")
            print("="*50)

    except (ValueError, Exception) as e:
        logging.error(f"An error occurred during the fixing process: {e}")