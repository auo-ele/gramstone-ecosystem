#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  BOT AUTO HASHLANE ($TON) 24/7 - KHAI THÁC & THU HOẠCH ĐIỂM TỰ ĐỘNG
  Platform: HashLane Mini App (https://46-101-192-249.sslip.io/app/)
  Telegram Bot: @hashlane_bot
  
  TÍNH NĂNG TỰ ĐỘNG HÓA 100%:
    1. Chuẩn hóa mã băm thiết bị X-Device SHA-256 + X-Tz-Offset.
    2. Tự động điểm danh nhận điểm & Gems hàng ngày (/api/checkin).
    3. Tự động quét và hoàn thành TẤT CẢ các nhiệm vụ 1 lần & social tasks (/api/tasks/start & check).
    4. Đối với kênh/nhóm Telegram: Join bằng Telethon, lập tức đưa vào Lưu trữ (Archive folder_id: 1)
       và TUYỆT ĐỐI GIỮ VĨNH VIỄN, KHÔNG BAO GIỜ OUT.
    5. Tự động kiểm tra trạng thái mỏ đào (/api/me).
    6. Tự động THU HOẠCH ĐIỂM (/api/mining/collect) khi mỏ đạt 100 điểm (Full).
    7. Tự động KÍCH HOẠT VÒNG ĐÀO MỚI (/api/mining/start) ngay sau khi thu hoạch.
    8. Vòng lặp 24/7 liên tục (session ~5h, MAX_RUNTIME_SECONDS: 17500, tự động chuyển giao ca tiếp theo).
=============================================================================
"""

import os
import sys
import time
import json
import random
import hashlib
import asyncio
import urllib.parse
import requests
from colorama import init, Fore, Style

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestWebViewRequest, ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.folders import EditPeerFoldersRequest
from telethon.tl.types import InputFolderPeer
from telethon.errors import UserAlreadyParticipantError, FloodWaitError, InviteHashExpiredError

init(autoreset=True)

_raw_id = os.getenv("TELEGRAM_API_ID", "").strip()
API_ID = int(_raw_id) if _raw_id.isdigit() else 34333329
API_HASH = os.getenv("TELEGRAM_API_HASH", "").strip() or "4f9371f95000578c84dbc670aaf1f819"

DEFAULT_SESSION_ACC1 = (
    "1BVtsOHIBuxmpWiBJ9hvwV9pSrzWw5U2I5Fe20Ww8l1LCk9rnsG6T6lLZEJXZE1JJC_qUH_yyWHnRoedRNI5lJYnfjRN4gyGeDrCxquDU12ZflrpCz0VLhMZx2C0LlyUCy2eHRSRE1wUCpEYZaymL0P7Z9eAHwMy4Oogewh5TqyO4x4MF6j0yTq8Zvfpv43O4aQDzErNv3GRqpx8DXBcOJIMP9yVhq-Mby5VH5J9cF-h-bJ5ws3xKjA4GY7YKjHxDt9OI-Zr7mr-V3qZy99UxJooThJj51f2RqOKhODdLh9XZQ0ygSoAd3iFAZDOPMEo8Ch5TrrzLXi2Q3N0HorIL1JfV0xoFQlY="
)
STRING_SESSION = (
    os.getenv("TELEGRAM_STRING_SESSION")
    or os.getenv("TELEGRAM_STRING_SESSION_ACC1")
    or os.getenv("STRING_SESSION")
    or DEFAULT_SESSION_ACC1
)

API_BASE = "https://46-101-192-249.sslip.io/api"
SESSION_FILE_PATH = os.getenv("TELEGRAM_SESSION_PATH", "C:/Users/Administrator/Downloads/kiemtien_autoplay/telepet_acc1.session")

def log(tag, msg, color=Fore.WHITE):
    t_str = time.strftime('%H:%M:%S')
    print(f"{Fore.LIGHTBLACK_EX}[{t_str}]{Style.RESET_ALL} {color}[{tag:<12}]{Style.RESET_ALL} {msg}", flush=True)

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
                log("TG_JOIN", "ℹ️ Đã ở trong nhóm từ trước.", Fore.CYAN)
                try:
                    ent = await client.get_entity(target)
                    input_peer = await client.get_input_entity(ent)
                    await client(EditPeerFoldersRequest(folder_peers=[InputFolderPeer(peer=input_peer, folder_id=1)]))
                    log("TG_ARCHIVE", "📁 Đã đưa vào Lưu trữ (Archive) - Giữ vĩnh viễn không out!", Fore.MAGENTA)
                except Exception:
                    pass
                await asyncio.sleep(1)
                return True
            except InviteHashExpiredError:
                log("TG_JOIN", f"⚠️ Link invite đã hết hạn: {target}", Fore.YELLOW)
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
            log("TG_JOIN", f"✅ Đã tham gia @{username} (ID: {entity.id}) thành công!", Fore.GREEN)
        except UserAlreadyParticipantError:
            log("TG_JOIN", f"ℹ️ Đã có mặt trong @{username} (ID: {entity.id}).", Fore.CYAN)
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

class HashLaneBot:
    def __init__(self, string_session=None, session_path=None):
        self.string_session = string_session or STRING_SESSION
        self.session_path = session_path or SESSION_FILE_PATH
        self.client = None
        self.init_data = None
        self.username = None
        self.points = 0
        self.gems = 0
        
        parts = [
            "Mozilla/5.0 (Linux; Android 14; SM-S928B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.6778.135 Mobile Safari/537.36 Telegram-Android/11.5.0",
            "vi-VN",
            "384x854x24",
            "2.8125",
            "Asia/Ho_Chi_Minh",
            "8",
            "8",
            "Linux armv8l",
            "android"
        ]
        self.ua = parts[0]
        self.dev_fp = hashlib.sha256("|".join(parts).encode('utf-8')).hexdigest()

    async def get_tg_client(self):
        if self.client and self.client.is_connected():
            return self.client
        await asyncio.sleep(random.uniform(3, 15))
        if self.session_path and os.path.exists(self.session_path):
            self.client = TelegramClient(self.session_path, API_ID, API_HASH)
        else:
            self.client = TelegramClient(StringSession(self.string_session), API_ID, API_HASH)
        for attempt in range(6):
            try:
                await self.client.connect()
                break
            except Exception as e:
                if "AuthKeyDuplicated" in str(e) or "auth key" in str(e).lower():
                    wait_sec = random.uniform(8, 15) * (attempt + 1)
                    log("TG_WAIT", f"⚠️ Trùng session IP ({e}), đợi {wait_sec:.1f}s thử lại...", Fore.YELLOW)
                    await asyncio.sleep(wait_sec)
                else:
                    raise
        return self.client

    async def disconnect_tg(self):
        if self.client:
            try:
                if self.client.is_connected():
                    await self.client.disconnect()
            except Exception:
                pass
            self.client = None

    async def fetch_tg_init_data(self):
        log("TELEGRAM", "Đang kết nối Telegram để lấy tgWebAppData HashLane...", Fore.CYAN)
        for attempt in range(8):
            try:
                client = await self.get_tg_client()
                if not await client.is_user_authorized():
                    log("TELEGRAM", "❌ Phiên Telegram không được ủy quyền!", Fore.RED)
                    await self.disconnect_tg()
                    return False

                bot_entity = await client.get_entity("hashlane_bot")
                res = await client(RequestWebViewRequest(
                    peer=bot_entity,
                    bot=bot_entity,
                    url="https://46-101-192-249.sslip.io/app/",
                    platform="android"
                ))

                frag = res.url.split("#tgWebAppData=")[1].split("&tgWebAppVersion")[0]
                self.init_data = urllib.parse.unquote(frag)
                params = dict(urllib.parse.parse_qsl(self.init_data))
                user_obj = json.loads(params.get("user", "{}"))
                self.username = user_obj.get("username", str(user_obj.get("id")))
                log("TELEGRAM", f"✅ Lấy init_data thành công cho @{self.username}", Fore.GREEN)
                return True
            except Exception as e:
                await self.disconnect_tg()
                if "AuthKeyDuplicated" in str(e) or "auth key" in str(e).lower():
                    wait_sec = random.uniform(10, 20) * (attempt + 1)
                    log("TG_WAIT", f"⚠️ Xung đột IP session ({e}), chờ {wait_sec:.1f}s thử lại...", Fore.YELLOW)
                    await asyncio.sleep(wait_sec)
                else:
                    log("TELEGRAM_ERR", f"Lỗi lấy WebApp Data: {e}", Fore.RED)
                    if attempt < 3:
                        await asyncio.sleep(5)
                    else:
                        return False
        return False

    def get_headers(self):
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Init-Data": self.init_data,
            "X-Device": self.dev_fp,
            "X-Tz-Offset": "420",
            "User-Agent": self.ua,
            "Origin": "https://46-101-192-249.sslip.io",
            "Referer": "https://46-101-192-249.sslip.io/app/"
        }

    def get_state(self):
        try:
            r = requests.get(f"{API_BASE}/me", headers=self.get_headers(), timeout=12)
            if r.status_code == 200:
                data = r.json()
                if data.get("ok"):
                    d = data.get("data", {})
                    u = d.get("user", {})
                    b = d.get("balances", {})
                    self.points = b.get("points", 0)
                    self.gems = b.get("gems", 0)
                    m = d.get("mining", {})
                    ses = m.get("session", {})
                    earned = ses.get("earned", 0)
                    capacity = ses.get("capacity", 100)
                    is_ready = ses.get("ready", False)
                    log("STATE", f"👤 User: @{u.get('username')} | Điểm: {self.points} | Gems: {self.gems} | Kho đào: {earned}/{capacity} (Sẵn sàng: {is_ready})", Fore.CYAN)
                    return d
            else:
                log("STATE_ERR", f"Lỗi lấy trạng thái HTTP {r.status_code}", Fore.RED)
        except Exception as e:
            log("STATE_ERR", f"Ngoại lệ get_state: {e}", Fore.RED)
        return None

    def checkin(self):
        try:
            r = requests.post(f"{API_BASE}/checkin", headers=self.get_headers(), json={}, timeout=10)
            if r.status_code == 200:
                d = r.json().get("data", {})
                log("CHECKIN", f"🎉 Điểm danh thành công Ngày {d.get('day', 1)}: +{d.get('points', 0)} Điểm!", Fore.GREEN)
            elif r.status_code == 409:
                log("CHECKIN", "ℹ️ Hôm nay đã điểm danh rồi.", Fore.LIGHTBLACK_EX)
        except Exception:
            pass

    async def scan_and_claim_tasks(self):
        """Quét và hoàn thành tất cả nhiệm vụ HashLane (Telegram channels đưa vào Archive vĩnh viễn)"""
        try:
            r = requests.get(f"{API_BASE}/tasks?tg_platform=android", headers=self.get_headers(), timeout=12)
            if r.status_code == 200:
                data = r.json().get("data", {})
                tasks = data.get("tasks", [])
                log("TASKS", f"📋 Quét được {len(tasks)} nhiệm vụ HashLane...", Fore.CYAN)
                for task in tasks:
                    t_id = task.get("id")
                    t_state = task.get("state")
                    t_title = task.get("title", f"Task #{t_id}")
                    if t_state == "done":
                        continue
                    
                    log("TASK", f"👉 Đang thực hiện nhiệm vụ '{t_title}' (ID: {t_id}, State: {t_state})...", Fore.YELLOW)
                    target_url = task.get("url") or task.get("link") or task.get("action_url") or task.get("channel") or task.get("group")
                    if not target_url and t_state == "new":
                        try:
                            r_s = requests.post(f"{API_BASE}/tasks/start", headers=self.get_headers(), json={"id": t_id}, timeout=10)
                            if r_s.status_code == 200:
                                res_data = r_s.json().get("data", {})
                                target_url = res_data.get("url") or res_data.get("link")
                        except Exception:
                            pass
                    
                    if target_url and ("t.me" in str(target_url) or "@" in str(target_url) or "tg://" in str(target_url)):
                        client = await self.get_tg_client()
                        await tg_join_and_archive(client, target_url)
                        log("TASK", "⏳ Chờ 3s xác thực nhiệm vụ Telegram...", Fore.CYAN)
                        await asyncio.sleep(3)
                    else:
                        await asyncio.sleep(2)
                    
                    r_c = requests.post(f"{API_BASE}/tasks/check", headers=self.get_headers(), json={"id": t_id}, timeout=10)
                    if r_c.status_code == 200:
                        cd = r_c.json().get("data", {})
                        new_p = cd.get("balances", {}).get("points", self.points)
                        log("TASK_CLAIM", f"🎉 HOÀN THÀNH NHIỆM VỤ '{t_title}'! Điểm mới: {new_p}", Fore.GREEN)
                    await asyncio.sleep(2)
        except Exception as e:
            log("TASKS_ERR", f"Lỗi quét tasks HashLane: {e}", Fore.RED)

    def collect_and_restart_mining(self, state_data):
        m = state_data.get("mining", {}) if state_data else {}
        ses = m.get("session")
        if not ses:
            log("MINING", "▶️ Chưa có phiên đào, tiến hành khởi động máy đào...", Fore.YELLOW)
            try:
                r = requests.post(f"{API_BASE}/mining/start", headers=self.get_headers(), json={}, timeout=10)
                if r.status_code == 200:
                    log("MINING", "✅ Đã bắt đầu ca đào mới 3600s (100 điểm/giờ)!", Fore.GREEN)
            except Exception as e:
                log("MINING_ERR", f"Lỗi start mining: {e}", Fore.RED)
            return

        is_ready = ses.get("ready", False)
        earned = ses.get("earned", 0)
        capacity = ses.get("capacity", 100)

        if is_ready or earned >= capacity:
            log("COLLECT", f"⛏️ Kho đào đã đầy ({earned}/{capacity} điểm). Tiến hành thu hoạch...", Fore.YELLOW)
            try:
                r_c = requests.post(f"{API_BASE}/mining/collect", headers=self.get_headers(), json={"double": False}, timeout=12)
                if r_c.status_code == 200:
                    cd = r_c.json().get("data", {})
                    self.points = cd.get("balance", self.points + earned)
                    log("COLLECT", f"🎉 THU HOẠCH THÀNH CÔNG +{cd.get('points', earned)} ĐIỂM! Số dư mới: {self.points} điểm.", Fore.GREEN)
                    
                    new_ses = cd.get("session")
                    if not new_ses or new_ses.get("earned", 0) > 0:
                        requests.post(f"{API_BASE}/mining/start", headers=self.get_headers(), json={}, timeout=10)
                else:
                    log("COLLECT_ERR", f"Lỗi thu hoạch: {r_c.text[:100]}", Fore.YELLOW)
            except Exception as e:
                log("COLLECT_ERR", f"Lỗi collect: {e}", Fore.RED)
        else:
            log("MINING", f"⏳ Máy đào đang hoạt động: {earned}/{capacity} điểm. Vòng đào tiếp theo sẽ đầy sau.", Fore.CYAN)

    async def run_cycle(self):
        ok = await self.fetch_tg_init_data()
        if not ok:
            return
        
        state = self.get_state()
        if not state:
            return

        self.checkin()
        await self.scan_and_claim_tasks()
        await self.disconnect_tg()
        self.collect_and_restart_mining(state)

def trigger_next_shift(workflow_file="hashlane_acc4.yml"):
    repo = (os.getenv("GITHUB_REPOSITORY") or "auo-ele/gramstone-ecosystem").strip()
    wf = (os.getenv("WORKFLOW_FILE") or workflow_file).strip()
    pat = (os.getenv("GH_PAT") or os.getenv("GITHUB_TOKEN") or "").strip()
    if not wf or not pat:
        log("HANDOVER", "Không có WORKFLOW_FILE hoặc GitHub Token để retrigger.", Fore.YELLOW)
        return False
    log("HANDOVER", f"🔄 Chuẩn bị chuyển giao ca làm việc tiếp theo trên {repo} ({wf})...", Fore.CYAN)
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{wf}/dispatches"
    headers = {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        r = requests.post(url, json={"ref": "main"}, headers=headers, timeout=15)
        if r.status_code in [200, 204]:
            log("HANDOVER", f"✅ Đã kích hoạt thành công ca chạy tiếp theo trên {repo} ({wf})!", Fore.GREEN)
            return True
        else:
            log("HANDOVER", f"Phản hồi dispatch: {r.status_code} {r.text}", Fore.YELLOW)
    except Exception as e:
        log("HANDOVER", f"Lỗi retrigger: {e}", Fore.RED)
    return False

async def run_loop_247(bot_instance, interval_mins=5):
    raw_rt = os.getenv("MAX_RUNTIME_SECONDS", "17500").strip()
    max_runtime = int(raw_rt) if raw_rt.isdigit() else 17500
    start_time = time.time()
    cycle = 1
    last_tasks_check = 0
    handover_done = False
    
    log("LOOP", "🔥 KHỞI ĐỘNG VÒNG LẶP AUTO HASHLANE 24/7 (TASKS + CHECKIN + MINING AUTO-RESTART)!", Fore.GREEN)
    
    ok = await bot_instance.fetch_tg_init_data()
    if not ok:
        log("INIT_ERR", "Không thể lấy init_data ban đầu.", Fore.RED)
        return

    # Quét nhiệm vụ 1 lần ngay đầu phiên
    await bot_instance.scan_and_claim_tasks()
    await bot_instance.disconnect_tg()
    last_tasks_check = time.time()

    while True:
        elapsed = time.time() - start_time
        if elapsed >= max_runtime - 300 and not handover_done:
            log("HANDOVER", f"⏰ Đã trực {elapsed/3600:.1f}h. Tự động chuyển giao ca tiếp theo...", Fore.CYAN)
            trigger_next_shift("hashlane_acc4.yml")
            handover_done = True

        if elapsed >= max_runtime:
            log("HANDOVER", f"⏰ Hoàn tất ca trực {max_runtime}s. Bàn giao runner 24/7 thành công!", Fore.GREEN)
            break

        now = time.time()
        log("LOOP", f"🌀 === BẮT ĐẦU CHU KỲ #{cycle} (HashLane 24/7) ===", Fore.MAGENTA)
        try:
            state = bot_instance.get_state()
            if state:
                bot_instance.checkin()
                bot_instance.collect_and_restart_mining(state)
        except Exception as e:
            log("CYCLE_ERR", f"Lỗi chu kỳ #{cycle}: {e}", Fore.RED)

        # Quét lại nhiệm vụ mỗi 30 phút
        if now - last_tasks_check >= 1800:
            await bot_instance.scan_and_claim_tasks()
            await bot_instance.disconnect_tg()
            last_tasks_check = now

        cycle += 1
        sleep_sec = random.randint(180, 300)
        log("LOOP", f"⏳ Nghỉ {sleep_sec}s trước lần kiểm tra tiếp theo (Đã trực {int(elapsed//60)}m)...", Fore.LIGHTBLACK_EX)
        await asyncio.sleep(sleep_sec)

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Bot Auto HashLane ($TON) 24/7")
    parser.add_argument("--loop", type=int, default=5, help="Số phút nghỉ giữa các chu kỳ")
    args, _ = parser.parse_known_args()

    print(Fore.YELLOW + """
=============================================================================
  BOT AUTO HASHLANE ($TON) 24/7 - CHUẨN X-DEVICE FINGERPRINT
  Tự động Quét Tasks & Archive Telegram | Thu Hoạch 100 Điểm Kho | Bắt Đầu Vòng Mới
=============================================================================
    """ + Style.RESET_ALL)
    
    bot = HashLaneBot()
    run_247 = os.getenv("RUN_247", "1") == "1"
    if run_247:
        await run_loop_247(bot, interval_mins=args.loop)
    else:
        await bot.run_cycle()

if __name__ == "__main__":
    asyncio.run(main())
