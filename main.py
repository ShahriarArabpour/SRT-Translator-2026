import os
import json
import re
import time
import argparse
import logging
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONFIGURATION ---
INPUT_DIR = "input"
OUTPUT_DIR = "output"
INSTRUCTION_FILE = "instructions.md"
GLOSSARY_FILE = "glossary.json"

# --- ARGUMENT PARSING ---
def parse_args():
    parser = argparse.ArgumentParser(description="Translate SRT files using Google Gemini.")
    parser.add_argument("--model", type=str, default="gemini-2.5-flash", help="Gemini model name (e.g., gemini-2.0-flash, gemini-2.5-pro, gemini-2.5-flash)")
    parser.add_argument("--api_key", type=str, help="Google Gemini API Key (overrides env var)")
    return parser.parse_args()

# --- MODEL SETUP ---
def get_model(model_name, api_key_arg=None):
    api_key = api_key_arg or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("API Key is missing. Set GEMINI_API_KEY env var or pass --api_key.")
    
    genai.configure(api_key=api_key)
    
    generation_config = {
        "temperature": 0.2,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    logging.info(f"Using model: {model_name}")
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
        logging.error(f"File not found: {filepath}")
        return ""

def parse_srt(srt_content):
    """Parses SRT into a list of blocks. Includes ALL blocks, even empty ones."""
    blocks = re.split(r'\n\n+', srt_content.strip())
    parsed_blocks = []
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 2:  # At least index and timecode
            index = lines[0].strip()
            timecode = lines[1].strip() if len(lines) > 1 else ""
            text = " ".join(lines[2:]).strip() if len(lines) > 2 else ""
            # Include ALL blocks - even empty text ones
            parsed_blocks.append({"index": index, "timecode": timecode, "text": text})
    return parsed_blocks

def chunk_srt(blocks, chunk_size=30):
    """Chunks SRT blocks to fit into context window efficiently."""
    for i in range(0, len(blocks), chunk_size):
        yield blocks[i:i + chunk_size]

def build_prompt(instructions, glossary, subtitle_chunk):
    """Constructs the prompt for the LLM. Skips empty subtitle blocks."""
    
    srt_text = ""
    for block in subtitle_chunk:
        # Skip blocks with no text content (empty placeholders)
        if not block['text'].strip():
            continue
        srt_text += f"{block['index']}\n{block['timecode']}\n{block['text']}\n\n"
    
    # If all blocks were empty, return None
    if not srt_text.strip():
        return None

    prompt = f"""
{instructions}

## Glossary & ASR Corrections
Use these mappings as a strict reference:
{glossary}

## Task
Translate the following SRT block to Persian (Farsi).

**CRITICAL RULES:**
1. Maintain the EXACT same SRT format: Index number, Timecode, then translated Text.
2. Do NOT change the index numbers or timecodes - keep them EXACTLY as provided.
3. Fix ASR errors (e.g. 'lama index' -> 'LlamaIndex') as per instructions.
4. Translate ONLY the text content, not the index or timecode.
5. Output translated SRT ONLY. No markdown code blocks, no explanations.

## Source SRT Input:
{srt_text}

## Persian SRT Output:
"""
    return prompt

def post_process_rtl(srt_content):
    """
    Fixes RTL direction for Persian subtitles using RLE/PDF sandwich approach.
    
    Method:
    1. Clean all existing Unicode directional control characters
    2. Wrap each text line with RLE (\\u202B) at start and PDF (\\u202C) at end
    
    This is the industry standard for mixed RTL/LTR subtitle text.
    """
    # Unicode directional control characters
    RLE = '\u202B'  # Right-to-Left Embedding - forces RTL context
    PDF = '\u202C'  # Pop Directional Format - ends the RLE embedding
    
    # All Unicode directional characters to remove first
    chars_to_remove = [
        '\u200E',  # LRM - Left-to-Right Mark
        '\u200F',  # RLM - Right-to-Left Mark
        '\u202A',  # LRE - Left-to-Right Embedding
        '\u202B',  # RLE - Right-to-Left Embedding
        '\u202C',  # PDF - Pop Directional Format
        '\u202D',  # LRO - Left-to-Right Override
        '\u202E',  # RLO - Right-to-Left Override
        '\u2066',  # LRI - Left-to-Right Isolate
        '\u2067',  # RLI - Right-to-Left Isolate
        '\u2068',  # FSI - First Strong Isolate
        '\u2069',  # PDI - Pop Directional Isolate
    ]
    
    lines = srt_content.split('\n')
    fixed_lines = []

    for line in lines:
        clean_line = line.strip()
        
        # Skip empty lines, index numbers, and timecodes
        is_index = re.match(r'^\d+$', clean_line)
        is_timecode = re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', clean_line)
        
        if is_index or is_timecode or not clean_line:
            fixed_lines.append(line)
        else:
            # It's a text line
            # Step 1: Remove ALL existing directional control characters
            for char in chars_to_remove:
                clean_line = clean_line.replace(char, '')
            
            # Step 2: Apply RLE/PDF sandwich
            # Format: RLE + text + PDF
            fixed_lines.append(RLE + clean_line + PDF)
            
    return "\n".join(fixed_lines)

# --- MAIN LOGIC ---
def translate_file(filename, model, output_file_handle):
    """Translates file and writes directly to output handle (chunk by chunk)."""
    input_path = os.path.join(INPUT_DIR, filename)
    
    logging.info(f"Reading {input_path}...")
    srt_content = load_file(input_path)
    if not srt_content:
        logging.error(f"Input file not found or empty: {input_path}")
        return False

    instructions = load_file(INSTRUCTION_FILE)
    glossary = load_file(GLOSSARY_FILE)
    
    blocks = parse_srt(srt_content)
    logging.info(f"Found {len(blocks)} subtitle blocks.")
    
    chunk_size = 30  # Larger chunks for better context and translation quality
    chunks = list(chunk_srt(blocks, chunk_size))
    total_chunks = len(chunks)
    
    logging.info(f"Translating in {total_chunks} chunks...")
    
    start_time_total = time.time()
    
    for i, chunk in enumerate(chunks):
        logging.info(f"Processing chunk {i+1}/{total_chunks}...")
        
        prompt = build_prompt(instructions, glossary, chunk)
        
        # Skip chunks with no content (all empty placeholders)
        if prompt is None:
            logging.info(f"Chunk {i+1} is empty, skipping...")
            continue
        
        try:
            response = model.generate_content(prompt)
            translated_text = response.text.strip()
            
            # Clean markdown if present
            translated_text = translated_text.replace("```srt", "").replace("```", "").strip()

            if "-->" not in translated_text:
                logging.warning(f"Chunk {i+1} might be malformed")
            
            # Apply RTL fix to this chunk
            fixed_chunk = post_process_rtl(translated_text)
            
            # WRITE IMMEDIATELY to file (reduces memory)
            output_file_handle.write(fixed_chunk + "\n\n")
            output_file_handle.flush()  # Force write to disk
            
            logging.info(f"Chunk {i+1} saved successfully")
            
            time.sleep(1)
            
        except Exception as e:
            logging.error(f"Error translating chunk {i+1}: {e}")
            
    end_time_total = time.time()
    logging.info(f"Total translation time: {end_time_total - start_time_total:.2f} seconds.")
    
    return True

if __name__ == "__main__":
    # Ensure dirs exist
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    args = parse_args()

    try:
        model = get_model(args.model, args.api_key)
        
        files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".srt")]
        if not files:
            logging.warning(f"No .srt files found in '{INPUT_DIR}' directory.")
        else:
            target_file = files[0]
            output_path = os.path.join(OUTPUT_DIR, target_file)
            
            logging.info(f"Processing file: {target_file}")
            logging.info(f"Output will be: {output_path}")
            
            # Open output file FIRST, then translate chunk-by-chunk
            with open(output_path, 'w', encoding='utf-8-sig') as out_f:
                success = translate_file(target_file, model, out_f)
            
            if success:
                # Verify file was created
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    logging.info(f"SUCCESS! Output file created: {output_path} ({file_size} bytes)")
                else:
                    logging.error(f"FAILED! Output file not found: {output_path}")
            
            logging.info("Done!")
                
    except Exception as e:
        logging.exception(f"Critical Error: {e}")