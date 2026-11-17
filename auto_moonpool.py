#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  BOT AUTO PLAY 24/7 SIÊU CẤP - MOONPOOL 3D AQUARIUM (@MoonpoolGameBot)
  Platform: Moonpool 3D Aquarium (https://moonpool.64-226-82-60.sslip.io/)
  Bot     : @MoonpoolGameBot (Telegram WebApp App: 'play')
  Target  : CÀY CÁ KHỦNG CẤP 3 (+12⚡ POWER) & QUÉT NHIỆM VỤ 1 LẦN NON-STOP 24/7
  
  TÍNH NĂNG TỰ ĐỘNG HÓA TOÀN DIỆN 100%:
    1. Quét và hoàn thành tất cả nhiệm vụ 1 lần (Channel, Group, Invite, Daily Streak).
    2. Kênh/nhóm Telegram được join qua Telethon, lập tức đưa vào Lưu trữ (Archive folder_id: 1)
       và TUYỆT ĐỐI GIỮ VĨNH VIỄN, KHÔNG BAO GIỜ OUT.
    3. CÀY CÁ KHỦNG TIER 3 (+12⚡) liên tục không dừng qua chuỗi QC Moonpool.
    4. Tự động thu hoạch vỏ Hàu TON liên tục mỗi khi có tiền.
    5. Tự động chuyển giao ca sau 4.8 giờ để cày thông suốt 24/7 không gián đoạn.
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
from telethon.tl.functions.messages import RequestAppWebViewRequest, ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.folders import EditPeerFoldersRequest
from telethon.tl.types import InputBotAppShortName, InputFolderPeer
from telethon.errors import UserAlreadyParticipantError, FloodWaitError, InviteHashExpiredError

urllib3.disable_warnings()
init(autoreset=True)

# ---------------------------------------------------------------------------
#  CẤU HÌNH HỆ THỐNG
# ---------------------------------------------------------------------------
_raw_id = os.getenv("TELEGRAM_API_ID", "").strip()
API_ID = int(_raw_id) if _raw_id.isdigit() else 34333329
API_HASH = os.getenv("TELEGRAM_API_HASH", "").strip() or "4f9371f95000578c84dbc670aaf1f819"

KNOWN_GOOD_STRING_SESSION = (
    os.getenv("TELEGRAM_STRING_SESSION") or
    "1BVtsOMMBu6WXSbH0pQyd4FdW0Fc-zqEWvx3RMUB53LJeKWWB6t61lV-p3TcR3k2psUxcUtbmfdeC1jATK8f7i5jIX_eiplenW3A-h9ALZB7cq9PodKB_KJP4fhOMNeb43G8H7SbF5hDnrdPOiFMEYS1tbjOrmzNu_UyzNe64ndfKb9SSpsTZtrKbo3ryx4x7gpXHrrfISsyMUm6gOjEl9KbyvWCt94yu_spYicw2YsAGCMlKmEYqGIIIpItqZ4VJrdwPtzS__VudhSQzwM56cZMwgTsicw0NA_zaRmgZ4sJEU0ADeMMutBhDtL-kQsJQUb145Ybagpel5xAK86xAKjaeQau5R1I="
)

REPO_NAME = (os.getenv("GITHUB_REPOSITORY") or "auo-ele/gramstone-ecosystem").strip()
WORKFLOW_NAME = (os.getenv("WORKFLOW_FILE") or "moonpool_acc4.yml").strip()

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
            return ss.save()
    except Exception:
        pass

    return KNOWN_GOOD_STRING_SESSION

async def tg_join_and_archive(client, target):
    """
    Tham gia kenh/nhom Telegram bang Telethon va dua NGAY LAP TUC vao Luu tru (Archive folder_id: 1).
    TUYET DOI KHONG ROI KENH (Never leave - giu vinh vien).
    """
    if not target or not client:
        return None
    target = str(target).strip()
    try:
        if target.startswith("{") and "}" in target:
            try:
                td = json.loads(target)
                target = td.get("url") or td.get("link") or td.get("channel") or td.get("username") or ""
            except Exception:
                pass

        if "domain=" in target:
            m = re.search(r'domain=([a-zA-Z0-9_]+)', target)
            if m:
                target = m.group(1)

        if "/+" in target or "/joinchat/" in target:
            invite_hash = target.split("/+")[-1] if "/+" in target else target.split("/joinchat/")[-1]
            invite_hash = invite_hash.split("/")[0].split("?")[0].strip()
            log("TG_JOIN", f"➕ Đang tham gia nhóm kín qua invite: {invite_hash[:10]}...", Fore.CYAN)
            try:
                updates = await client(ImportChatInviteRequest(invite_hash))
                if hasattr(updates, "chats") and updates.chats:
                    chat_obj = updates.chats[0]
                    title = getattr(chat_obj, "title", "Nhóm kín")
                    log("TG_JOIN", f"✅ Đã tham gia '{title}' (ID: {chat_obj.id}) thành công!", Fore.GREEN)
                    try:
                        input_peer = await client.get_input_entity(chat_obj)
                        await client(EditPeerFoldersRequest(folder_peers=[InputFolderPeer(peer=input_peer, folder_id=1)]))
                        log("TG_ARCHIVE", f"📁 Đã đưa '{title}' vào Lưu trữ (Archive) - Giữ vĩnh viễn không out!", Fore.MAGENTA)
                    except Exception:
                        pass
                    await asyncio.sleep(2)
                    return chat_obj
            except UserAlreadyParticipantError:
                ent = await client.get_entity(target)
                log("TG_JOIN", "ℹ️ Đã ở trong nhóm từ trước.", Fore.CYAN)
                try:
                    input_peer = await client.get_input_entity(ent)
                    await client(EditPeerFoldersRequest(folder_peers=[InputFolderPeer(peer=input_peer, folder_id=1)]))
                    log("TG_ARCHIVE", "📁 Đã đưa vào Lưu trữ (Archive) - Giữ vĩnh viễn không out!", Fore.MAGENTA)
                except Exception:
                    pass
                await asyncio.sleep(1)
                return True
            except InviteHashExpiredError:
                log("TG_WARN", f"⚠️ Link invite đã hết hạn: {target}", Fore.YELLOW)
                return None
            except Exception as e:
                log("TG_JOIN_ERR", f"⚠️ Không thể Join invite: {e}", Fore.YELLOW)
                return None

        username = target.replace("https://", "").replace("http://", "").replace("telegram.me/", "").replace("t.me/", "").replace("tg://resolve?domain=", "").replace("@", "").split("/")[0].split("?")[0].strip()
        if not username or username.lower() in ("i", "addstickers", "proxy", "socks", "share", "boost"):
            return None

        entity = await client.get_entity(username)
        title = getattr(entity, "title", username)
        log("TG_JOIN", f"➕ Đang tham gia kênh/nhóm @{username} ('{title}')...", Fore.CYAN)
        try:
            await client(JoinChannelRequest(entity))
            log("TG_JOIN", f"✅ Đã tham gia @{username} thành công!", Fore.GREEN)
        except UserAlreadyParticipantError:
            log("TG_JOIN", f"ℹ️ Đã có mặt trong @{username}.", Fore.CYAN)
        except Exception as e:
            log("TG_JOIN_ERR", f"⚠️ Lỗi join @{username}: {e}", Fore.YELLOW)

        try:
            input_peer = await client.get_input_entity(entity)
            await client(EditPeerFoldersRequest(folder_peers=[InputFolderPeer(peer=input_peer, folder_id=1)]))
            log("TG_ARCHIVE", f"📁 Đã đưa '{title}' vào Lưu trữ (Archive) - Giữ vĩnh viễn không out!", Fore.MAGENTA)
        except Exception as e:
            log("TG_ARCHIVE_ERR", f"⚠️ Không thể archive: {e}", Fore.YELLOW)
        await asyncio.sleep(2)
        return entity

    except FloodWaitError as e:
        log("TG_FLOOD", f"⏳ Telegram FloodWait: Cần chờ {e.seconds}s...", Fore.YELLOW)
        await asyncio.sleep(min(e.seconds, 60))
    except Exception as e:
        log("TG_JOIN_ERR", f"⚠️ Không thể xử lý '{target}': {e}", Fore.YELLOW)
    return None

def trigger_next_shift():
    """Tự động trigger dispatch workflow cho ca chạy tiếp theo trên GitHub Actions."""
    repo = REPO_NAME
    wf = WORKFLOW_NAME
    token = os.getenv("GH_PAT") or os.getenv("GITHUB_TOKEN")

    if not token:
        log("HANDOVER", "Không có token GH_PAT để trigger ca tiếp theo.", Fore.YELLOW)
        return False

    url = f"https://api.github.com/repos/{repo}/actions/workflows/{wf}/dispatches"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        r = requests.post(url, headers=headers, json={"ref": "main"}, timeout=15)
        if r.status_code in [200, 204]:
            log("HANDOVER", f"✅ Đã kích hoạt ca chạy tiếp theo trên {repo} ({wf})!", Fore.GREEN)
            return True
        else:
            log("HANDOVER", f"⚠️ Phản hồi dispatch: {r.status_code} {r.text}", Fore.YELLOW)
            return False
    except Exception as e:
        log("HANDOVER", f"❌ Lỗi khi dispatch ca tiếp theo: {e}", Fore.RED)
        return False

# ---------------------------------------------------------------------------
#  1. TELETHON AUTO IN-DATA & CLIENT
# ---------------------------------------------------------------------------
_global_tg_client = None

async def get_tg_client():
    global _global_tg_client
    if _global_tg_client and _global_tg_client.is_connected():
        return _global_tg_client
    await asyncio.sleep(random.uniform(3, 15))
    session_str = get_clean_string_session()
    _global_tg_client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
    for attempt in range(6):
        try:
            await _global_tg_client.connect()
            break
        except Exception as e:
            if "AuthKeyDuplicated" in type(e).__name__ or "authorization key" in str(e).lower() or "auth key" in str(e).lower():
                wait_sec = random.uniform(8, 15) * (attempt + 1)
                log("TG_WAIT", f"⚠️ Trùng session IP ({e}), đợi {wait_sec:.1f}s thử lại...", Fore.YELLOW)
                await asyncio.sleep(wait_sec)
            else:
                raise
    return _global_tg_client

async def disconnect_tg():
    global _global_tg_client
    if _global_tg_client:
        try:
            if _global_tg_client.is_connected():
                await _global_tg_client.disconnect()
        except Exception:
            pass
        _global_tg_client = None

async def fetch_fresh_init_data():
    """Tự động kết nối Telethon lấy init_data mới nhất từ Telegram."""
    try:
        client = await get_tg_client()
        if not await client.is_user_authorized():
            log("AUTH_ERR", "StringSession không hợp lệ hoặc chưa đăng nhập!", Fore.RED)
            await disconnect_tg()
            return None

        bot = await client.get_input_entity(BOT_USERNAME)
        bot_app = InputBotAppShortName(bot_id=bot, short_name=APP_SHORT_NAME)
        res = await client(RequestAppWebViewRequest(peer=bot, app=bot_app, platform="android"))

        frag = urllib.parse.urlparse(res.url).fragment
        init_data = urllib.parse.parse_qs(frag).get("tgWebAppData", [None])[0]
        await disconnect_tg()
        return init_data
    except Exception as e:
        log("TELETHON_ERR", f"Lỗi lấy init_data: {e}", Fore.RED)
        await disconnect_tg()
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
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
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

    async def scan_and_claim_tasks(self, client):
        """Quét và hoàn thành tất cả nhiệm vụ Moonpool (Kênh/Nhóm Telegram đưa vào Archive vĩnh viễn không out)"""
        tasks = self.state.get("tasks", []) if self.state else []
        log("TASKS", f"📋 Quét {len(tasks)} nhiệm vụ Moonpool...", Fore.CYAN)
        for task in tasks:
            t_id = task.get("id")
            status = task.get("status")
            kind = task.get("kind")

            # 1. Join Channel
            if t_id == "channel" and status != "done":
                log("TASK", "👉 Đang thực hiện nhiệm vụ Join Channel Moonpool...", Fore.YELLOW)
                ch = task.get("channel", {})
                target = ch.get("url") or ch.get("link") or (f"@{ch.get('username')}" if ch.get("username") else None)
                if target and client:
                    await tg_join_and_archive(client, target)
                    log("TASK", "⏳ Chờ 3s xác thực tham gia Channel...", Fore.CYAN)
                    await asyncio.sleep(3)
                r = self.post("/api/tasks/channel/check")
                if r.get("ok"):
                    log("TASK_CLAIM", "🎉 HOÀN THÀNH NHIỆM VỤ JOIN CHANNEL! Đã đưa vào Archive vĩnh viễn.", Fore.GREEN)
                    self.state = r.get("state", self.state)
                await asyncio.sleep(2)

            # 2. Join Payout Group
            elif t_id == "group" and status != "done":
                log("TASK", "👉 Đang thực hiện nhiệm vụ Join Group Moonpool...", Fore.YELLOW)
                gr = task.get("group", {})
                target = gr.get("url") or gr.get("link") or (f"@{gr.get('username')}" if gr.get("username") else None)
                if target and client:
                    await tg_join_and_archive(client, target)
                    log("TASK", "⏳ Chờ 3s xác thực tham gia Group...", Fore.CYAN)
                    await asyncio.sleep(3)
                r = self.post("/api/tasks/group/check")
                if r.get("ok"):
                    log("TASK_CLAIM", "🎉 HOÀN THÀNH NHIỆM VỤ JOIN GROUP! Đã đưa vào Archive vĩnh viễn.", Fore.GREEN)
                    self.state = r.get("state", self.state)
                await asyncio.sleep(2)

            # 3. Invite Milestones
            elif kind == "invite" and status == "claimable":
                n = task.get("threshold", 1)
                log("TASK", f"👉 Đang nhận thưởng Invite Milestone {n} bạn...", Fore.YELLOW)
                r = self.post("/api/tasks/invite/claim", {"threshold": n})
                if r.get("ok"):
                    log("TASK_CLAIM", f"🎉 HOÀN THÀNH INVITE MILESTONE {n}! Nhận thưởng power.", Fore.GREEN)
                    self.state = r.get("state", self.state)
                await asyncio.sleep(1)

            # 4. Daily Streak
            elif t_id == "streak" and status == "claimable":
                log("TASK", "👉 Đang nhận thưởng Daily Streak...", Fore.YELLOW)
                r = self.post("/api/tasks/streak/claim")
                if r.get("ok"):
                    rew = r.get("reward", {})
                    log("TASK_CLAIM", f"🎉 ĐÃ NHẬN DAILY STREAK! +{rew.get('ton', 0)} TON, +{rew.get('power', 0)}⚡ Power!", Fore.GREEN)
                    self.state = r.get("state", self.state)
                await asyncio.sleep(1)

            # 5. Generic / Partner tasks
            elif status not in ("done", "completed"):
                target = task.get("url") or task.get("link") or task.get("action_url") or task.get("channel") or task.get("group")
                if isinstance(target, dict):
                    target = target.get("url") or target.get("link") or (f"@{target.get('username')}" if target.get("username") else None)
                if target and ("t.me" in str(target) or "@" in str(target)) and client:
                    await tg_join_and_archive(client, target)
                    await asyncio.sleep(3)
                r = self.post(f"/api/tasks/{t_id}/check")
                if r.get("ok"):
                    log("TASK_CLAIM", f"🎉 HOÀN THÀNH NHIỆM VỤ '{t_id}'!", Fore.GREEN)
                    self.state = r.get("state", self.state)
                await asyncio.sleep(1)

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
            cfg = self.state.get("config", {})
            block_id = cfg.get("networks", {}).get("adsgram", {}).get("block_id") or "56919"

            # --- BƯỚC 1: ADSGRAM ---
            log("STEP1_ADSGRAM", f"Bước 1/3: Đang tải quảng cáo Adsgram (Block: {block_id})...", Fore.YELLOW)
            ad_headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36',
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
async def run_bot():
    print(f"""
{Fore.CYAN}======================================================================
  🌊 BOT AUTO MOONPOOL 3D AQUARIUM 24/7 (@MoonpoolGameBot)
  - Quét & Hoàn Thành Tasks 1 Lần + Telegram Archive vĩnh viễn (folder_id: 1)
  - CHẾ ĐỘ: CHUYÊN CÀY CÁ KHỦNG +12⚡ (TIER 3) LIÊN TỤC KHÔNG DỪNG
  - Tự động lấy InData 100% qua Telethon StringSession
  - Vượt chuỗi 3 QC (Adsgram + Gigapub + Monetag) nhận ngay +12⚡
  - Tự động Thu hoạch vỏ Hàu TON liên tục mỗi khi có tiền
  - Tự động bàn giao ca sau 4.8 giờ để cày thông suốt 24/7
======================================================================{Style.RESET_ALL}
    """)

    start_bot_time = time.time()
    handover_triggered = False
    last_tasks_check = 0

    while True:
        elapsed_total = time.time() - start_bot_time
        if elapsed_total > MAX_RUNTIME_SECONDS - 600 and not handover_triggered:
            trigger_next_shift()
            handover_triggered = True

        if elapsed_total >= MAX_RUNTIME_SECONDS:
            log("LIFETIME", f"Đã chạy đủ {MAX_RUNTIME_SECONDS} giây (4.8h). Nhường slot cho phiên mới tiếp quản 24/7...", Fore.MAGENTA)
            break

        log("AUTH", "Đang kết nối Telegram lấy tgWebAppData tươi mới...", Fore.CYAN)
        init_data = await fetch_fresh_init_data()
        if not init_data:
            log("RETRY", "Không lấy được init_data, thử lại sau 20 giây...", Fore.YELLOW)
            await asyncio.sleep(20)
            continue

        mp = MoonpoolBot(init_data)
        ok, res = mp.auth()
        if not ok:
            if isinstance(res, dict) and res.get("code") == "banned":
                log("BANNED", f"❌ TÀI KHOẢN ĐÃ BỊ GAME MOONPOOL KHÓA (BANNED): {res.get('error')}", Fore.RED)
                return
            log("AUTH_ERR", f"Đăng nhập thất bại: {res}", Fore.RED)
            await asyncio.sleep(20)
            continue

        user = mp.state.get("user", {})
        bal = mp.state.get("balance", "0")
        power = mp.state.get("power", {}).get("total", 0)
        earn_h = mp.state.get("earn", {}).get("per_hour", "0")

        log("LOGIN", f"Đăng nhập thành công: {Fore.YELLOW}@{user.get('username', 'N/A')}{Style.RESET_ALL} (ID: {user.get('telegram_id')})", Fore.GREEN)
        log("STATUS", f"💰 Số dư: {Fore.GREEN}{float(bal):.8f} TON{Style.RESET_ALL} | ⚡ Sức mạnh: {Fore.CYAN}{power} Power{Style.RESET_ALL} | 🚀 Tốc độ: {Fore.YELLOW}{float(earn_h):.8f} TON/h{Style.RESET_ALL}", Fore.GREEN)

        # Quét và hoàn thành nhiệm vụ 1 lần ngay đầu phiên
        tg_client = await get_tg_client()
        await mp.scan_and_claim_tasks(tg_client)
        await disconnect_tg()
        last_tasks_check = time.time()

        session_start = time.time()

        while time.time() - session_start < 1800:
            elapsed_now = time.time() - start_bot_time
            if elapsed_now > MAX_RUNTIME_SECONDS - 600 and not handover_triggered:
                trigger_next_shift()
                handover_triggered = True

            if elapsed_now >= MAX_RUNTIME_SECONDS:
                break

            now = time.time()
            if now - last_tasks_check >= 1800:
                tg_client = await get_tg_client()
                await mp.scan_and_claim_tasks(tg_client)
                await disconnect_tg()
                last_tasks_check = now

            st = mp.get_state()
            if not st:
                log("WARN", "Không lấy được trạng thái game, thử kết nối lại...", Fore.YELLOW)
                await asyncio.sleep(5)
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

            card3 = None
            for c in cards:
                if c.get("tier") == 3 or c.get("power") == 12:
                    card3 = c
                    break

            if left_today <= 0:
                log("DAILY_CAP", "Đã đạt giới hạn tối đa hôm nay! Tiếp tục treo thu hoạch TON 24/7...", Fore.GREEN)
                await asyncio.sleep(15)
            elif card3:
                cooldown_sec = card3.get("cooldown_left_sec", 0)
                is_ready = card3.get("ready", False)

                if is_ready or cooldown_sec <= 0:
                    log("TIER3_READY", f"Thẻ cá Cấp 3 (+12⚡) sẵn sàng (Còn lại: {left_today})! Bắt đầu xem QC...", Fore.CYAN)
                    f_ok, f_msg = mp.watch_ads_and_claim_tier3_fish()
                    if f_ok:
                        log("FISH_WIN", f"{f_msg}", Fore.GREEN)
                        await asyncio.sleep(65)
                        continue
                    else:
                        log("FISH_NOTE", f"{f_msg}", Fore.YELLOW)
                        await asyncio.sleep(60)
                        continue
                else:
                    log("WAIT_12P", f"⏱ Hồi chiêu thẻ +12⚡: còn {cooldown_sec}s | Hàu: {pending_ton:.8f} TON | Power: {Fore.CYAN}{total_power}⚡{Style.RESET_ALL} | Ví: {Fore.GREEN}{cur_bal:.8f} TON{Style.RESET_ALL}", Fore.LIGHTBLACK_EX)
                    sleep_t = min(max(2, cooldown_sec + 1), 15)
                    await asyncio.sleep(sleep_t)
            else:
                log("WARN", "Không tìm thấy thẻ cá Cấp 3 trong danh sách thẻ!", Fore.YELLOW)
                await asyncio.sleep(10)

            mp.ping()

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("\nĐã dừng bot an toàn.")
