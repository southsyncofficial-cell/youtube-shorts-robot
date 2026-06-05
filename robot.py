import os
import io
import re
import time
import json
import random
import datetime  # 👈 Added back to fix the NameError
import sys       # 👈 Added back to fix the NameError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# Import the official Gemini AI library
from google import genai

# ==========================================
# 1. SETUP DETAILS (MULTI-FOLDER CONFIG)
# ==========================================
FOLDER_IDS = [
    "15jclc285jDJ9T2McW4zZfkKH9UsAFSRK",
    "1VuhTb8PuWjwAUBZHC-MLz6Vxl-Uh6gWf",
    "1X9qF_lyT2-0JX5eTFRexki_oyMA4p4II",
    "1yp9qe6K2Lu9WTNkzZKBDy2uZ0M86NmS_",
    "1vB55RoK3VPKA7wBFAYDnYwsIn5YBbE51",
    "1UtimJh7rvUNvngHUuEpoRCNAxTHIXYle",
    "1yRIY4Eza9SHRAbdubi7CQSMX2GCWk-p_",
    "1-ZreTe2JMdtT08lWL3KC0dPGXYlFzGxS"
]

HISTORY_FILE = "upload_history.txt"            # The ledger file tracking what we uploaded
LOCAL_VIDEO_NAME = "temp_short.mp4"             # Temporary file name on your PC

SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/youtube.upload'
]

# 🔑 COMBINED CLOUD & LOCAL SAFETYS: Keep your real key as the local fallback!
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

def get_google_services():
    creds = None
    
    # ☁️ Cloud Environment Check: Pull keys from GitHub Vault if running in the cloud
    if os.getenv("RUNNING_IN_CLOUD") == "true":
        print("☁️ Running in GitHub Cloud. Extracting tokens from secure vault...")
        creds_json = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        token_json = json.loads(os.getenv("GOOGLE_TOKEN"))
        
        creds = Credentials.from_authorized_user_info(token_json, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
    else:
        # 💻 Local Environment Check: Use your local files if running on your PC
        print("💻 Running locally on PC. Reading token.json...")
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
                
    return build('drive', 'v3', credentials=creds), build('youtube', 'v3', credentials=creds)

def get_uploaded_history():
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f.readlines() if line.strip())

def log_successful_upload(filename):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(filename + "\n")

# ==========================================
# 🧠 CODESAFE INSTANT VIRAL TEXT-AI ENGINE
# ==========================================
def get_viral_text_metadata(filename, fallback_title):
    print("🧠 [AI INSTANT GENERATION] Crafting custom viral title & caption from theme...")
    try:
        # ☁️ Force look at the exact Cloud Environment Variable first, fallback to Local constant
        actual_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
        
        # Initialize the official Google GenAI Client
        client = genai.Client(api_key=actual_key)
        random_seed = random.randint(1000, 9999)

        prompt = (
            f"You are a YouTube Shorts Growth Hacker. The channel name is 'Realtoontribe', "
            f"which posts highly engaging cartoon animations, retro funny clips, and relatable toon reels.\n"
            f"The current file marker identifier is: {filename}. (Seed: {random_seed})\n\n"
            "Task 1: Generate a highly relevant, high-click-through-rate (CTR) viral title under 50 characters. "
            "It must trigger intense curiosity, humor, or nostalgia for someone who loves animations or funny cartoon reels. "
            "Use curiosity loops, relatable angles, or emojis (e.g., 'When the cartoon logic makes no sense 💀', "
            "'This animation took it too far 😂', 'Childhood memories unlocked 🥺', 'Wait for the plot twist... 💥'). "
            "Do NOT include any hashtags in the title itself.\n\n"
            "Task 2: Write a matching 2-sentence engaging caption that drives comments. Include 4-5 viral hashtags at the bottom.\n\n"
            "Return your final response ONLY in strict JSON format like this:\n"
            "{\n"
            '  "title": "Your Click-Worthy Title Here",\n'
            '  "caption": "Your matched caption text here...\\n\\n#Shorts #Viral"\n'
            "}"
        )
        
        # Call the updated official model
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"} 
        )
        
        raw_text = response.text.strip()
        
        if raw_text.startswith("```"):
            lines = raw_text.splitlines()
            if lines[0].startswith("```"):
                lines.pop(0)
            if lines and lines[-1].strip() == "```":
                lines.pop(-1)
            raw_text = "\n".join(lines).strip()
            
        data = json.loads(raw_text)
        return data.get("title", fallback_title), data.get("caption", "Check this out! #Shorts")
        
    except Exception as e:
        # 🚨 This prints the EXACT reason why Gemini failed so we can see it in the log!
        print(f"❌ Instant AI Generation failed internal crash log: {e}")
        return f"{fallback_title}", "Check out this amazing short! 👇\n\n#Shorts #Viral #Trending"

