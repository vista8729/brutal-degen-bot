import os
print("=== DEBUG START ===")
print("Python script started successfully")

import feedparser
import requests
import time
import json
from datetime import datetime
import tweepy
from dotenv import load_dotenv
import pytz

print("Wszystkie importy załadowane pomyślnie")

load_dotenv()
print("Environment variables załadowane")

print("XAI_BEARER:", "OK" if os.getenv("XAI_BEARER") else "BRAK")
print("CONSUMER_KEY:", "OK" if os.getenv("CONSUMER_KEY") else "BRAK")

print("🚀 Brutal Degen Roast Bot STARTED – @BrutalDegenX")
print("Harmonogram ET • Debug version aktywna")

# Prosta pętla testowa
while True:
    print(f"[{datetime.now(pytz.timezone('America/New_York')).strftime('%H:%M')} ET] Bot żyje i działa...")
    time.sleep(60)
