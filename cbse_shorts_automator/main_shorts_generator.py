#!/usr/bin/env python3
"""
File: main_shorts_generator.py
Main orchestrator for generating YouTube Shorts from Google Sheets
Updated: 
- Writes Metadata (Filename, Template, Duration) to Columns AR, AS, AT.
- Batch processing ready.
"""

import imagemagick_setup
import os
import sys
import json
import time
import re
import requests
import fitz
import random
import gc 

#from google.auth.transport.requests import Request
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import google.generativeai as genai

from shorts_engine import ShortsEngine, generate_random_config
from voice_manager import VoiceManager
from prompt_manager import PromptManager  # <--- NEW IMPORT

CONFIG_FILE = "config/generator_config.json"

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

CONFIG = load_config()
DIRS = CONFIG['DIRS']

# Load column indices
COL_MAPPING = CONFIG.get('COLUMN_MAPPING', {})
COL_IDX_CLASS = COL_MAPPING.get('COL_INDEX_CLASS', 1)
COL_IDX_PDF = COL_MAPPING.get('COL_INDEX_PDF', 5)
COL_IDX_CHAPTER = COL_MAPPING.get('COL_INDEX_CHAPTER', 8)
COL_IDX_FILTER = COL_MAPPING.get('COL_INDEX_FILTER', 12)
COL_IDX_ID = COL_MAPPING.get('COL_INDEX_ID', 13)
COL_IDX_TOPIC = COL_MAPPING.get('COL_INDEX_TOPIC', 18)
COL_IDX_VIDEO = COL_MAPPING.get('COL_INDEX_VIDEO', 24)
COL_IDX_STATUS = COL_MAPPING.get('COL_INDEX_STATUS', 39)
COL_IDX_VOICE = COL_MAPPING.get('COL_INDEX_VOICE_SYSTEM', 49)

# NEW: Metadata Columns (AR=43, AS=44, AT=45)
COL_IDX_FILENAME = COL_MAPPING.get('COL_INDEX_FILENAME', 43)
COL_IDX_TEMPLATE = COL_MAPPING.get('COL_INDEX_TEMPLATE', 44)
COL_IDX_DURATION = COL_MAPPING.get('COL_INDEX_DURATION', 45)

STOP_WORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'this', 'that', 'it', 'to', 'for', 'with', 'on', 'in', 'of',
    'and', 'or', 'but', 'so', 'because', 'if', 'then', 'else', 'when', 'where', 'how', 'why', 'who', 'which',
    'friends', 'students', 'champs', 'guys', 'kids', 'buddies', 'pals',
    'learners', 'explorers', 'scientists', 'scholars', 'brainiacs', 'geniuses', 
    'detectives', 'achievers', 'warriors', 'thinkers', 'creators', 'inventors',
    'hero', 'heroes', 'class', 'grade', 'batch'
}
def authenticate(scopes, token_filename, service_name):
    """ Authenticates with Google APIs using the manual input flow. """
    print(f"\n--- AUTHENTICATION: {service_name} ---")
    
    creds = None
    
    # 1. Check for existing token
    if os.path.exists(token_filename):
        try:
            creds = Credentials.from_authorized_user_file(token_filename, scopes)
            if set(scopes) != set(creds.scopes):
                 print(f"WARNING: Existing {service_name} token scopes mismatch. Forcing re-authorization.")
                 creds = None 
            else:
                print(f"Reusing existing {service_name} credentials.")
        except Exception as e:
            print(f"WARNING: Failed to load {service_name} token file ({e}). Starting new authorization.")
            if os.path.exists(token_filename): os.remove(token_filename)
            creds = None

    # 2. If no valid token, initiate the flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Credentials expired. Attempting to refresh token.")
            try:
                creds.refresh(google.auth.transport.requests.Request())
            except Exception as e:
                print(f"WARNING: Token refresh failed ({e}). Starting new authorization.")
                creds = None
        
        if not creds or not creds.valid:
            print(f"Initiating NEW {service_name} authorization flow (Manual Code Input).")
            flow = InstalledAppFlow.from_client_secrets_file(CONFIG['CREDENTIALS_FILE'], scopes)
            # Use out-of-band flow for manual copy-paste
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
            
            auth_url, _ = flow.authorization_url(prompt='consent')

            print("\n=======================================================")
            print(f"  CRITICAL AUTHORIZATION STEP REQUIRED: {service_name.upper()}")
            print("=======================================================")
            print("1. Please visit this URL in your browser:")
            print(f"\n{auth_url}\n")
            print("2. Log in with your email and approve access.")
            print("3. Paste the authorization code below:")
            
            code = input("Enter the authorization code: ").strip()
            
            try:
                flow.fetch_token(code=code)
                creds = flow.credentials
            except Exception as e:
                print(f"FATAL AUTH ERROR: Failed to exchange code for token. Error: {e}")
                sys.exit(1)
            
        # 3. Save the credentials
        with open(token_filename, 'w') as token:
            token.write(creds.to_json())
            print(f"New or refreshed token saved to {token_filename}.")

    return creds

