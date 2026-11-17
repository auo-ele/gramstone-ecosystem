import os
import sys
import time
import json
import base64
import random
import asyncio
import urllib.parse
from datetime import datetime, timezone, timedelta
from colorama import Fore, Style, init
import requests
import urllib3

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon import functions

urllib3.disable_warnings()
init(autoreset=True)

# ---------------------------------------------------------------------------
#  CẤU HÌNH TÀI KHOẢN (CHỈ DÀNH CHO ACC 4 THEO YÊU CẦU)
# ---------------------------------------------------------------------------
CURRENT_ACC = {
    "name": "Acc 4 (Belinnh2k)",
    "api_id": 34333329,
    "api_hash": "4f9371f95000578c84dbc670aaf1f819",
    "session": (
        "1BVtsOMMBu6WXSbH0pQyd4FdW0Fc-zqEWvx3RMUB53LJeKWWB6t61lV-p3TcR3k2psUxcUtbmfdeC1jATK8f7i5jIX_eiplenW3A-h9ALZB7cq9PodKB_KJP4fhOMNeb43G8H7SbF5hDnrdPOiFMEYS1tbjOrmzNu_UyzNe64ndfKb9SSpsTZtrKbo3ryx4x7gpXHrrfISsyMUm6gOjEl9KbyvWCt94yu_spYicw2YsAGCMlKmEYqGIIIpItqZ4VJrdwPtzS__VudhSQzwM56cZMwgTsicw0NA_zaRmgZ4sJEU0ADeMMutBhDtL-kQsJQUb145Ybagpel5xAK86xAKjaeQau5R1I="
    )
}

API_BASE = "https://eggram.209-38-193-227.sslip.io"
BOT_USERNAME = "eggramearnbot"
APP_URL = "https://eggram.209-38-193-227.sslip.io/"
MAX_RUNTIME_SECONDS = int(os.getenv("MAX_RUNTIME_SECONDS", "17500"))

def log(tag, msg, color=Fore.WHITE):
    t_str = time.strftime('%H:%M:%S')
    print(f"{Fore.LIGHTBLACK_EX}[{t_str}]{Style.RESET_ALL} {Fore.CYAN}[{tag:<14}]{Style.RESET_ALL} {color}{msg}{Style.RESET_ALL}", flush=True)

async def fetch_tg_init_data():
    try:
        client = TelegramClient(StringSession(CURRENT_ACC["session"]), CURRENT_ACC["api_id"], CURRENT_ACC["api_hash"])
        await client.connect()
        if not await client.is_user_authorized():
            log("AUTH_ERR", f"Session {CURRENT_ACC['name']} không hợp lệ!", Fore.RED)
            await client.disconnect()
            return None
        bot = await client.get_input_entity(BOT_USERNAME)
        res = await client(functions.messages.RequestWebViewRequest(
            peer=bot,
            bot=bot,
            platform="android",
            url=APP_URL
        ))
        await client.disconnect()
        frag = urllib.parse.urlparse(res.url).fragment
        init_data = urllib.parse.parse_qs(frag).get("tgWebAppData", [None])[0]
        return init_data
    except Exception as e:
        log("TELETHON_ERR", f"Lỗi lấy initData: {e}", Fore.RED)
        return None

class EggramBot:
    def __init__(self, init_data):
        self.init_data = init_data
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Telegram-Init-Data": self.init_data,
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
            "Origin": API_BASE,
            "Referer": f"{API_BASE}/"
        })
        self.state = {}

    def get_state(self):
        try:
            time.sleep(random.uniform(0.8, 1.5))
            r = self.session.get(f"{API_BASE}/api/state", timeout=15)
            if r.status_code == 200:
                self.state = r.json().get("state", {})
                return self.state
            return None
        except Exception:
            return None

    def auth(self):
        try:
            r = self.session.post(f"{API_BASE}/api/auth", json={}, timeout=15)
            if r.status_code == 200:
                self.state = r.json().get("state", {})
                return True
            return False
        except Exception:
            return False

    def claim_basket(self):
        """Thu hoạch giỏ trứng quy đổi sang GRAM/TON"""
        try:
            # Thử claim x2 trước
            r = self.session.post(f"{API_BASE}/api/claim", json={}, timeout=15)
            if r.status_code == 200:
                d = r.json()
                self.state = d.get("state", {})
                amt = d.get("amount", 0)
                log("EGG_CLAIM", f"🥚 Thu hoạch giỏ trứng thành công: +{amt} GRAM!", Fore.GREEN)
                return True
        except Exception:
            pass
        return False

def trigger_next_shift():
    token = os.getenv("GH_PAT")
    repo = os.getenv("GITHUB_REPOSITORY", "auo-ele/gramstone-ecosystem")
    if not token:
        return
    try:
        url = f"https://api.github.com/repos/{repo}/actions/workflows/eggram_acc4.yml/dispatches"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        requests.post(url, headers=headers, json={"ref": "main"}, timeout=15)
    except Exception:
        pass

async def main():
    log("START", f"Khởi động Eggram Auto 24/7 cho {CURRENT_ACC['name']} (Chống autoclick)...", Fore.GREEN)
    start_time = time.time()
    handover_done = False

    while time.time() - start_time < MAX_RUNTIME_SECONDS:
        elapsed = time.time() - start_time
        if elapsed > MAX_RUNTIME_SECONDS - 600 and not handover_done:
            trigger_next_shift()
            handover_done = True

        init_data = await fetch_tg_init_data()
        if not init_data:
            await asyncio.sleep(30)
            continue

        bot = EggramBot(init_data)
        st = bot.get_state()
        if not st:
            bot.auth()
            st = bot.get_state()

        if st:
            user = st.get("user", {})
            bal = float(st.get("balance", 0))
            vault = st.get("vault", {})
            pending = float(vault.get("pending", 0))
            can_claim = vault.get("claimable", False)
            log("STATUS", f"Trang trại gà: {user.get('first_name')} | Số dư: {bal:.6f} GRAM | Trứng chờ thu hoạch: {pending:.6f} GRAM (Có thể nhận: {can_claim})", Fore.CYAN)

            if can_claim or pending > 0.000001:
                bot.claim_basket()

        await asyncio.sleep(random.uniform(60, 95))

if __name__ == "__main__":
    asyncio.run(main())
