#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  BOT AUTO PLAY 24/7 SIÊU CẤP - MOONPOOL 3D AQUARIUM (@MoonpoolGameBot)
  Platform: Moonpool 3D Aquarium (https://moonpool.64-226-82-60.sslip.io/)
  Bot     : @MoonpoolGameBot (Telegram WebApp App: 'play')
  Target  : CHUYÊN CÀY CÁ KHỦNG CẤP 3 (+12⚡ POWER) NON-STOP 24/7
  Account : hungzai22 (ID: 7744031191) - Acc 1 (Repo: nthanhhung0122-max/m-n)

  CẬP NHẬT MỚI NHẤT TỪ GAME (2/11/2026):
    1. BỎ GIỚI HẠN 40 CÁ/NGÀY: Nâng hạn mức lên 1.000 cá/ngày (cày không giới hạn).
    2. COOLDOWN RÚT GỌN TỪ 5 PHÚT -> 1 PHÚT (60s): Cứ 60s nhận 1 cá khủng +12⚡.
    3. ADSGRAM BLOCK ID MỚI: 56919 (Tự động lấy động theo cấu hình server).
    4. 24/7 AUTO HANDOVER: Tự động dispatch phiên mới sau 4.8h chạy xuyên suốt.
=============================================================================
"""

import os
import sys
import time
import json
import base64
import random
import asyncio
import urllib.parse
import urllib3
import requests
import re
import sqlite3
import tempfile
from datetime import datetime, timezone, timedelta
from colorama import Fore, Style, init

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.crypto import AuthKey
from telethon.tl.functions.messages import RequestAppWebViewRequest
from telethon.tl.types import InputBotAppShortName

urllib3.disable_warnings()
init(autoreset=True)

# ---------------------------------------------------------------------------
#  CẤU HÌNH HỆ THỐNG - ACC 1
# ---------------------------------------------------------------------------
API_ID = 39182276
API_HASH = "f02b155d895a3a3fbf8a1cbe810b5338"

KNOWN_GOOD_STRING_SESSION = (
    os.getenv("TELEGRAM_STRING_SESSION") or
    "1BVtsOMMBu4twagryqQ2jg8Lq0r5ht_iJ-LHnM5qYYrNYGz6aTkbk6gA42gQZ9ZJs80wXSEzppw8z6RK4eKpp6qtGAegFWNsoEbJpCmmd47phuoQ3YN1DPsxsX2uoWJQ60B18gArjt603YezUARHPh7opveQtVwZR9N9M8O4eSFDDQmFHeglnaqniplilMXYSF1Jr7e9E2XevLm2MkYUv4roxlragUkxtKPlSoLOd0V2JMIKN9A4yOzsRHcdI4H33W1XwP1J9UiQrb52gGxsf3i73f_NzbByCFlZPHh04aTRUhNtLBETfLb5XHLtwoxg5SOt24eSkBDRJOtaPCik32hnP3fQjTrQ="
)

REPO_NAME = "m-n"
WORKFLOW_NAME = "moonpool.yml"

API_BASE = "https://moonpool.64-226-82-60.sslip.io"
BOT_USERNAME = "MoonpoolGameBot"
APP_SHORT_NAME = "play"

MAX_RUNTIME_SECONDS = int(os.getenv("MAX_RUNTIME_SECONDS", "17500"))

def log(tag, msg, color=Fore.WHITE):
    t_str = time.strftime('%H:%M:%S')
    print(f"{Fore.LIGHTBLACK_EX}[{t_str}]{Style.RESET_ALL} {color}[{tag:14s}]{Style.RESET_ALL} {msg}", flush=True)

def get_clean_string_session():
    raw = (
        os.getenv("TELEGRAM_STRING_SESSION")
        or os.getenv("TELEGRAM_STRING_SESSION_ACC1")
        or os.getenv("TELEGRAM_SESSION_B64_ACC1")
        or os.getenv("TELEGRAM_SESSION_B64")
        or ""
    ).strip()

    if not raw:
        return KNOWN_GOOD_STRING_SESSION

    if raw.startswith("1") and 300 <= len(raw) <= 450:
        return raw

    try:
        bdata = base64.b64decode(raw)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".session") as tmp:
            tmp.write(bdata)
            tmp_path = tmp.name

        conn = sqlite3.connect(tmp_path)
        c = conn.cursor()
        c.execute("SELECT dc_id, server_address, port, auth_key FROM sessions")
        row = c.fetchone()
        conn.close()
        try: os.remove(tmp_path)
        except Exception: pass

        if row and row[3]:
            ss = StringSession()
            ss.set_dc(row[0], row[1], row[2])
            ss.auth_key = AuthKey(data=row[3])
            extracted = ss.save()
            if extracted:
                return extracted
    except Exception:
        pass

    return KNOWN_GOOD_STRING_SESSION

# ---------------------------------------------------------------------------
#  TỰ ĐỘNG BÀN GIAO CA CHẠY 24/7 (HANDOVER)
# ---------------------------------------------------------------------------
def trigger_next_shift():
    log("HANDOVER", f"🔄 Chuẩn bị chuyển giao ca làm việc tiếp theo trên {REPO_NAME}...", Fore.CYAN)
    pat = os.getenv("GH_PAT", "")
    repo = os.getenv("GITHUB_REPOSITORY") or f"nthanhhung0122-max/{REPO_NAME}"
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{WORKFLOW_NAME}/dispatches"
    headers = {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        r = requests.post(url, headers=headers, json={"ref": "main"}, timeout=15)
        if r.status_code == 204:
            log("HANDOVER", f"✅ Đã kích hoạt ca chạy tiếp theo trên {repo}!", Fore.GREEN)
            return True
        else:
            log("HANDOVER", f"⚠️ Phản hồi dispatch: {r.status_code} {r.text}", Fore.YELLOW)
            return False
    except Exception as e:
        log("HANDOVER", f"❌ Lỗi khi dispatch ca tiếp theo: {e}", Fore.RED)
        return False

# ---------------------------------------------------------------------------
#  1. TELETHON AUTO IN-DATA
# ---------------------------------------------------------------------------
async def fetch_fresh_init_data():
    """Tự động kết nối Telethon lấy init_data mới nhất từ Telegram."""
    try:
        session_str = get_clean_string_session()
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            log("AUTH_ERR", "StringSession không hợp lệ hoặc chưa đăng nhập!", Fore.RED)
            return None

        bot = await client.get_input_entity(BOT_USERNAME)
        bot_app = InputBotAppShortName(bot_id=bot, short_name=APP_SHORT_NAME)
        res = await client(RequestAppWebViewRequest(peer=bot, app=bot_app, platform="android"))
        await client.disconnect()

        frag = urllib.parse.urlparse(res.url).fragment
        init_data = urllib.parse.parse_qs(frag).get("tgWebAppData", [None])[0]
        return init_data
    except Exception as e:
        log("TELETHON_ERR", f"Lỗi lấy init_data: {e}", Fore.RED)
        return None

def make_data_check_string(init_d):
    """Tạo chuỗi data_check_string chuẩn base64url theo đúng Adsgram SDK 2.2.5."""
    params = urllib.parse.parse_qsl(init_d)
    items = []
    for k, v in params:
        if k not in ['hash', 'signature']:
            items.append(f"{k}={v}")
    items.sort()
    raw = "\n".join(items)
    return base64.b64encode(raw.encode('utf-8')).decode('ascii').replace('+', '-').replace('/', '_').rstrip('=')

# ---------------------------------------------------------------------------
#  2. API CLIENT & ENGINE CÀY CÁ +12⚡
# ---------------------------------------------------------------------------
class MoonpoolBot:
    def __init__(self, init_data):
        self.init_data = init_data
        parsed = dict(urllib.parse.parse_qsl(init_data))
        user_obj = json.loads(parsed.get('user', '{}'))
        self.tg_id = str(user_obj.get('id', ''))
        self.sig = parsed.get('signature', '')
        self.dcs = make_data_check_string(init_data)

        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Telegram-Init-Data": self.init_data,
            "User-Agent": "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Origin": API_BASE,
            "Referer": f"{API_BASE}/"
        })
        self.state = {}

    def get(self, endpoint):
        try:
            r = self.session.get(f"{API_BASE}{endpoint}", timeout=15)
            return r.json()
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def post(self, endpoint, data=None):
        try:
            r = self.session.post(f"{API_BASE}{endpoint}", json=data or {}, timeout=15)
            return r.json()
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def auth(self):
        r = self.post("/api/auth", {})
        if r.get("ok"):
            self.state = r.get("state", {})
            return True, self.state
        return False, r

    def get_state(self):
        r = self.get("/api/state")
        if r.get("ok"):
            self.state = r.get("state", {})
            return self.state
        return None

    def claim_vault(self):
        r = self.post("/api/claim", {})
        if r.get("ok"):
            self.state = r.get("state", {})
            return True, r
        return False, r

    def watch_ads_and_claim_tier3_fish(self):
        """
        Quy trình xem chuỗi 3 QC tự động để nhận cá cấp 3 (+12⚡ Power):
          Bước 1: QC Adsgram (Thực hiện bypass Adsgram Reward URL thật)
          Bước 2: QC Gigapub (Delay 6.5s theo quy định hệ thống)
          Bước 3: QC Monetag (Delay 6.5s theo quy định hệ thống)
          Kết thúc: Gọi /api/fish/finish để đưa cá +12⚡ về bể!
        """
        # Đóng session dở dang nếu có
        open_ses = self.state.get("open_session")
        if open_ses and open_ses.get("id"):
            self.post("/api/fish/finish", {"session_id": open_ses.get("id")})
            time.sleep(1)

        # 1. Khởi tạo ca nuôi cá cấp 3 (+12⚡)
        log("TIER3_START", "Đang kích hoạt ca nuôi cá Cấp 3 (+12⚡ Power)...", Fore.CYAN)
        r_start = self.post("/api/fish/start", {"tier": 3})
        if not r_start.get("ok"):
            err = r_start.get("error", "Không thể bắt đầu ca")
            return False, f"Bắt đầu ca thất bại: {err}"

        ses_id = r_start.get("session", {}).get("id")
        if not ses_id:
            return False, "Không nhận được session id từ server"

        log("TIER3_FLOW", f"Phiên nuôi cá #{ses_id} đã mở! Chuỗi QC: Adsgram -> Gigapub -> Monetag", Fore.CYAN)

        try:
            # Lấy block_id động từ config server
            cfg = self.state.get("config", {})
            block_id = cfg.get("networks", {}).get("adsgram", {}).get("block_id") or "56919"

            # --- BƯỚC 1: ADSGRAM ---
            log("STEP1_ADSGRAM", f"Bước 1/3: Đang tải quảng cáo Adsgram (Block: {block_id})...", Fore.YELLOW)
            ad_headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                'Origin': API_BASE,
                'Referer': f"{API_BASE}/",
                'Accept': 'application/json',
                'X-Requested-With': 'org.telegram.messenger'
            }
            params = {
                'blockId': block_id,
                'tg_id': self.tg_id,
                'tg_platform': 'android',
                'platform': 'Linux aarch64',
                'language': 'vi',
                'top_domain': 'sslip.io',
                'signature': self.sig,
                'data_check_string': self.dcs,
                'sdk_version': '2.2.5'
            }

            r_adv = requests.get('https://api.adsgram.ai/adv', headers=ad_headers, params=params, timeout=12)
            if r_adv.status_code == 200:
                reward_url = None
                for u in re.findall(r'https://api\.adsgram\.ai/event\?[^\s\'"\\]+', r_adv.text):
                    if 'Reward' in u or 'type=Reward' in u:
                        reward_url = u
                        break

                if reward_url:
                    log("STEP1_ADSGRAM", "Đang xem video Adsgram (6.5 giây)...", Fore.YELLOW)
                    time.sleep(6.5)
                    requests.get(reward_url, headers=ad_headers, timeout=10)
                    time.sleep(3)

            counted_s1 = False
            for _ in range(6):
                r_s1 = self.post("/api/fish/step", {"session_id": ses_id, "network": "adsgram"})
                if r_s1.get("counted"):
                    counted_s1 = True
                    log("STEP1_ADSGRAM", "✓ Bước 1 Adsgram hoàn thành!", Fore.GREEN)
                    break
                time.sleep(2)

            if not counted_s1:
                self.post("/api/fish/finish", {"session_id": ses_id})
                return False, "Server chưa ghi nhận QC Adsgram. Thử lại sau ít phút..."

            # --- BƯỚC 2: GIGAPUB ---
            log("STEP2_GIGAPUB", "Bước 2/3: Đang xem QC Gigapub (6.5 giây)...", Fore.YELLOW)
            time.sleep(6.5)
            counted_s2 = False
            for _ in range(4):
                r_s2 = self.post("/api/fish/step", {"session_id": ses_id, "network": "gigapub"})
                if r_s2.get("counted"):
                    counted_s2 = True
                    log("STEP2_GIGAPUB", "✓ Bước 2 Gigapub hoàn thành!", Fore.GREEN)
                    break
                time.sleep(2)
            if not counted_s2:
                log("STEP2_WARN", f"Gigapub phản hồi: {r_s2}", Fore.YELLOW)

            # --- BƯỚC 3: MONETAG ---
            log("STEP3_MONETAG", "Bước 3/3: Đang xem QC Monetag (6.5 giây)...", Fore.YELLOW)
            time.sleep(6.5)
            counted_s3 = False
            for _ in range(4):
                r_s3 = self.post("/api/fish/step", {"session_id": ses_id, "network": "monetag"})
                if r_s3.get("counted"):
                    counted_s3 = True
                    log("STEP3_MONETAG", "✓ Bước 3 Monetag hoàn thành!", Fore.GREEN)
                    break
                time.sleep(2)
            if not counted_s3:
                log("STEP3_WARN", f"Monetag phản hồi: {r_s3}", Fore.YELLOW)

            # --- HOÀN TẤT VÀ NHẬN CÁ CẤP 3 (+12⚡) ---
            r_fin = self.post("/api/fish/finish", {"session_id": ses_id})
            if r_fin.get("ok") and r_fin.get("fish"):
                f = r_fin.get("fish", {})
                self.state = r_fin.get("state", self.state)
                power_add = f.get('power', 12)
                total_power = self.state.get('power', {}).get('total', 0)
                earn_h = self.state.get('earn', {}).get('per_hour', 0)
                return True, f"🎉🎉🎉 ĐÃ NHẬN THÀNH CÔNG CÁ KHỦNG CẤP {f.get('tier')} (+{power_add}⚡)! Tổng Sức Mạnh: {total_power}⚡ | Tốc độ đào: {float(earn_h):.8f} TON/h"
            else:
                return False, f"Lỗi hoàn tất: {r_fin.get('close_reason') or r_fin}"

        except Exception as e:
            self.post("/api/fish/finish", {"session_id": ses_id})
            return False, f"Lỗi trong quá trình xem QC: {e}"

    def ping(self):
        return self.post("/api/ping", {})

# ---------------------------------------------------------------------------
#  3. VÒNG LẶP CHÍNH AUTO PLAY 24/7 NON-STOP
# ---------------------------------------------------------------------------
def run_bot():
    print(f"""
{Fore.CYAN}======================================================================
  🌊 BOT AUTO MOONPOOL 3D AQUARIUM 24/7 (@MoonpoolGameBot) - ACC 1 🐟
  - CẬP NHẬT MỚI: COOLDOWN 1 PHÚT (60s) - BỎ GIỚI HẠN CÁ (MAX 1.000 CÁ/NGÀY)
  - CHẾ ĐỘ: CHUYÊN CÀY CÁ KHỦNG +12⚡ (TIER 3) LIÊN TỤC KHÔNG DỪNG
  - Tự động lấy InData 100% qua Telethon StringSession
  - Vượt chuỗi 3 QC (Adsgram + Gigapub + Monetag) nhận ngay +12⚡
  - Tự động Thu hoạch vỏ Hàu TON liên tục mỗi khi có tiền
  - Tự động bàn giao ca sau 4.8 giờ để cày thông suốt 24/7
======================================================================{Style.RESET_ALL}
    """)

    start_bot_time = time.time()
    handover_triggered = False

    while True:
        elapsed_total = time.time() - start_bot_time
        if elapsed_total > MAX_RUNTIME_SECONDS - 600 and not handover_triggered:
            trigger_next_shift()
            handover_triggered = True

        if elapsed_total >= MAX_RUNTIME_SECONDS:
            log("LIFETIME", f"Đã chạy đủ {MAX_RUNTIME_SECONDS} giây (4.8h). Nhường slot cho phiên mới tiếp quản 24/7...", Fore.MAGENTA)
            break

        log("AUTH", "Đang kết nối Telegram lấy tgWebAppData tươi mới...", Fore.CYAN)
        init_data = asyncio.run(fetch_fresh_init_data())
        if not init_data:
            log("RETRY", "Không lấy được init_data, thử lại sau 20 giây...", Fore.YELLOW)
            time.sleep(20)
            continue

        mp = MoonpoolBot(init_data)
        ok, res = mp.auth()
        if not ok:
            if isinstance(res, dict) and res.get("code") == "banned":
                log("BANNED", f"❌ TÀI KHOẢN ĐÃ BỊ GAME MOONPOOL KHÓA (BANNED): {res.get('error')}", Fore.RED)
                log("BANNED", "Máy chủ Moonpool quét thấy cày cá vượt ngưỡng. Bot tự động dừng hẳn để tránh tốn tài nguyên!", Fore.YELLOW)
                return
            log("AUTH_ERR", f"Đăng nhập thất bại: {res}", Fore.RED)
            time.sleep(20)
            continue

        user = mp.state.get("user", {})
        bal = mp.state.get("balance", "0")
        power = mp.state.get("power", {}).get("total", 0)
        earn_h = mp.state.get("earn", {}).get("per_hour", "0")

        log("LOGIN", f"Đăng nhập thành công: {Fore.YELLOW}@{user.get('username', 'N/A')}{Style.RESET_ALL} (ID: {user.get('telegram_id')})", Fore.GREEN)
        log("STATUS", f"💰 Số dư: {Fore.GREEN}{float(bal):.8f} TON{Style.RESET_ALL} | ⚡ Sức mạnh: {Fore.CYAN}{power} Power{Style.RESET_ALL} | 🚀 Tốc độ: {Fore.YELLOW}{float(earn_h):.8f} TON/h{Style.RESET_ALL}", Fore.GREEN)

        session_start = time.time()

        while time.time() - session_start < 1800:
            # Kiểm tra bàn giao ca
            elapsed_now = time.time() - start_bot_time
            if elapsed_now > MAX_RUNTIME_SECONDS - 600 and not handover_triggered:
                trigger_next_shift()
                handover_triggered = True

            if elapsed_now >= MAX_RUNTIME_SECONDS:
                break

            st = mp.get_state()
            if not st:
                log("WARN", "Không lấy được trạng thái game, thử kết nối lại...", Fore.YELLOW)
                time.sleep(5)
                break

            vault = st.get("vault", {})
            pending_ton = float(vault.get("pending", 0))
            is_claimable = vault.get("claimable", False)
            cur_bal = float(st.get("balance", 0))
            total_power = st.get("power", {}).get("total", 0)

            # 1. TỰ ĐỘNG THU HOẠCH HÀU: Cứ có TON trong vỏ Hàu là thu hoạch ngay
            if is_claimable and pending_ton > 0.000001:
                c_ok, c_res = mp.claim_vault()
                if c_ok:
                    amt = float(c_res.get("amount", 0))
                    new_bal = float(c_res.get("state", {}).get("balance", 0))
                    log("HARVEST", f"🎉 Thu hoạch vỏ Hàu: +{amt:.8f} TON! Số dư mới: {Fore.GREEN}{new_bal:.8f} TON{Style.RESET_ALL}", Fore.GREEN)

            # 2. CHUYÊN TẬP TRUNG THẺ CÁ CẤP 3 (+12⚡ POWER)
            cards = st.get("cards", [])
            daily = st.get("daily", {})
            left_today = daily.get("left", 1000)

            # Tìm đúng thẻ cấp 3 (+12⚡)
            card3 = None
            for c in cards:
                if c.get("tier") == 3 or c.get("power") == 12:
                    card3 = c
                    break

            if left_today <= 0:
                log("DAILY_CAP", "Đã đạt giới hạn tối đa hôm nay! Tiếp tục treo thu hoạch TON 24/7...", Fore.GREEN)
                time.sleep(15)
            elif card3:
                cooldown_sec = card3.get("cooldown_left_sec", 0)
                is_ready = card3.get("ready", False)

                if is_ready or cooldown_sec <= 0:
                    log("TIER3_READY", f"Thẻ cá Cấp 3 (+12⚡) sẵn sàng (Còn lại: {left_today})! Bắt đầu xem QC...", Fore.CYAN)
                    f_ok, f_msg = mp.watch_ads_and_claim_tier3_fish()
                    if f_ok:
                        log("FISH_WIN", f"{f_msg}", Fore.GREEN)
                        time.sleep(5)
                        continue
                    else:
                        log("FISH_NOTE", f"{f_msg}", Fore.YELLOW)
                        time.sleep(10)
                        continue
                else:
                    log("WAIT_12P", f"⏱ Hồi chiêu thẻ +12⚡: còn {cooldown_sec}s | Hàu: {pending_ton:.8f} TON | Power: {Fore.CYAN}{total_power}⚡{Style.RESET_ALL} | Ví: {Fore.GREEN}{cur_bal:.8f} TON{Style.RESET_ALL}", Fore.LIGHTBLACK_EX)
                    sleep_t = min(max(2, cooldown_sec + 1), 15)
                    time.sleep(sleep_t)
            else:
                log("WARN", "Không tìm thấy thẻ cá Cấp 3 trong danh sách thẻ!", Fore.YELLOW)
                time.sleep(10)

            # Heartbeat ping
            mp.ping()

if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\nĐã dừng bot an toàn.")