#def get_sheets_service():
#    creds = None
#    token_file = CONFIG['SHEETS_TOKEN_FILE']
#    if os.path.exists(token_file):
#        creds = Credentials.from_authorized_user_file(token_file, CONFIG['SHEETS_SCOPES'])
#    if not creds or not creds.valid:
#        if creds and creds.expired and creds.refresh_token:
#           creds.refresh(Request())
#        else:
#            flow = InstalledAppFlow.from_client_secrets_file(CONFIG['CREDENTIALS_FILE'], CONFIG['SHEETS_SCOPES'])
#            creds = flow.run_local_server(port=0)
#        with open(token_file, 'w') as token:
#            token.write(creds.to_json())
#    return build('sheets', 'v4', credentials=creds)

def get_col_letter(n):
    """Converts 0-based index to A, B, ... AA, AB format"""
    s = ""
    while n >= 0:
        s = chr(n % 26 + 65) + s
        n = n // 26 - 1
    return s

class GeminiManager:
    def __init__(self):
        self.keys = [line.strip() for line in open(CONFIG['GEMINI_KEYS_FILE']) if line.strip()]
        self.idx = 0
        self.prompter = PromptManager() # Initialize Prompter
        self._configure()

    def _configure(self):
        if self.idx < len(self.keys):
            genai.configure(api_key=self.keys[self.idx])
        else:
            raise Exception("All Gemini keys exhausted")

    def get_script(self, pdf_text, class_level=None, template='quiz'):
        prompt = self.prompter.create_prompt(pdf_text, class_level, template)

        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
        ]

        gen_config = genai.types.GenerationConfig(
            temperature=0.9, 
            max_output_tokens=4096 
        )
        
        models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.0-flash-exp']
        
        for m in models:
            try:
                model = genai.GenerativeModel(m)
                res = model.generate_content(prompt, generation_config=gen_config, safety_settings=safety_settings)
                # Check if we have valid parts before accessing .text
                #if res.candidates[0].content.parts:
                #    print(res.text)
                if not res.text:
                    raise Exception(f"Blocked by filters. Finish Reason: {res.candidates[0].finish_reason}")

                clean_json = res.text.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean_json)
                
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed[0]
                return parsed
                
            except Exception as e:
                print(f"⚠️ Gemini error with {m}: {e}")
                if "429" in str(e) or "quota" in str(e).lower():
                    self.idx += 1
                    self._configure()
        
        raise Exception("Gemini generation failed")

def normalize_filename_part(text, max_len):
    if not text: return 'untitled'[:max_len]
    safe = ''.join(c if c.isalnum() else '_' for c in text.lower())
    safe = re.sub(r'_+', '_', safe).strip('_')
    if not safe: safe = 'content'
    return safe[:max_len]

def parse_class_level(text):
    if not text: return None
    match = re.search(r'\d+', text)
    if match: return int(match.group())
    roman_map = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10, 'xi': 11, 'xii': 12}
    clean = text.lower().replace('class', '').replace('grade', '').strip()
    return roman_map.get(clean, 9)

def extract_keyword_from_explanation(script, max_len=8):
    text = script.get('explanation_spoken', '') + ' ' + script.get('fact_details', '') + ' ' + script.get('tip_content', '')
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    for word in words:
        if word not in STOP_WORDS: return word[:max_len]
    return 'content'[:max_len]

def format_column_n(value):
    try:
        num = int(float(value))
        return str(num).zfill(4)
    except:
        return '0000'

def find_next_version(output_dir, base_filename):
    version = 1
    while os.path.exists(os.path.join(output_dir, f"{base_filename}_V{version}.mp4")):
        version += 1
    return version

