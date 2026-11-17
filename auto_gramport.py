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
from telethon.tl.types import InputFolderPeer
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.folders import EditPeerFoldersRequest
from telethon.errors import UserAlreadyParticipantError, FloodWaitError

urllib3.disable_warnings()
init(autoreset=True)

# ---------------------------------------------------------------------------
#  CẤU HÌNH TÀI KHOẢN (ACC 1, 2, 4)
# ---------------------------------------------------------------------------
ACCOUNTS_CONFIG = {
    1: {
        "name": "Acc 1 (hungzai22)",
        "api_id": 39182276,
        "api_hash": "f02b155d895a3a3fbf8a1cbe810b5338",
        "session": (
            "1BVtsOHIBuxmpWiBJ9hvwV9pSrzWw5U2I5Fe20Ww8l1LCk9rnsG6T6lLZEJXZE1JJC_qUH_yyWHnRoed"
            "RNI5lJYnfjRN4gyGeDrCxquDU12ZflrpCz0VLhMZx2C0LlyUCy2eHRSRE1wUCpEYZaymL0P7Z9eAHwMy4"
            "Oogewh5TqyO4x4MF6j0yTq8Zvfpv43O4aQDzErNv3GRqpx8DXBcOJIMP9yVhq-Mby5VH5J9cF-h-bJ5ws"
            "3xKjA4GY7YKjHxDt9OI-Zr7mr-V3qZy99UxJooThJj51f2RqOKhODdLh9XZQ0ygSoAd3iFAZDOPMEo8Ch"
            "5TrrzLXi2Q3N0HorIL1JfV0xoFQlY="
        )
    },
    2: {
        "name": "Acc 2 (gaylobucu)",
        "api_id": 39182276,
        "api_hash": "f02b155d895a3a3fbf8a1cbe810b5338",
        "session": (
            "1BVtsOHIBuzoeRtBOmpNGh2sdyxpZ5e0nY4MrFe-6KKbmJPaM0YnCJiKRI0L9mEh1C5rwqLQqucj456LRF7v"
            "V1YIPjZNqL6JevLM0Ww3FTml1NoKdwsiPINfsy9MbBlBhKOvha7py44L4pK5aEXjwpjpoNj4LaSmtWaPiQPuf"
            "JuTwPB86f4gYjSeXM3HtxhnFU7MtHR5vbZPBa9N2HQSlt2BMB47q00DbQVtvYA37R3R-TrtV2MtwixL9ozChAD"
            "Fq38NYcw4eRyRwKrkobVLccvz0_hvqgHXiQbrfcFLLRkRGwGlRCB-Ew4YhLLdnCbG1hjGEfxUrp9MRmF0JvS"
            "-u20MfAuvlcgQ="
        )
    },
    4: {
        "name": "Acc 4 (Belinnh2k)",
        "api_id": 34333329,
        "api_hash": "4f9371f95000578c84dbc670aaf1f819",
        "session": (
            "1BVtsOMMBu6WXSbH0pQyd4FdW0Fc-zqEWvx3RMUB53LJeKWWB6t61lV-p3TcR3k2psUxcUtbmfdeC1jATK8f7i5jIX_eiplenW3A-h9ALZB7cq9PodKB_KJP4fhOMNeb43G8H7SbF5hDnrdPOiFMEYS1tbjOrmzNu_UyzNe64ndfKb9SSpsTZtrKbo3ryx4x7gpXHrrfISsyMUm6gOjEl9KbyvWCt94yu_spYicw2YsAGCMlKmEYqGIIIpItqZ4VJrdwPtzS__VudhSQzwM56cZMwgTsicw0NA_zaRmgZ4sJEU0ADeMMutBhDtL-kQsJQUb145Ybagpel5xAK86xAKjaeQau5R1I="
        )
    }
}

ACC_NUM = int(os.getenv("ACC_NUM", "4"))
CURRENT_ACC = ACCOUNTS_CONFIG.get(ACC_NUM, ACCOUNTS_CONFIG[4])

API_BASE = "https://142-93-138-24.sslip.io"
BOT_USERNAME = "freegramportbot"
APP_URL = "https://142-93-138-24.sslip.io/app/"
MAX_RUNTIME_SECONDS = int(os.getenv("MAX_RUNTIME_SECONDS", "17500"))

def log(tag, msg, color=Fore.WHITE):
    t_str = time.strftime('%H:%M:%S')
    print(f"{Fore.LIGHTBLACK_EX}[{t_str}]{Style.RESET_ALL} {Fore.CYAN}[{tag:<14}]{Style.RESET_ALL} {color}{msg}{Style.RESET_ALL}", flush=True)

async def tg_join_and_archive(client, channel_target):
    try:
        clean_target = channel_target.strip().replace("https://t.me/", "").replace("t.me/", "")
        clean_target = clean_target.split("/")[0].split("?")[0]
        entity = await client.get_input_entity(clean_target)
        try:
            await client(JoinChannelRequest(entity))
        except UserAlreadyParticipantError:
            pass
        except Exception as e:
            log("TG_JOIN_WARN", f"Join '{clean_target}': {e}", Fore.YELLOW)
        await client(EditPeerFoldersRequest(folder_peers=[InputFolderPeer(peer=entity, folder_id=1)]))
        log("TG_ARCHIVE", f"Đã lưu trữ kênh {clean_target} vào Folder 1 (Archive) vĩnh viễn không out.", Fore.GREEN)
    except Exception as e:
        log("TG_ARCH_ERR", f"Lỗi lưu trữ: {e}", Fore.YELLOW)

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

