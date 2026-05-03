import feedparser
import requests
import time
import json
import os
from datetime import datetime
import tweepy
from dotenv import load_dotenv
import pytz

load_dotenv()

# ====================== KONFIGURACJA ======================
XAI_BEARER = os.getenv("XAI_BEARER")

RSS_QUERIES = [
    "bitcoin+OR+btc+ETF+OR+regulation",
    "ethereum+OR+eth+ETF+OR+staking",
    "solana+OR+sol+DeFi+OR+ETF",
    "XRP+OR+Ripple+MiCA+OR+SEC",
    "crypto+regulation+OR+stablecoin+OR+CLARITY+Act"
]

# ====================== HARMONOGRAM ET ======================
ET = pytz.timezone("America/New_York")
SLOTS = [
    "08:00", "09:20", "09:55",     # Opening
    "11:15", "12:45", "14:20", "15:50", "17:00", "19:00",  # Value
    "13:40", "16:40", "20:00",     # News
    "21:15", "22:20", "23:30"      # Closing
]

DATA_FILE = "last_seen.json"
CHECK_INTERVAL = 600  # co 10 minut sprawdzamy newsy

# Tweepy
auth = tweepy.OAuth1UserHandler(
    os.getenv("CONSUMER_KEY"), os.getenv("CONSUMER_SECRET"),
    os.getenv("ACCESS_TOKEN"), os.getenv("ACCESS_TOKEN_SECRET")
)
api = tweepy.API(auth)

def load_last_seen():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"last_pub": "1970-01-01T00:00:00Z", "seen": []}

def save_last_seen(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def fetch_rss_news():
    all_entries = []
    last_seen = load_last_seen()
    cutoff = datetime.fromisoformat(last_seen["last_pub"].replace("Z", "+00:00"))
    
    for query in RSS_QUERIES:
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        for entry in feed.entries:
            try:
                pub_date = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z")
                if pub_date > cutoff and entry.link not in last_seen["seen"]:
                    all_entries.append({
                        "title": entry.title,
                        "link": entry.link,
                        "pubDate": entry.published,
                        "description": entry.description[:500] if hasattr(entry, "description") else ""
                    })
                    last_seen["seen"].append(entry.link)
            except:
                continue
    
    if all_entries:
        last_seen["last_pub"] = max([e["pubDate"] for e in all_entries], 
                                  key=lambda x: datetime.strptime(x, "%a, %d %b %Y %H:%M:%S %Z")
                                  ).replace(" ", "T").replace("GMT", "Z")
        save_last_seen(last_seen)
    
    return all_entries[:10]

def generate_posts_grok(news_items):
    if not news_items:
        return []
    
    news_text = "\n\n".join([f"Title: {n['title']}\nLink: {n['link']}\nSnippet: {n['description']}" for n in news_items])
    
    system_prompt = """You are Brutal Degen Roast (@BrutalDegenX).
Style: Brutal crypto roasts daily. Sarcastic, degen humor, roast the market, always end with "I lose money so you don’t have to".
Mix hype + pain + dark humor. Use emojis 🔥😭🚀.
Generate exactly 2-4 ready-to-post tweets (max 280 characters each).
Separate posts with "---".
If the news is huge - start the post with "🚨 BREAKING"."""

    payload = {
        "model": "grok-4.20-reasoning",
        "input": f"{system_prompt}\n\nLatest news:\n{news_text}\n\nGenerate posts in my Brutal Degen Roast style."
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {XAI_BEARER}"
    }

    try:
        resp = requests.post("https://api.x.ai/v1/responses", json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        content = result.get("output") or result.get("choices", [{}])[0].get("message", {}).get("content", "")
        posts = [p.strip() for p in content.split("---") if p.strip()]
        return posts[:4]
    except Exception as e:
        print(f"Grok API error: {e}")
        return []

def post_to_x(text):
    try:
        api.update_status(text)
        print(f"✅ Posted at {datetime.now(ET).strftime('%H:%M')} ET: {text[:80]}...")
        time.sleep(3)
        return True
    except Exception as e:
        print(f"Post error: {e}")
        return False

def is_slot_time():
    now = datetime.now(ET)
    current = now.strftime("%H:%M")
    return current in SLOTS

# ====================== MAIN LOOP ======================
print("🚀 Brutal Degen Roast Bot STARTED – @BrutalDegenX")
print("Harmonogram ET • Global crypto • No spam")

while True:
    now_et = datetime.now(ET)
    print(f"[{now_et.strftime('%H:%M')} ET] Sprawdzam nowe newsy...")

    news = fetch_rss_news()

    if news:
        print(f"Znaleziono {len(news)} nowych newsów → generuję roasty...")
        posts = generate_posts_grok(news)
        
        for post in posts:
            # Jeśli Grok oznaczył jako BREAKING → publikujemy OD RAZU
            if post.startswith("🚨 BREAKING") or "BREAKING" in post.upper():
                print("🚨 BREAKING NEWS – publikuję natychmiast!")
                post_to_x(post)
            # Normalny post → publikujemy tylko w slotach
            elif is_slot_time():
                post_to_x(post)
            else:
                print("⏳ Nie ma slotu – pomijam publikację")
    else:
        print("Brak nowych newsów.")

    print(f"⏳ Czekam {CHECK_INTERVAL//60} minut...\n")
    time.sleep(CHECK_INTERVAL)
