import asyncio
import aiohttp
import re
from bs4 import BeautifulSoup

BOT_TOKEN = "8715379481:AAH3DDvgE_53hGuO3ZgMbFfk-DdXLnZt2zM"
CHAT_ID = "7179654594"

SEARCHES = [
    "prop firm coupon",
    "prop firm discount code",
    "free challenge prop firm",
    "funded account giveaway",
    "prop firm promo code"
]

# --- CODE DETECTION ---
def extract_codes(text):
    patterns = [
        r"\b[A-Z]{4,10}[0-9]{2,4}\b",   # SAVE100, FTMO2024
        r"\b[A-Z0-9]{6,12}\b",          # general codes
        r"\bFREE[A-Z0-9]{2,8}\b"        # FREE codes
    ]

    blacklist = ["HTTPS", "HTTP", "WWW", "COM", "TWITTER"]

    results = set()
    text = text.upper()

    for p in patterns:
        matches = re.findall(p, text)
        for m in matches:
            if m not in blacklist:
                if any(c.isdigit() for c in m):
                    results.add(m)

    return list(results)

sent = set()

# --- SEND TO TELEGRAM ---
async def send(session, msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    await session.post(url, data={"chat_id": CHAT_ID, "text": msg})

# --- FETCH DATA ---
async def fetch(session, url):
    try:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as res:
            return await res.text()
    except:
        return ""

# --- SCAN TWITTER (via Nitter) ---
async def scan_query(session, query):
    url = f"https://nitter.net/search?f=tweets&q={query.replace(' ', '+')}"
    html = await fetch(session, url)

    soup = BeautifulSoup(html, "html.parser")
    tweets = soup.find_all("div", class_="tweet-content")

    for t in tweets[:10]:
        text = t.get_text()
        codes = extract_codes(text)

        if codes:
            key = text[:100]

            if key not in sent:
                msg = f"💸 CODE FOUND\n\n{text[:120]}\n\nCodes: {', '.join(codes)}"
                await send(session, msg)
                sent.add(key)

# --- MAIN LOOP ---
async def main():
    async with aiohttp.ClientSession() as session:
        # Test message (so you know bot works)
        await send(session, "✅ Bot is running and scanning...")

        while True:
            tasks = []
            for query in SEARCHES:
                tasks.append(scan_query(session, query))

            await asyncio.gather(*tasks)
            await asyncio.sleep(15)  # fast but safe

asyncio.run(main())