class GramPortBot:
    def __init__(self, init_data):
        self.init_data = init_data
        self.session = requests.Session()
        self.session.headers.update({
            "content-type": "application/json",
            "x-init-data": self.init_data,
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
            "Origin": API_BASE,
            "Referer": f"{API_BASE}/app/"
        })
        self.state = {}

    def get_state(self):
        try:
            # Chống autoclick: Jitter delay ngẫu nhiên
            time.sleep(random.uniform(0.8, 1.6))
            r = self.session.get(f"{API_BASE}/api/state", timeout=15)
            if r.status_code == 200:
                self.state = r.json()
                return self.state
            log("STATE_ERR", f"Lỗi lấy state: HTTP {r.status_code}", Fore.RED)
            return None
        except Exception as e:
            log("STATE_ERR", f"Exception lấy state: {e}", Fore.RED)
            return None

    def action(self, act_type, body=None):
        try:
            time.sleep(random.uniform(1.2, 2.5))
            payload = {"type": act_type}
            if body:
                payload.update(body)
            r = self.session.post(f"{API_BASE}/api/action", json=payload, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if "state" in data:
                    self.state = data["state"]
                return data.get("result", True)
            log("ACTION_ERR", f"Action '{act_type}' HTTP {r.status_code}: {r.text[:100]}", Fore.YELLOW)
            return None
        except Exception as e:
            log("ACTION_ERR", f"Lỗi gọi action '{act_type}': {e}", Fore.YELLOW)
            return None

    def check_and_start_shift(self):
        """Bật ca làm việc mới cho máy bay Sparrow P-1 (4 giờ) ngay khi phi công nghỉ ngơi"""
        planes = self.state.get("planes", [])
        now_ts = self.state.get("now", int(time.time() * 1000))
        p1 = None
        for p in planes:
            if p.get("tier") == "p1":
                p1 = p
                break

        if not p1 or p1.get("ended") or now_ts >= p1.get("expires", 0):
            log("SHIFT", "✈️ Phi công đang nghỉ ngơi! Bắt đầu ca làm việc 4h mới (Sparrow P-1)...", Fore.CYAN)
            res = self.action("shift")
            if res:
                log("SHIFT_OK", "🎉 Đã bắt đầu ca làm việc mới thành công! Máy bay đang hạ cánh kiếm GRAM.", Fore.GREEN)
                return True
        else:
            remain_min = max(0, int((p1.get("expires", 0) - now_ts) / 60000))
            landings = p1.get("landings", 0)
            earned = p1.get("earned", 0)
            log("PLANE_ACTIVE", f"✈️ Sparrow P-1 đang bay: Còn {remain_min} phút | Đã hạ cánh: {landings} lần | Đã kiếm: {earned/1e9:.6f} GRAM", Fore.LIGHTBLUE_EX)
        return False

    def claim_daily(self):
        user = self.state.get("user", {})
        daily = user.get("daily", {})
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if daily.get("last") != today_str:
            log("DAILY", "🎁 Phát hiện điểm danh hằng ngày chưa nhận, đang nhận...", Fore.CYAN)
            res = self.action("daily")
            if res:
                streak = res.get("streak", 1)
                xp = res.get("xp", 0)
                nano = res.get("nano", 0)
                log("DAILY_OK", f"🎉 Điểm danh thành công! Streak {streak} ngày | +{nano/1e9:.6f} GRAM | +{xp} XP", Fore.GREEN)

def trigger_next_shift(acc_num):
    token = os.getenv("GH_PAT")
    repo = os.getenv("GITHUB_REPOSITORY", "auo-ele/gramstone-ecosystem")
    workflow = f"gramport_acc{acc_num}.yml"
    if not token:
        return
    try:
        url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        r = requests.post(url, headers=headers, json={"ref": "main"}, timeout=15)
        log("HANDOVER", f"Bàn giao ca 24/7 tiếp theo ({workflow}): HTTP {r.status_code}", Fore.MAGENTA)
    except Exception as e:
        log("HANDOVER_ERR", f"Lỗi trigger ca tiếp theo: {e}", Fore.RED)

async def main():
    log("START", f"Khởi động GramPort Auto 24/7 cho {CURRENT_ACC['name']} (Chống autoclick, jitter ngẫu nhiên)...", Fore.GREEN)
    start_time = time.time()
    handover_done = False

    while time.time() - start_time < MAX_RUNTIME_SECONDS:
        elapsed = time.time() - start_time
        if elapsed > MAX_RUNTIME_SECONDS - 600 and not handover_done:
            trigger_next_shift(ACC_NUM)
            handover_done = True

        init_data = await fetch_tg_init_data()
        if not init_data:
            log("RETRY", "Không lấy được initData, thử lại sau 30s...", Fore.YELLOW)
            await asyncio.sleep(30)
            continue

        bot = GramPortBot(init_data)
        st = bot.get_state()
        if not st:
            log("RETRY", "Không kết nối được GramPort, thử lại sau 20s...", Fore.YELLOW)
            await asyncio.sleep(20)
            continue

        user = st.get("user", {})
        bal = user.get("balance", 0) / 1e9
        lvl = user.get("level", 1)
        xp = user.get("xp", 0)
        need = user.get("need", 100)
        log("USER_INFO", f"Phi công: {user.get('name')} | Cấp {lvl} (XP: {xp}/{need}) | Số dư: {bal:.6f} GRAM (TON)", Fore.GREEN)

        bot.claim_daily()
        bot.check_and_start_shift()

        # Nghỉ an toàn chống phát hiện autoclick (chu kỳ kiểm tra 60s - 90s)
        jitter_sleep = random.uniform(60, 95)
        await asyncio.sleep(jitter_sleep)

if __name__ == "__main__":
    asyncio.run(main())