# ==========================================
# 🚀 AUTOMATION CORE (MULTI-FOLDER HAUL)
# ==========================================
def run_automation_cycle():
    print("🤖 Robot assembly line starting up...")
    drive_service, youtube_service = get_google_services()
    
    uploaded_videos = get_uploaded_history()
    print(f"📊 History ledger check: You have already uploaded {len(uploaded_videos)} videos.")
    
    target_item = None
    
    for current_folder_id in FOLDER_IDS:
        print(f"📁 Scanning folder ID: {current_folder_id}...")
        query = f"'{current_folder_id}' in parents and (mimeType contains 'video/' or mimeType = 'application/vnd.google-apps.shortcut') and trashed = false"
        
        results = drive_service.files().list(q=query, pageSize=100, fields="files(id, name, mimeType, shortcutDetails)").execute()
        items = results.get('files', [])
        
        for item in items:
            if item['name'] not in uploaded_videos:
                target_item = item
                break
                
        if target_item:
            break

    if not target_item:
        print("🎉 Awesome! Every single video scanned in all 8 folders has already been uploaded!")
        return

    file_name = target_item['name']
    mime_type = target_item['mimeType']
    video_id = target_item['id']
    
    if mime_type == 'application/vnd.google-apps.shortcut':
        video_id = target_item.get('shortcutDetails', {}).get('targetId')
        print(f"🎯 Found new video bookmark: {file_name}")
    else:
        print(f"🎯 Found new physical video file: {file_name}")

    print(f"📥 Downloading video data to local PC...")
    try:
        request = drive_service.files().get_media(fileId=video_id)
        with io.FileIO(LOCAL_VIDEO_NAME, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
        print("✅ Download finished.")
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return

    backup_title = file_name.replace(".mp4", "").replace(".mov", "")
    backup_title = re.sub(r'AM\d+|PM\d+', '', backup_title).replace("_", " ").title().strip()

    ai_title, ai_caption = get_viral_text_metadata(file_name, backup_title)
    final_title = f"{ai_title} #Shorts"
        
    body = {
        'snippet': {
            'title': final_title,
            'description': ai_caption,
            'categoryId': '22'
        },
        'status': {
            'privacyStatus': 'public' 
        }
    }

    print(f"🚀 Uploading live to YouTube Shorts...")
    print(f"💥 High-CTR Title:  {final_title}")
    print(f"💬 Matched Caption:\n{ai_caption}\n")
    
    media = None
    try:
        media = MediaFileUpload(LOCAL_VIDEO_NAME, chunksize=1024*1024, mimetype='video/mp4', resumable=True)
        request = youtube_service.videos().insert(part='snippet,status', body=body, media_body=media)
        response = None
        while response is None:
            _, response = request.next_chunk()

        new_video_id = response.get('id')
        print(f"🎉 LIVE! URL: [https://youtu.be/](https://youtu.be/){new_video_id}")
        
        log_successful_upload(file_name)
        print(f"📝 Saved '{file_name}' into history ledger.")

    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    finally:
        if media is not None and hasattr(media, '_fd') and media._fd:
            try:
                media._fd.close()
            except:
                pass
                
        if os.path.exists(LOCAL_VIDEO_NAME):
            try:
                os.remove(LOCAL_VIDEO_NAME)
                print("🧹 Cleaned up temporary video file.")
            except Exception as delete_error:
                print(f"⚠️ Cleanup note: {delete_error}")
    
    print("🏁 Cycle completed successfully!\n")

# ==========================================
# 🛑 HIGH-PRECISION TWIN-WAVE TIME GATE
# ==========================================

import datetime
import os

    def run_time_gate():
    # 👤 Manual Button Override: Always let it run if you click it manually
    if os.getenv("GITHUB_EVENT_NAME", "") == "workflow_dispatch":
        print("👤 Manual trigger detected! Bypassing all checks to upload immediately.")
        return True

    # 🌍 Calculate today's date string in Indian Standard Time (YYYY-MM-DD)
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
    today_str = ist_now.strftime("%Y-%m-%d")
    
    # 📖 Check how many videos we have already uploaded today
    history_file = "upload_history.txt"
    todays_upload_count = 0
    
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            history_content = f.read()
            # Count how many times today's date shows up in your log file
            todays_upload_count = history_content.count(today_str)
            
    print(f"📊 Daily Report: Total uploads completed so far today ({today_str}): {todays_upload_count}/2")
    
    # 🛑 Strictly cap it at 2 reels per day
    if todays_upload_count >= 2:
        print("🔒 Daily quota reached (2/2 videos posted). Standing down until tomorrow.")
        return False
        
    print(f"🔓 Quota remaining ({todays_upload_count}/2). Opening gate to upload a video!")
    return True

if __name__ == '__main__':
    # 🛑 Stop execution early if GitHub boots the computer outside your target wave hours
    if not run_time_gate():
        sys.exit()
        
    # 🎬 Run your untouched core pipeline if the time gate is unlocked!
    run_automation_cycle()