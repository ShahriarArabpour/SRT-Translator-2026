import os
import json
import re
import time
import argparse
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

# Load .env
load_dotenv()

# --- CONFIGURATION ---
INPUT_DIR = "input"
OUTPUT_DIR = "output"
INSTRUCTION_FILE = "instructions.md"
GLOSSARY_FILE = "glossary.json"

# --- ARGUMENT PARSING ---
def parse_args():
    parser = argparse.ArgumentParser(description="Translate SRT files using Google Gemini.")
    parser.add_argument("--model", type=str, default="gemini-2.5-pro", help="Gemini model name (e.g., gemini-2.0-flash, gemini-2.5-pro)")
    parser.add_argument("--api_key", type=str, help="Google Gemini API Key (overrides env var)")
    return parser.parse_args()

# --- MODEL SETUP ---
def get_model(model_name, api_key_arg=None):
    api_key = api_key_arg or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("API Key is missing. Set GEMINI_API_KEY env var or pass --api_key.")
    
    genai.configure(api_key=api_key)
    
    generation_config = {
        "temperature": 0.2, # Low temperature for consistent translation
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    
    # Safety settings
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    print(f"Using model: {model_name}")
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config,
        safety_settings=safety_settings,
    )
    return model

# --- UTILS ---
def load_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Required file not found: {filepath}")
        return ""

def parse_srt(srt_content):
    """Parses SRT into a list of blocks."""
    blocks = re.split(r'\n\n+', srt_content.strip())
    parsed_blocks = []
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            index = lines[0].strip()
            timecode = lines[1].strip()
            text = " ".join(lines[2:]).strip()
            parsed_blocks.append({"index": index, "timecode": timecode, "text": text})
    return parsed_blocks

def chunk_srt(blocks, chunk_size=30):
    """Chunks SRT blocks to fit into context window efficiently."""
    for i in range(0, len(blocks), chunk_size):
        yield blocks[i:i + chunk_size]

def build_prompt(instructions, glossary, subtitle_chunk):
    """Constructs the prompt for the LLM."""
    
    srt_text = ""
    for block in subtitle_chunk:
        srt_text += f"{block['index']}\n{block['timecode']}\n{block['text']}\n\n"

    prompt = f"""
{instructions}

## Glossary & ASR Corrections
Use these mappings as a strict reference:
{glossary}

## Task
Translate the following SRT block to Persian (Farsi).
- Maintain the exact same SRT format (Index, Timecode, Text).
- Do NOT change the timecodes.
- Fix ASR errors (e.g. 'lama index' -> 'LlamaIndex') as per instructions.
- Ensure sentences flow naturally even if split across lines.
- Only output the translated SRT content. No markdown code blocks like ```srt or ```.

## Source SRT Input:
{srt_text}

## Persian SRT Output:
"""
    return prompt

def post_process_rtl(srt_content):
    """
    Programmatically fixes RTL direction for Persian subtitles.
    Adds RLM (\u200f) to the start of every text line to force RTL rendering
    even if the line starts with an English word.
    """
    lines = srt_content.split('\n')
    fixed_lines = []
    # Unicode chars to strip (LRM, RLM, LRE, RLE, PDF)
    chars_to_strip = '\u200e\u200f\u202a\u202b\u202c'
    RLM = '\u200f'

    for line in lines:
        clean_line = line.strip()
        
        # Check if line is Index or Timecode
        is_index = re.match(r'^\d+$', clean_line)
        is_timecode = re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', clean_line)
        
        if is_index or is_timecode or not clean_line:
            fixed_lines.append(line)
        else:
            # It's a text line
            # 1. Clean existing marks
            content = clean_line.strip(chars_to_strip)
            # 2. Force RLM at start
            fixed_lines.append(RLM + content)
            
    return "\n".join(fixed_lines)

# --- MAIN LOGIC ---
def translate_file(filename, model):
    input_path = os.path.join(INPUT_DIR, filename)
    output_path = os.path.join(OUTPUT_DIR, filename)
    
    print(f"Reading {input_path}...")
    srt_content = load_file(input_path)
    if not srt_content:
        return

    instructions = load_file(INSTRUCTION_FILE)
    glossary = load_file(GLOSSARY_FILE)
    
    blocks = parse_srt(srt_content)
    print(f"Found {len(blocks)} subtitle blocks.")
    
    translated_srt = ""
    chunk_size = 20 # Smaller chunk size for better stability in translation
    
    chunks = list(chunk_srt(blocks, chunk_size))
    total_chunks = len(chunks)
    
    print(f"Translating in {total_chunks} chunks...")
    
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{total_chunks}...")
        
        prompt = build_prompt(instructions, glossary, chunk)
        
        try:
            response = model.generate_content(prompt)
            translated_text = response.text.strip()
            
            # Clean up markdown code blocks if the model adds them
            translated_text = translated_text.replace("```srt", "").replace("```", "").strip()

            # Validation
            if "-->" not in translated_text:
                print(f"Warning: Chunk {i+1} output might be malformed.")
            
            translated_srt += translated_text + "\n\n"
            
            time.sleep(1) # Rate limit nice-ness
            
        except Exception as e:
            print(f"Error translating chunk {i+1}: {e}")
            
    # --- POST PROCESSING (RTL FIX) ---
    print("Applying RTL direction fix...")
    final_srt = post_process_rtl(translated_srt)

    print(f"Saving translation to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_srt)
    print("Done!")

if __name__ == "__main__":
    # Ensure dirs exist
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    args = parse_args()

    try:
        model = get_model(args.model, args.api_key)
        
        files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".srt")]
        if not files:
            print(f"No .srt files found in '{INPUT_DIR}' directory.")
        else:
            for f in files:
                translate_file(f, model)
                
    except Exception as e:
        print(f"Critical Error: {e}")
