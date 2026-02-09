import re
import sys

def fix_srt_cleanly(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    
    # Unicode Control Characters to aggressively strip
    # LRI (2066), PDI (2069), RLI (2067), FSI (2068)
    # LRM (200E), RLM (200F), LRE (202A), RLE (202B), PDF (202C)
    bad_chars = [
        '\u2066', '\u2069', '\u2067', '\u2068', 
        '\u200e', '\u200f', '\u202a', '\u202b', '\u202c'
    ]
    
    # RLE (Right-to-Left Embedding) start
    RLE = '\u202b'
    # PDF (Pop Directional Format) end
    PDF = '\u202c'

    for line in lines:
        clean_line = line.strip()
        
        # Identify SRT components
        is_index = re.match(r'^\d+$', clean_line)
        is_timecode = re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', clean_line)
        
        if is_index or is_timecode or not clean_line:
            fixed_lines.append(line)
        else:
            # It's a text line
            # 1. Aggressively strip ALL control chars to start fresh
            text_content = clean_line
            for char in bad_chars:
                text_content = text_content.replace(char, '')
            
            # 2. Wrap in RLE ... PDF
            # This is the "Nuclear Option" for bi-directional text
            fixed_line = RLE + text_content + PDF + '\n'
            fixed_lines.append(fixed_line)
            
    # Save with UTF-8-SIG (BOM) for Windows/PotPlayer compatibility
    with open(output_path, 'w', encoding='utf-8-sig') as f:
        f.writelines(fixed_lines)
    print(f"Fixed (RLE+PDF wrapped) SRT saved to: {output_path}")

if __name__ == "__main__":
    fix_srt_cleanly(
        '/mnt/d/ag5-translator/output/test_video_clean.srt', # Use the existing clean file as input
        '/mnt/d/ag5-translator/output/test_video_final_bom.srt'
    )
