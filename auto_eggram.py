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

def make_dcs(init_d):
    params = urllib.parse.parse_qsl(init_d)
    items = []
    for k, v in params:
        if k not in ['hash', 'signature']:
            items.append(f"{k}={v}")
    items.sort()
    raw = "\n".join(items)
    return base64.b64encode(raw.encode('utf-8')).decode('ascii').replace('+', '-').replace('/', '_').rstrip('=')

async def tg_join_and_archive(client, target):
    try:
        clean_target = target.strip().replace("https://t.me/", "").replace("t.me/", "").split("/")[0].split("?")[0]
        entity = await client.get_input_entity(clean_target)
        try:
            await client(JoinChannelRequest(entity))
        except UserAlreadyParticipantError:
            pass
        except Exception:
            pass
        await client(EditPeerFoldersRequest(folder_peers=[InputFolderPeer(peer=entity, folder_id=1)]))
        log("TG_ARCHIVE", f"Đã lưu trữ {clean_target} vào Folder 1 (Archive) vĩnh viễn không out.", Fore.GREEN)
    except Exception as e:
        log("TG_ERR", f"Lỗi join/archive: {e}", Fore.YELLOW)

async def fetch_tg_init_data():
    try:
        client = TelegramClient(StringSession(CURRENT_ACC["session"]), CURRENT_ACC["api_id"], CURRENT_ACC["api_hash"])
        await client.connect()
        if not await client.is_user_authorized():
            log("AUTH_ERR", f"Session {CURRENT_ACC['name']} không hợp lệ!", Fore.RED)
            await client.disconnect()
            return None, None
        bot = await client.get_input_entity(BOT_USERNAME)
        res = await client(functions.messages.RequestWebViewRequest(
            peer=bot,
            bot=bot,
            platform="android",
            url=APP_URL
        ))
        frag = urllib.parse.urlparse(res.url).fragment
        init_data = urllib.parse.parse_qs(frag).get("tgWebAppData", [None])[0]
        return init_data, client
    except Exception as e:
        log("TELETHON_ERR", f"Lỗi lấy initData: {e}", Fore.RED)
        return None, None