def generate_output_filename(chapter_title, template_type, script, col_n_value, output_dir):
    chapter = normalize_filename_part(chapter_title, max_len=10)
    type_short = template_type[:5].lower()
    
    # === CHANGED: Priority Logic for Keyword ===
    # 1. Check if AI provided a specific slug (Smartest)
    if 'filename_slug' in script and script['filename_slug']:
        keyword = normalize_filename_part(script['filename_slug'], max_len=12)
    # 2. Fallback to extracting from text (Old method)
    else:
        keyword = extract_keyword_from_explanation(script, max_len=8)
    # ===========================================

    col_n = format_column_n(col_n_value)
    base = f"{chapter}_{type_short}_{keyword}_{col_n}"
    version = find_next_version(output_dir, base)
    return f"{base}_V{version}.mp4"

def download_file(url, save_path):
    headers = {'User-Agent': 'Mozilla/5.0'}
    retries = CONFIG.get('API_RETRY_ATTEMPTS', 3)
    for attempt in range(retries):
        try:
            if attempt > 0:
                print(f"   ⏳ Retry {attempt+1}/{retries} for PDF...")
                time.sleep(2)
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code == 200:
                with open(save_path, 'wb') as f: f.write(r.content)
                return True
        except Exception as e:
            print(f"   ❌ PDF Error: {e}")
    return False

def download_drive_video(url, output_path):
    try:
        print(f"⬇️ Downloading Video...")
        patterns = [r'/d/([a-zA-Z0-9_-]+)', r'id=([a-zA-Z0-9_-]+)']
        file_id = None
        for p in patterns:
            match = re.search(p, url)
            if match:
                file_id = match.group(1)
                break
        if not file_id: return False

        DL_URL = "https://drive.google.com/uc?export=download"
        session = requests.Session()
        response = session.get(DL_URL, params={'id': file_id}, stream=True)
        token = None
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                token = value
                break
        if token:
            response = session.get(DL_URL, params={'id': file_id, 'confirm': token}, stream=True)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(32768):
                    if chunk: f.write(chunk)
            return True
        return False
    except Exception: return False

def process_row(engine, gemini, row, row_idx):
    def get_c(i): return row[i].strip() if len(row) > i else ""
    
    vid_id = get_c(COL_IDX_ID)
    chapter_title = get_c(COL_IDX_CHAPTER)
    video_title = get_c(COL_IDX_TOPIC)
    pdf_url = get_c(COL_IDX_PDF)
    vid_url = get_c(COL_IDX_VIDEO)
    
    if not vid_id: return False, {"status": "Skipped: Column N empty"}
    
    class_str = get_c(COL_IDX_CLASS)
    class_level = parse_class_level(class_str)
    
    print(f"\n🎬 Processing Row {row_idx} [ID: {vid_id}]...")
    
    temp_pdf = os.path.join(DIRS['DOWNLOADS_PDF'], f"t_{vid_id}.pdf")
    temp_vid = os.path.join(DIRS['DOWNLOADS_VID'], f"t_{vid_id}.mp4")

    try:
        if not download_file(pdf_url, temp_pdf): raise Exception("PDF download failed")
        
        doc = fitz.open(temp_pdf)
        pdf_text = "".join([page.get_text() for page in doc])
        pdf_text = re.sub(r'\n+', '\n', pdf_text)
        
        if len(pdf_text) < 50: raise Exception("PDF empty")
        
        if not download_drive_video(vid_url, temp_vid): raise Exception("Video download failed")
        
        gen_config = generate_random_config(class_level=class_level)
        print(f"   🎨 Template: {gen_config['template'].upper()}")

        print("🤖 Generating AI script...")
        script = gemini.get_script(
            pdf_text, 
            class_level=class_level,
            template=gen_config['template']
        )
        
        # Preview
        if gen_config['template'] == 'quiz': preview = script.get('question_text', '')
        elif gen_config['template'] == 'fact': preview = script.get('fact_title', '')
        else: preview = script.get('tip_title', '')
        print(f"   ✅ Script: {preview[:50]}...")
        
        output_filename = generate_output_filename(
            chapter_title, gen_config['template'], script, vid_id, DIRS['SHORTS_OUT']
        )
        output_path = os.path.join(DIRS['SHORTS_OUT'], output_filename)
        
        result = engine.generate_short(
            video_path=temp_vid,
            pdf_path=temp_pdf,
            script=script,
            config=gen_config,
            output_path=output_path,
            class_level=class_level
        )

        if result['success']:
            print(f"✅ Created: {output_filename}")
            # Get voice system used
            voice_system_used = engine.voice_manager.last_used_system or "Unknown"
            
            # Return full metadata for Sheet update
            meta_data = {
                "status": CONFIG['STATUS_SUCCESS'],
                "filename": output_filename,
                "template": gen_config['template'],
                "duration": int(result.get('duration', 0)),
                "voice_system": voice_system_used  # ADD THIS LINE
            }
            return True, meta_data
        else:
            raise Exception(result.get('error', 'Unknown error'))

    except Exception as e:
        print(f"❌ Error: {e}")
        return False, {"status": f"{CONFIG['STATUS_FAILURE_PREFIX']} {str(e)}"}
    
    finally:
        if CONFIG.get('DELETE_TEMP_FILES', True):
            for p in [temp_pdf, temp_vid]:
                if os.path.exists(p): os.remove(p)
        gc.collect()

