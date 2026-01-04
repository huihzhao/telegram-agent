from keep_sync import KeepSync
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

import os
email = os.getenv("GOOGLE_EMAIL")
pw = os.getenv("GOOGLE_APP_PASSWORD")

print(f"DEBUG: Email starts with: {email[0] if email else 'None'}")
print(f"DEBUG: Password len: {len(pw) if pw else 0}")
print(f"DEBUG: Password starts with: {pw[0] if pw else 'None'}")

print("Testing Google Keep Connection...")
ks = KeepSync()
if ks.login():
    print("✅ Login Successful!")
    try:
        label = ks.keep.findLabel('TelegramAgent')
        print(f"✅ Found Label: {label}")
    except Exception as e:
        print(f"⚠️ Label check failed: {e}")
else:
    print("❌ Login Failed.")
