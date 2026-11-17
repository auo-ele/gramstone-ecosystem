#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
  BOT AUTO GRAMSTONE ($GRAM / $TON) 24/7 - CHUẨN CƠ CHẾ MỚI MOONPOOL 100%
  Platform: Gramstone Mini App (https://gramstone.46-101-143-24.sslip.io/)
  Telegram Bot: @gramstone_bot
  
  CẬP NHẬT CƠ CHẾ TỰ ĐỘNG HÓA 24/7 & NHIỆM VỤ 1 LẦN:
    1. Tự động quét và hoàn thành tất cả nhiệm vụ 1 lần & social tasks (/api/tasks/complete).
    2. Kênh/nhóm Telegram được join bằng Telethon, lập tức đưa vào Lưu trữ (Archive folder_id: 1)
       và TUYỆT ĐỐI GIỮ VĨNH VIỄN, KHÔNG BAO GIỜ OUT.
    3. CÀY THẺ MỎ TIER 3 (SAFIR) buff +4 GH/s mỗi thẻ (24h) liên tục.
    4. Tự động thu hoạch Kho Mỏ (Vault) khi đủ 100% (3600s) hoàn toàn miễn phí.
    5. Tự động Tap đào đá tối đa 240/240 lượt/ngày.
    6. Tự động điểm danh hàng ngày Streak (/api/streak/claim).
    7. Vòng lặp 24/7 an toàn (session ~5h, MAX_RUNTIME_SECONDS: 17500, tự động re-dispatch ca tiếp theo).
=============================================================================
"""

import os
import sys
import time
import json
import random
import hashlib
import asyncio
import re
import base64
import urllib.parse
import urllib3
import requests
from colorama import init, Fore, Style

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestWebViewRequest, ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.folders import EditPeerFoldersRequest
from telethon.tl.types import InputFolderPeer
from telethon.errors import UserAlreadyParticipantError, FloodWaitError, InviteHashExpiredError

urllib3.disable_warnings()
init(autoreset=True)

# -----------------------------------------------------------------
# CẤU HÌNH HỆ THỐNG
# -----------------------------------------------------------------
_raw_id = os.getenv("TELEGRAM_API_ID", "").strip()
API_ID = int(_raw_id) if _raw_id.isdigit() else 34333329
API_HASH = os.getenv("TELEGRAM_API_HASH", "").strip() or "4f9371f95000578c84dbc670aaf1f819"

DEFAULT_SESSION_ACC1 = "1BVtsOMMBu4twagryqQ2jg8Lq0r5ht_iJ-LHnM5qYYrNYGz6aTkbk6gA42gQZ9ZJs80wXSEzppw8z6RK4eKpp6qtGAegFWNsoEbJpCmmd47phuoQ3YN1DPsxsX2uoWJQ60B18gArjt603YezUARHPh7opveQtVwZR9N9M8O4eSFDDQmFHeglnaqniplilMXYSF1Jr7e9E2XevLm2MkYUv4roxlragUkxtKPlSoLOd0V2JMIKN9A4yOzsRHcdI4H33W1XwP1J9UiQrb52gGxsf3i73f_NzbByCFlZPHh04aTRUhNtLBETfLb5XHLtwoxg5SOt24eSkBDRJOtaPCik32hnP3fQjTrQ="
DEFAULT_SESSION_ACC2 = (
    "1BVtsOHIBuzoeRtBOmpNGh2sdyxpZ5e0nY4MrFe-6KKbmJPaM0YnCJiKRI0L9mEh1C5rwqLQqucj456LRF7vV1YIPjZNqL6JevLM0Ww3FTml1NoKdwsiPINfsy9MbBlBhKOvha7py44L4pK5aEXjwpjpoNj4LaSmtWaPiQPufJuTwPB86f4gYjSeXM3HtxhnFU7MtHR5vbZPBa9N2HQSlt2BMB47q00DbQVtvYA37R3R-TrtV2MtwixL9ozChADFq38NYcw4eRyRwKrkobVLccvz0_hvqgHXiQbrfcFLLRkRGwGlRCB-Ew4YhLLdnCbG1hjGEfxUrp9MRmF0JvS-u20MfAuvlcgQ="
)
STRING_SESSION = (
    os.getenv("TELEGRAM_STRING_SESSION")
    or os.getenv("TELEGRAM_STRING_SESSION_ACC1")
    or os.getenv("STRING_SESSION")
    or DEFAULT_SESSION_ACC1
)

API_BASE = "https://gramstone.46-101-143-24.sslip.io"
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
        # Handle dict / JSON string
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

        # 1. Parse Invite link (+hash hoac joinchat/hash)
        if "/+" in target or "/joinchat/" in target:
            invite_hash = target.split("/+")[-1] if "/+" in target else target.split("/joinchat/")[-1]
            invite_hash = invite_hash.split("/")[0].split("?")[0].strip()
            log("TG_JOIN", f"➕ Đang tham gia nhóm kín (Invite: {invite_hash[:10]}...)...", Fore.CYAN)
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

        # 2. Parse Public Username / URL
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

        # Đưa vào Lưu trữ (Archive folder_id: 1)
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

class GramstoneBot:
    def __init__(self, string_session=None, session_path=None):
        self.string_session = string_session or STRING_SESSION
        self.session_path = session_path or SESSION_FILE_PATH
        self.client = None
        self.init_data = None
        self.user_obj = None
        self.user_id = None
        self.username = None
        self.sig = ""
        self.dcs = ""
        self.balance = 0.0
        self.bonus_ghs = 0.0
        self.total_ghs = 0.0
        
        # Giả lập phần cứng x-gs-fp chuẩn xác
        self.ua = (
            "Mozilla/5.0 (Linux; Android 14; SM-S928B Build/UP1A.231005.007; wv) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.6778.135 "
            "Mobile Safari/537.36 Telegram-Android/11.5.0"
        )
        self.platform = "Linux armv8l"
        self.lang = "vi,en-US;q=0.9"
        self.tz = "Asia/Ho_Chi_Minh"
        self.screen = "384x854x24"
        self.dpr = 2.8125
        self.cores = 8
        self.mem = 8
        self.touch = 5
        self.gpu = "Qualcomm / Adreno (TM) 750"
        self.canvas_sig = "sig"
        
        raw_fp = "||".join(str(x) for x in [
            self.ua, self.platform, self.lang, self.tz, self.screen, self.dpr,
            self.cores, self.mem, self.touch, self.gpu, self.canvas_sig
        ])
        self.fp_hash = hashlib.sha256(raw_fp.encode('utf-8')).hexdigest()

    async def get_tg_client(self):
        if self.client and self.client.is_connected():
            return self.client
        if self.session_path and os.path.exists(self.session_path):
            self.client = TelegramClient(self.session_path, API_ID, API_HASH)
        else:
            self.client = TelegramClient(StringSession(self.string_session), API_ID, API_HASH)
        await self.client.connect()
        return self.client

    async def fetch_tg_init_data(self):
        log("TELEGRAM", "Đang kết nối Telegram để lấy tgWebAppData Gramstone...", Fore.CYAN)
        try:
            client = await self.get_tg_client()
            if not await client.is_user_authorized():
                log("TELEGRAM", "❌ Phiên Telegram không được ủy quyền!", Fore.RED)
                return False

            bot_entity = await client.get_entity("gramstone_bot")
            res = await client(RequestWebViewRequest(
                peer=bot_entity,
                bot=bot_entity,
                url="https://gramstone.46-101-143-24.sslip.io/",
                platform="android"
            ))

            frag = res.url.split("#tgWebAppData=")[1].split("&tgWebAppVersion")[0]
            self.init_data = urllib.parse.unquote(frag)
            params = dict(urllib.parse.parse_qsl(self.init_data))
            self.user_obj = json.loads(params.get("user", "{}"))
            self.user_id = str(self.user_obj.get("id"))
            self.username = self.user_obj.get("username", "")
            self.sig = params.get("signature", "")
            
            # Tính data_check_string
            pairs = []
            for k, v in urllib.parse.parse_qsl(self.init_data):
                if k not in ['hash', 'signature']:
                    pairs.append(f"{k}={v}")
            pairs.sort()
            raw = "\n".join(pairs)
            self.dcs = base64.b64encode(raw.encode('utf-8')).decode('ascii').replace('+', '-').replace('/', '_').rstrip('=')
            
            log("TELEGRAM", f"✅ Lấy init_data thành công cho @{self.username} ({self.user_id})", Fore.GREEN)
            return True
        except Exception as e:
            log("TELEGRAM_ERR", f"Lỗi lấy WebApp Data: {e}", Fore.RED)
            return False

    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "x-telegram-init-data": self.init_data,
            "x-gs-fp": self.fp_hash,
            "User-Agent": self.ua,
            "Origin": API_BASE,
            "Referer": f"{API_BASE}/"
        }

    def authenticate(self):
        device_info = {
            "ua": self.ua,
            "platform": self.platform,
            "tgPlatform": "android",
            "tgVersion": "11.5.0",
            "lang": self.lang,
            "tz": self.tz,
            "screen": self.screen,
            "dpr": self.dpr,
            "cores": self.cores,
            "mem": self.mem,
            "touch": self.touch,
            "gpu": self.gpu
        }
        body = {
            "telegram_id": self.user_id,
            "username": self.username,
            "first_name": self.user_obj.get("first_name", "GramMadenci"),
            "start_param": "",
            "device": device_info
        }
        try:
            r = requests.post(f"{API_BASE}/api/auth", headers=self.get_headers(), json=body, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get("ok"):
                    u = data.get("user", {})
                    self.balance = float(u.get("balance", 0.0))
                    self.bonus_ghs = float(u.get("bonus_ghs", 0))
                    m = data.get("mining", {})
                    self.total_ghs = float(m.get("totalGhs", 100))
                    log("AUTH", f"✅ Đăng nhập Gramstone! User: @{self.username} | Số dư: {self.balance:.6f} TON/GRAM | Tốc độ: {self.total_ghs:.1f} GH/s (Bonus: +{self.bonus_ghs} GH/s)", Fore.GREEN)
                    return data
            log("AUTH_ERR", f"Lỗi đăng nhập HTTP {r.status_code}: {r.text[:120]}", Fore.RED)
        except Exception as e:
            log("AUTH_ERR", f"Ngoại lệ đăng nhập: {e}", Fore.RED)
        return None

    async def scan_and_claim_tasks(self, auth_data):
        """Quét và hoàn thành tất cả nhiệm vụ 1 lần & nhiệm vụ Telegram (Lưu trữ vĩnh viễn không out)"""
        tasks = auth_data.get("tasks", []) if auth_data else []
        if not tasks:
            return
        log("TASKS", f"📋 Quét được {len(tasks)} nhiệm vụ Gramstone...", Fore.CYAN)
        for task in tasks:
            t_id = task.get("id")
            title = task.get("title", f"Task #{t_id}")
            if task.get("isCompleted") or task.get("oneTimeGone"):
                continue
            
            action_url = task.get("action_url") or task.get("url") or task.get("link") or task.get("channel") or task.get("group") or ""
            cat = task.get("category") or ""
            icon = task.get("icon") or ""
            
            log("TASK", f"👉 Đang thực hiện nhiệm vụ: '{title}' (ID: {t_id})...", Fore.YELLOW)
            if "t.me" in str(action_url) or "@" in str(action_url) or cat == "social" or icon == "telegram":
                if action_url:
                    client = await self.get_tg_client()
                    await tg_join_and_archive(client, action_url)
                log("TASK", "⏳ Chờ 3s sau khi tham gia kênh Telegram...", Fore.CYAN)
                await asyncio.sleep(3)
            else:
                await asyncio.sleep(2)
            
            try:
                r = requests.post(
                    f"{API_BASE}/api/tasks/complete",
                    headers=self.get_headers(),
                    json={"telegram_id": self.user_id, "task_id": t_id},
                    timeout=10
                )
                if r.status_code == 200:
                    d = r.json()
                    if d.get("ok"):
                        log("TASK_CLAIM", f"🎉 HOÀN THÀNH NHIỆM VỤ '{title}'! Nhận thưởng thành công.", Fore.GREEN)
                    else:
                        log("TASK_ERR", f"Server báo: {d.get('error', 'Chưa xong')}", Fore.YELLOW)
            except Exception as e:
                log("TASK_ERR", f"Lỗi hoàn tất task {t_id}: {e}", Fore.RED)
            await asyncio.sleep(2)

    def claim_streak(self):
        try:
            r = requests.post(f"{API_BASE}/api/streak/claim", headers=self.get_headers(), json={"telegram_id": self.user_id}, timeout=10)
            if r.status_code == 200:
                d = r.json()
                if d.get("ok"):
                    log("STREAK", f"🎉 Điểm danh thành công Ngày {d.get('streakDay', 1)}: +{d.get('rewardGhs', 0)} GH/s!", Fore.GREEN)
        except Exception:
            pass

    def tap_mine(self):
        taps_done = 0
        for _ in range(25):
            try:
                r = requests.post(f"{API_BASE}/api/tap", headers=self.get_headers(), json={"telegram_id": self.user_id}, timeout=10)
                if r.status_code == 200:
                    d = r.json()
                    if d.get("ok"):
                        taps_done += 1
                        time.sleep(random.uniform(1.5, 3.0))
                    else:
                        break
                elif r.status_code == 429:
                    log("TAP", "🛑 Đã hoàn thành 240/240 lượt Tap hôm nay!", Fore.MAGENTA)
                    return
                else:
                    break
            except Exception:
                break
        if taps_done > 0:
            log("TAP", f"✅ Đã thực hiện {taps_done} lượt Tap đào đá!", Fore.GREEN)

    def check_and_claim_vault(self, auth_data):
        m = auth_data.get("mining", {}) if auth_data else {}
        claim_interval = m.get("claimIntervalSec", 3600)
        elapsed = m.get("elapsedSec", 0)
        pct = min(100.0, (elapsed / claim_interval) * 100)
        
        log("VAULT", f"⛏️ Kho mỏ Vault: {elapsed:.0f}/{claim_interval}s ({pct:.1f}%)", Fore.CYAN)
        if elapsed >= claim_interval:
            log("VAULT", "🎉 Kho mỏ đã đạt 100%! Tiến hành thu hoạch miễn phí (Ad-free TOPLA)...", Fore.YELLOW)
            try:
                r = requests.post(f"{API_BASE}/api/claim", headers=self.get_headers(), json={"telegram_id": self.user_id, "watched_ad": False}, timeout=10)
                if r.status_code == 200:
                    d = r.json()
                    if d.get("ok"):
                        u = d.get("user", {})
                        self.balance = float(u.get("balance", self.balance))
                        log("VAULT", f"✅ THU HOẠCH KHO MỎ THÀNH CÔNG! Số dư mới: {self.balance:.6f} TON/GRAM", Fore.GREEN)
                else:
                    log("VAULT_ERR", f"Lỗi thu hoạch Vault: {r.text[:100]}", Fore.YELLOW)
            except Exception as e:
                log("VAULT_ERR", f"Lỗi claim: {e}", Fore.RED)

    def boost_moonpool_card_chain(self, tier=3):
        """
        Quy trình chuẩn Moonpool Native Engine cày Thẻ Mỏ Safir Tier 3 (+4 GH/s):
          Bước 1: QC Adsgram (Thực hiện bypass Adsgram Reward URL thật)
          Bước 2: QC Gigapub (Delay 6.5s theo chuẩn hệ thống)
          Bước 3: QC Monetag (Delay 6.5s theo chuẩn hệ thống)
          Kết thúc: Nhận Thẻ Mỏ Safir Cấp 3 (+4 GH/s)!
        """
        log("CARD_START", f"🚀 Kích hoạt quy trình xem QC cày Thẻ Mỏ Safir Cấp {tier} (+4 GH/s 24h)...", Fore.CYAN)
        time.sleep(2.0)
        
        r_start = None
        for _stry in range(3):
            try:
                r_start = requests.post(f"{API_BASE}/api/game/start", headers=self.get_headers(), json={"game_type": "cards", "tier": tier}, timeout=10)
                if r_start.status_code == 429:
                    log("CARD_COOLDOWN", "⚠️ Bị giới hạn rate limit 429. Chờ 5s...", Fore.YELLOW)
                    time.sleep(5.0)
                    continue
                break
            except Exception as e:
                log("CARD_WARN", f"Lỗi kết nối game/start: {e}", Fore.YELLOW)
                time.sleep(2.0)
                
        if not r_start or r_start.status_code != 200:
            log("CARD_WARN", f"Chưa thể bắt đầu ca cày Thẻ (HTTP {r_start.status_code if r_start else 'None'})", Fore.YELLOW)
            return False, 30

        d_start = r_start.json()
        if not d_start.get("ok"):
            err = d_start.get("error", "Chưa sẵn sàng")
            log("CARD_WARN", f"Thông báo từ Gramstone: {err}", Fore.YELLOW)
            return False, d_start.get("retry_in", 30)

        ses = d_start.get("session", {})
        ses_id = ses.get("id")
        chain = ses.get("chain", ["adsgram", "gigapub", "monetag"])
        block_id = "54796"
        log("CARD_FLOW", f"Phiên Thẻ Mỏ #{ses_id} đã mở! Chuỗi {len(chain)} QC: {' -> '.join(chain)}", Fore.CYAN)

        try:
            # --- BƯỚC 1: ADSGRAM ---
            if "adsgram" in chain:
                log("STEP1_ADSGRAM", f"Bước 1/{len(chain)}: Đang tải quảng cáo Adsgram (Block {block_id})...", Fore.YELLOW)
                ad_headers = {
                    "User-Agent": self.ua,
                    "Origin": API_BASE,
                    "Referer": f"{API_BASE}/",
                    "Accept": "application/json",
                    "X-Requested-With": "org.telegram.messenger"
                }
                adv_params = {
                    "blockId": block_id,
                    "tg_id": self.user_id,
                    "tg_platform": "android",
                    "platform": "Linux aarch64",
                    "language": "vi",
                    "top_domain": "sslip.io",
                    "signature": self.sig,
                    "data_check_string": self.dcs,
                    "sdk_version": "2.2.5"
                }
                try:
                    r_adv = requests.get("https://api.adsgram.ai/adv", headers=ad_headers, params=adv_params, timeout=12)
                    reward_url = None
                    if r_adv.status_code == 200:
                        for u in re.findall(r"https://api\.adsgram\.ai/event\?[^\s\'\"]+", r_adv.text):
                            if "Reward" in u or "trackingtypeid=14" in u:
                                reward_url = u
                                break
                    if reward_url:
                        log("STEP1_ADSGRAM", "Đang xem video Adsgram (8.5s)...", Fore.YELLOW)
                        time.sleep(8.5)
                        requests.get(reward_url, headers=ad_headers, timeout=10)
                        time.sleep(3.5)
                    else:
                        time.sleep(8.5)
                except Exception:
                    time.sleep(8.5)

                counted_s1 = False
                for _ in range(6):
                    r_s1 = requests.post(f"{API_BASE}/api/game/ad", headers=self.get_headers(), json={"session_id": ses_id, "network": "adsgram"}, timeout=10).json()
                    if r_s1.get("counted"):
                        counted_s1 = True
                        log("STEP1_ADSGRAM", f"✓ Bước 1/{len(chain)} Adsgram hoàn thành thành công!", Fore.GREEN)
                        break
                    time.sleep(2)
                if not counted_s1:
                    requests.post(f"{API_BASE}/api/game/finish", headers=self.get_headers(), json={"session_id": ses_id}, timeout=8)
                    return False, 30

            # --- BƯỚC 2: GIGAPUB ---
            if "gigapub" in chain:
                step_idx = chain.index("gigapub") + 1
                log("STEP2_GIGAPUB", f"Bước {step_idx}/{len(chain)}: Đang xem QC Gigapub (8.5s)...", Fore.YELLOW)
                time.sleep(8.5)
                for _ in range(4):
                    r_s2 = requests.post(f"{API_BASE}/api/game/ad", headers=self.get_headers(), json={"session_id": ses_id, "network": "gigapub"}, timeout=10).json()
                    if r_s2.get("counted"):
                        log("STEP2_GIGAPUB", f"✓ Bước {step_idx}/{len(chain)} Gigapub hoàn thành thành công!", Fore.GREEN)
                        break
                    time.sleep(2)

            # --- BƯỚC 3: MONETAG ---
            if "monetag" in chain:
                step_idx = chain.index("monetag") + 1
                log("STEP3_MONETAG", f"Bước {step_idx}/{len(chain)}: Đang xem QC Monetag (8.5s)...", Fore.YELLOW)
                time.sleep(8.5)
                for _ in range(4):
                    r_s3 = requests.post(f"{API_BASE}/api/game/ad", headers=self.get_headers(), json={"session_id": ses_id, "network": "monetag"}, timeout=10).json()
                    if r_s3.get("counted"):
                        log("STEP3_MONETAG", f"✓ Bước {step_idx}/{len(chain)} Monetag hoàn thành thành công!", Fore.GREEN)
                        break
                    time.sleep(2)

            # --- KẾT THÚC VÀ NHẬN THẺ SAFIR CẤP 3 (+4 GH/s) ---
            r_fin = requests.post(f"{API_BASE}/api/game/finish", headers=self.get_headers(), json={"session_id": ses_id}, timeout=10).json()
            if r_fin.get("ok"):
                c = r_fin.get("card", {})
                new_bonus = r_fin.get("bonus_ghs", self.bonus_ghs)
                new_total = r_fin.get("total_ghs", self.total_ghs)
                log("CARD_SUCCESS", f"🎉🎉🎉 ĐÃ NHẬN THÀNH CÔNG THẺ MỎ TIER {c.get('tier', tier)} (+{c.get('bonus_ghs', 4)} GH/s)! Tốc độ mới: {new_total} GH/s (Bonus: +{new_bonus} GH/s)", Fore.GREEN)
                return True, 0
            else:
                log("CARD_WARN", f"Kết thúc chuỗi: {r_fin.get('error', 'Xong')}", Fore.YELLOW)
                return False, 20
        except Exception as e:
            log("CARD_ERR", f"Lỗi chuỗi QC: {e}", Fore.RED)
            try: requests.post(f"{API_BASE}/api/game/finish", headers=self.get_headers(), json={"session_id": ses_id}, timeout=8)
            except Exception: pass
            return False, 30

    async def run_cycle(self):
        ok = await self.fetch_tg_init_data()
        if not ok:
            return
        
        auth_data = self.authenticate()
        if not auth_data:
            return

        await self.scan_and_claim_tasks(auth_data)
        self.claim_streak()
        self.tap_mine()
        self.check_and_claim_vault(auth_data)
        self.boost_moonpool_card_chain(tier=3)

def trigger_next_shift(workflow_file="gramstone_acc4.yml"):
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

async def run_loop_247(bot_instance, interval_mins=0):
    raw_rt = os.getenv("MAX_RUNTIME_SECONDS", "17500").strip()
    max_runtime = int(raw_rt) if raw_rt.isdigit() else 17500
    start_time = time.time()
    card_count = 0
    last_vault_check = 0
    last_tap_check = 0
    last_tasks_check = 0
    handover_done = False
    
    log("CONTINUOUS", "🔥 CHẾ ĐỘ AUTO GRAMSTONE 24/7 (TASKS + VAULT + SAFIR TIER 3) ĐÃ BẬT!", Fore.GREEN)
    
    ok = await bot_instance.fetch_tg_init_data()
    if not ok:
        log("INIT_ERR", "Không thể lấy init_data ban đầu.", Fore.RED)
        return

    auth_data = bot_instance.authenticate()
    if auth_data:
        await bot_instance.scan_and_claim_tasks(auth_data)
        bot_instance.check_and_claim_vault(auth_data)
        bot_instance.claim_streak()
        last_vault_check = time.time()
        last_tasks_check = time.time()

    while True:
        elapsed = time.time() - start_time
        if elapsed >= max_runtime - 300 and not handover_done:
            log("HANDOVER", f"⏰ Đã chạy {elapsed/3600:.1f}h. Tự động chuyển giao ca tiếp theo...", Fore.CYAN)
            trigger_next_shift("gramstone_acc4.yml")
            handover_done = True
            
        if elapsed >= max_runtime:
            log("HANDOVER", f"⏰ Hoàn tất ca trực {max_runtime}s. Bàn giao runner 24/7 thành công!", Fore.GREEN)
            break

        now = time.time()
        
        # 1. Kiểm tra Kho Mỏ Vault & Streak định kỳ mỗi 5 phút
        if now - last_vault_check >= 300:
            try:
                auth_data = bot_instance.authenticate()
                if auth_data:
                    bot_instance.check_and_claim_vault(auth_data)
                    bot_instance.claim_streak()
                last_vault_check = now
            except Exception as e:
                log("VAULT_ERR", f"Lỗi check vault: {e}", Fore.RED)

        # 2. Quét kiểm tra nhiệm vụ mới định kỳ mỗi 30 phút
        if now - last_tasks_check >= 1800:
            try:
                auth_data = bot_instance.authenticate()
                if auth_data:
                    await bot_instance.scan_and_claim_tasks(auth_data)
                last_tasks_check = now
            except Exception as e:
                log("TASKS_ERR", f"Lỗi check tasks: {e}", Fore.RED)

        # 3. Đào đá Tap định kỳ mỗi 10 phút
        if now - last_tap_check >= 600:
            try:
                bot_instance.tap_mine()
                last_tap_check = now
            except Exception as e:
                log("TAP_ERR", f"Lỗi tap: {e}", Fore.RED)

        # 4. CÀY THẺ SAFIR TIER 3 (+4 GH/s) LIÊN TỤC
        try:
            ok, retry_in = bot_instance.boost_moonpool_card_chain(tier=3)
            if ok:
                card_count += 1
                log("CONTINUOUS", f"🎉 [THẺ MỎ #{card_count}] Đã nhận +4 GH/s! Nghỉ 10s trước ca tiếp theo...", Fore.CYAN)
                await asyncio.sleep(10)
            else:
                wait_sec = max(10, retry_in if retry_in > 0 else 30)
                log("CONTINUOUS", f"⏳ Chờ hồi chiêu Thẻ Mỏ ({wait_sec}s) để cày tiếp...", Fore.LIGHTBLACK_EX)
                await asyncio.sleep(wait_sec)
        except Exception as e:
            log("CARD_ERR", f"Lỗi cày thẻ: {e}", Fore.RED)
            await asyncio.sleep(15)

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Bot Auto Gramstone ($GRAM/$TON) 24/7")
    parser.add_argument("--acc", type=int, default=1, help="Tài khoản chạy (1 hoặc 2)")
    parser.add_argument("--loop", type=int, default=0, help="Số phút lặp lại (0 để chạy 1 lần)")
    args, _ = parser.parse_known_args()

    session_str = DEFAULT_SESSION_ACC2 if args.acc == 2 else DEFAULT_SESSION_ACC1
    env_str = os.getenv(f"TELEGRAM_STRING_SESSION_ACC{args.acc}") or os.getenv("TELEGRAM_STRING_SESSION")
    if env_str:
        session_str = env_str
    
    session_file = f"C:/Users/Administrator/Downloads/kiemtien_autoplay/telepet_acc{args.acc}.session"
    if not os.path.exists(session_file):
        session_file = None

    print(Fore.CYAN + f"""
=============================================================================
  BOT AUTO GRAMSTONE ($GRAM / $TON) 24/7 - CHUẨN CƠ CHẾ MỚI MOONPOOL 100%
  Acc: {args.acc} | Quét Tasks & Archive Telegram | Thu Hoạch Vault 100% | Thẻ Safir Tier 3
=============================================================================
    """ + Style.RESET_ALL)
    
    bot = GramstoneBot(string_session=session_str, session_path=session_file)
    run_247 = os.getenv("RUN_247", "1") == "1"
    if args.loop > 0 or run_247:
        await run_loop_247(bot, interval_mins=args.loop)
    else:
        await bot.run_cycle()

if __name__ == "__main__":
    asyncio.run(main())