class EggramBot:
    def __init__(self, init_data):
        self.init_data = init_data
        parsed = dict(urllib.parse.parse_qsl(init_data))
        user_obj = json.loads(parsed.get('user', '{}'))
        self.tg_id = str(user_obj.get('id', ''))
        self.sig = parsed.get('signature', '')
        self.dcs = make_dcs(init_data)

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

    async def scan_and_claim_tasks(self, client):
        tasks = self.state.get("tasks", [])
        for tk in tasks:
            t_id = tk.get("id")
            status = tk.get("status")
            if status == "available":
                ch = tk.get("channel") or tk.get("group")
                if ch:
                    target = ch.get("url") or (f"@{ch.get('username')}" if ch.get("username") else None)
                    if target and client:
                        log("TASK", f"👉 Làm nhiệm vụ join kênh/nhóm {target}...", Fore.YELLOW)
                        await tg_join_and_archive(client, target)
                        await asyncio.sleep(3)
                    r = self.session.post(f"{API_BASE}/api/tasks/{t_id}/check", json={})
                    if r.status_code == 200 and r.json().get("ok"):
                        log("TASK_CLAIM", f"🎉 Hoàn thành nhiệm vụ '{t_id}'!", Fore.GREEN)
                        self.state = r.json().get("state", self.state)
                elif t_id == "streak":
                    r = self.session.post(f"{API_BASE}/api/tasks/streak/claim", json={})
                    if r.status_code == 200 and r.json().get("ok"):
                        log("STREAK", "🎉 Nhận thưởng Streak hằng ngày thành công!", Fore.GREEN)
                        self.state = r.json().get("state", self.state)

    def claim_basket_2x(self):
        """Thu hoạch giỏ trứng 2x qua chuỗi QC hoặc claim thường"""
        vault = self.state.get("vault", {})
        pending = float(vault.get("pending", 0))
        can_claim = vault.get("claimable", False)
        if not can_claim and pending < 0.000001:
            return

        log("BASKET", f"🧺 Có {pending:.6f} GRAM trong giỏ trứng! Đang bắt đầu thu hoạch...", Fore.MAGENTA)
        r = self.session.post(f"{API_BASE}/api/claim", json={}, timeout=15)
        if r.status_code == 200:
            d = r.json()
            amt = d.get("amount", pending)
            self.state = d.get("state", self.state)
            log("BASKET_CLAIM", f"🎉 Thu hoạch giỏ trứng thành công: +{float(amt):.8f} GRAM/TON!", Fore.GREEN)

    def hatch_hen_tier3(self):
        """CÀY GÀ ĐẺ TRỨNG TIER 3 (+12⚡ Power) bằng chuỗi 3 QC: Adsgram -> Gigapub -> Monetag"""
        cards = self.state.get("cards", [])
        c3 = None
        for c in cards:
            if c.get("tier") == 3:
                c3 = c
                break

        if c3:
            ready = c3.get("ready", False)
            cd = c3.get("cooldown_left_sec", 0)
            if not ready and cd > 0:
                log("HATCH_WAIT", f"⏳ Thẻ gà Tier 3 đang hồi chiêu ({cd}s)...", Fore.LIGHTBLACK_EX)
                return False, cd

        log("HATCH_START", "🥚 Bắt đầu ấp nở Gà Đẻ Trứng Cấp 3 (+12⚡ Power)...", Fore.CYAN)
        r_start = self.session.post(f"{API_BASE}/api/fish/start", json={"tier": 3}, timeout=15)
        if r_start.status_code != 200 or not r_start.json().get("ok"):
            err = r_start.json().get("error", "Lỗi bắt đầu ấp gà")
            log("HATCH_NOTE", f"Server báo: {err}", Fore.YELLOW)
            return False, 60

        ses = r_start.json().get("session", {})
        ses_id = ses.get("id")
        chain = ses.get("chain", ["adsgram", "gigapub", "monetag"])
        cfg = self.state.get("config", {})
        block_id = cfg.get("networks", {}).get("adsgram", {}).get("block_id", "58569")

        log("HATCH_FLOW", f"Phiên ấp gà #{ses_id} đã mở! Chuỗi QC: {' -> '.join(chain)}", Fore.CYAN)

        try:
            # 1. Adsgram
            if "adsgram" in chain:
                log("STEP1", f"Bước 1/3: Đang tải quảng cáo Adsgram (Block {block_id})...", Fore.YELLOW)
                ad_headers = {
                    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
                    "Origin": API_BASE,
                    "Referer": f"{API_BASE}/",
                    "Accept": "application/json",
                    "X-Requested-With": "org.telegram.messenger"
                }
                params = {
                    "blockId": block_id,
                    "tg_id": self.tg_id,
                    "tg_platform": "android",
                    "platform": "Linux aarch64",
                    "language": "vi",
                    "top_domain": "sslip.io",
                    "signature": self.sig,
                    "data_check_string": self.dcs,
                    "sdk_version": "2.2.5"
                }
                r_adv = requests.get("https://api.adsgram.ai/adv", headers=ad_headers, params=params, timeout=12)
                if r_adv.status_code == 200:
                    import re
                    for u in re.findall(r'https://api\.adsgram\.ai/event\?[^\s\'"\\]+', r_adv.text):
                        if "Reward" in u or "type=Reward" in u:
                            time.sleep(6.5)
                            requests.get(u, headers=ad_headers, timeout=10)
                            time.sleep(3)
                            break
                self.session.post(f"{API_BASE}/api/fish/step", json={"session_id": ses_id, "network": "adsgram"}, timeout=15)

            # 2. Gigapub
            if "gigapub" in chain:
                log("STEP2", "Bước 2/3: Đang xem QC Gigapub (6.5s)...", Fore.YELLOW)
                time.sleep(6.5)
                self.session.post(f"{API_BASE}/api/fish/step", json={"session_id": ses_id, "network": "gigapub"}, timeout=15)

            # 3. Monetag
            if "monetag" in chain:
                log("STEP3", "Bước 3/3: Đang xem QC Monetag (6.5s)...", Fore.YELLOW)
                time.sleep(6.5)
                self.session.post(f"{API_BASE}/api/fish/step", json={"session_id": ses_id, "network": "monetag"}, timeout=15)

            # Hoàn tất ấp gà
            r_fin = self.session.post(f"{API_BASE}/api/fish/finish", json={"session_id": ses_id}, timeout=15)
            if r_fin.status_code == 200 and r_fin.json().get("ok"):
                f = r_fin.json().get("fish", {})
                self.state = r_fin.json().get("state", self.state)
                pwr = self.state.get("power", {}).get("total", 100)
                log("HATCH_SUCCESS", f"🎉🎉🎉 ĐÃ ẤP NỞ THÀNH CÔNG GÀ CẤP {f.get('tier', 3)} (+12⚡ Power)! Tổng Power: {pwr}⚡!", Fore.GREEN)
                return True, 65
            else:
                log("HATCH_NOTE", f"Lỗi hoàn tất: {r_fin.text[:100]}", Fore.YELLOW)
                return False, 60
        except Exception as e:
            log("HATCH_ERR", f"Lỗi chuỗi ấp gà: {e}", Fore.RED)
            return False, 60

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
    log("START", f"Khởi động Eggram Auto 24/7 cày Gà +12⚡ & Giỏ trứng cho {CURRENT_ACC['name']}...", Fore.GREEN)
    start_time = time.time()
    handover_done = False

    while time.time() - start_time < MAX_RUNTIME_SECONDS:
        elapsed = time.time() - start_time
        if elapsed > MAX_RUNTIME_SECONDS - 600 and not handover_done:
            trigger_next_shift()
            handover_done = True

        init_data, tg_client = await fetch_tg_init_data()
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
            pwr = st.get("power", {}).get("total", 100)
            log("STATUS", f"Trang trại gà: {user.get('first_name')} | Số dư: {bal:.8f} GRAM | Sức mạnh: {pwr}⚡ Power", Fore.CYAN)

            # Quét nhiệm vụ
            if tg_client:
                await bot.scan_and_claim_tasks(tg_client)
                await tg_client.disconnect()

            # Thu hoạch giỏ trứng
            bot.claim_basket_2x()

            # Cày Gà Tier 3 (+12⚡ Power)
            ok, cd = bot.hatch_hen_tier3()
            wait_s = max(60, cd + 2)
            log("WAIT", f"Nghỉ {wait_s:.0f}s theo chu kỳ hồi chiêu để chống phát hiện autoclick...", Fore.LIGHTBLACK_EX)
            await asyncio.sleep(wait_s)
        else:
            if tg_client:
                await tg_client.disconnect()
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
