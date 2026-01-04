import gpsoauth
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

email = os.getenv("GOOGLE_EMAIL")
password = os.getenv("GOOGLE_APP_PASSWORD").replace(" ", "")

print(f"Attempting OAuth with:")
print(f"Email: {email}")
print(f"Password: {password[:2]}...{password[-2:]}")

t = gpsoauth.perform_master_login(email, password, 'androidId')
print(f"Response: {t}")