def main():
    for d in DIRS.values(): os.makedirs(d, exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    
    print("🚀 Starting NCERT QuickPrep Shorts Generator")
    # --- CHANGED SECTION START ---
    # Use the new authenticate function
    sheets_creds = authenticate(
        CONFIG['SHEETS_SCOPES'], 
        CONFIG['SHEETS_TOKEN_FILE'], 
        "Google Sheets"
    )
    
    # Build the service object using the credentials
    sheets = build('sheets', 'v4', credentials=sheets_creds)
    gemini = GeminiManager()
    engine = ShortsEngine(CONFIG_FILE)
    
    last_col = get_col_letter(COL_IDX_DURATION) # Ensure we read enough columns if needed
    range_n = f"{CONFIG['SHEET_NAME']}!A:{last_col}"
    
    rows = sheets.spreadsheets().values().get(
        spreadsheetId=CONFIG['SPREADSHEET_ID'], range=range_n
    ).execute().get('values', [])
    
    processed = 0
    for i, row in enumerate(rows):
        if i == 0: continue
        if processed >= CONFIG['MAX_ROWS_TO_PROCESS']: break
        
        def val(idx): return row[idx].strip() if len(row) > idx else ""
        
        if val(COL_IDX_STATUS).lower() != CONFIG['STATUS_TO_PROCESS'].lower(): continue
        if not val(COL_IDX_FILTER) or not val(COL_IDX_ID) or not val(COL_IDX_VIDEO): continue
        
        success, meta_data = process_row(engine, gemini, row, i+1)
        
        # 1. Update Status (Column AN / 39)
        status_cell = f"{CONFIG['SHEET_NAME']}!{get_col_letter(COL_IDX_STATUS)}{i+1}"
        sheets.spreadsheets().values().update(
            spreadsheetId=CONFIG['SPREADSHEET_ID'], range=status_cell,
            valueInputOption='USER_ENTERED', body={'values': [[meta_data['status']]]}
        ).execute()
        
       # 2. If Successful, Update Metadata Columns (AR, AS, AT, AX)
        if success:
            # Range AR:AT (43 to 45) - Filename, Template, Duration
            start_col = get_col_letter(COL_IDX_FILENAME)
            end_col = get_col_letter(COL_IDX_DURATION)
            meta_range = f"{CONFIG['SHEET_NAME']}!{start_col}{i+1}:{end_col}{i+1}"
            
            meta_values = [[
                meta_data['filename'],
                meta_data['template'],
                meta_data['duration']
            ]]
            
            sheets.spreadsheets().values().update(
                spreadsheetId=CONFIG['SPREADSHEET_ID'], range=meta_range,
                valueInputOption='USER_ENTERED', body={'values': meta_values}
            ).execute()
            
            # 3. Update Voice System Used (Column AX / 49)
            voice_cell = f"{CONFIG['SHEET_NAME']}!{get_col_letter(COL_IDX_VOICE)}{i+1}"
            sheets.spreadsheets().values().update(
                spreadsheetId=CONFIG['SPREADSHEET_ID'], range=voice_cell,
                valueInputOption='USER_ENTERED', body={'values': [[meta_data['voice_system']]]}
            ).execute()
        
        processed += 1
    
    print(f"\n✨ Processed {processed} videos!")

if __name__ == "__main__":
    main()