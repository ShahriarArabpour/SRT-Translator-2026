import re
import sys

def fix_srt_direction(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    # Unicode Control Characters to strip
    # LRM: 200E, RLM: 200F, LRE: 202A, RLE: 202B, PDF: 202C
    chars_to_strip = '\u200e\u200f\u202a\u202b\u202c'
    
    # Right-to-Left Mark (Standard for fixing mixed text start)
    RLM = '\u200f'

    for line in lines:
        clean_line = line.strip()
        
        # Identify SRT components
        is_index = re.match(r'^\d+$', clean_line)
        is_timecode = re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', clean_line)
        
        if is_index or is_timecode or not clean_line:
            # Keep structure lines as is
            fixed_lines.append(line)
        else:
            # It's a text line
            # 1. Strip existing bad control chars
            text_content = clean_line.strip(chars_to_strip)
            
            # 2. Add RLM at the start
            # This forces the player to see the line as starting with an RTL char
            fixed_line = RLM + text_content + '\n'
            fixed_lines.append(fixed_line)
            
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    print(f"Fixed RTL direction in: {output_path}")

if __name__ == "__main__":
    fix_srt_direction(
        '/mnt/d/ag5-translator/output/test_video.srt',
        '/mnt/d/ag5-translator/output/test_video_fixed.srt'
    )
