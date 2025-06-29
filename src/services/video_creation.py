import re
import subprocess
import os
import glob
import logging

def get_scene_name(manim_code):
    match = re.search(r'class\s+(\w+)\s*\(\s*Scene\s*\)', manim_code)
    if match:
        return match.group(1)
    raise ValueError("No Scene class found in generated code")

def create_manim_video(video_data, manim_code, audio_file=None):
    logging.info("Starting to create Manim video")
    with open("generated_video.py", "w") as f:
        manim_code_clean = re.sub(r"```python", "", manim_code)
        manim_code_clean = manim_code_clean.replace("```", "").strip()
        f.write(manim_code_clean)
    
    scene_name = get_scene_name(manim_code_clean)
    logging.info(f"Identified scene name: {scene_name}")
    
    command = ["manim", "-qh", "generated_video.py", scene_name]
    logging.info(f"Running Manim with command: {' '.join(command)}")
    subprocess.run(command, check=True)
    
    search_pattern = os.path.join("media", "videos", "generated_video", "1080p60", f"{scene_name}.mp4")
    if not os.path.exists(search_pattern):
        logging.error(f"No rendered video found at: {search_pattern}")
        raise Exception(f"No rendered video found for scene {scene_name}")
    
    output_video = search_pattern
    final_output = "final_output.mp4"

    if audio_file and os.path.exists(audio_file):
        logging.info(f"Merging video with audio file: {audio_file}")
        
        video_duration_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
                             "-of", "default=noprint_wrappers=1:nokey=1", output_video]
        audio_duration_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
                             "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
        
        video_duration = float(subprocess.check_output(video_duration_cmd).decode('utf-8').strip())
        audio_duration = float(subprocess.check_output(audio_duration_cmd).decode('utf-8').strip())
        
        logging.info(f"Video duration: {video_duration}s, Audio duration: {audio_duration}s")
        
        if audio_duration > video_duration:
            logging.info("Audio is longer than video, extending video duration")
            extended_video = "extended_video.mp4"
            padding_time = audio_duration - video_duration
            
            extend_cmd = [
                "ffmpeg", "-y",
                "-i", output_video,
                "-f", "lavfi", "-i", "color=black:s=1920x1080:r=60",
                "-filter_complex", f"[0:v][1:v]concat=n=2:v=1:a=0[outv]",
                "-map", "[outv]",
                "-c:v", "libx264",
                "-t", str(audio_duration),
                extended_video
            ]
            
            logging.info(f"Extending video with command: {' '.join(extend_cmd)}")
            subprocess.run(extend_cmd, check=True)
            output_video = extended_video
        
        merge_cmd = [
            "ffmpeg", "-y",
            "-i", output_video,
            "-i", audio_file,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            final_output
        ]
        
        logging.info(f"Merging with command: {' '.join(merge_cmd)}")
        subprocess.run(merge_cmd, check=True)
        output_video = final_output
        
        if os.path.exists("extended_video.mp4"):
            os.remove("extended_video.mp4")
            logging.info("Removed temporary extended video file")

    if os.path.exists("generated_video.py"):
        os.remove("generated_video.py")
        logging.info("Removed generated_video.py")

    logging.info(f"Final video created at: {output_video}")
    return output_video
