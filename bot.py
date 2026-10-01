import os
import sys
import json
import time
import signal
import hashlib
import asyncio
import aiohttp

from urllib.parse import parse_qs

from utils.banner import show_banner

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"

MY_PROJECT = "Pirates Miniapp"
BASE_URL = "https://piratesbackend.raeton.uk"
REF_CODE = "1161"


def log_green(msg):
    print(f"{GREEN}{BOLD}{msg}{RESET}", flush=True)


def log_yellow(msg):
    print(f"{YELLOW}{BOLD}{msg}{RESET}", flush=True)


def log_red(msg):
    print(f"{RED}{BOLD}{msg}{RESET}", flush=True)


def signal_handler(sig, frame):
    print()
    log_red("Script stopped by user")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def normalize_proxy(proxy_line):
    if not proxy_line:
        return None
    value = proxy_line.strip()
    if "://" in value:
        return value
    parts = value.split(":")
    if len(parts) == 4:
        host, port, user, password = parts
        return f"http://{user}:{password}@{host}:{port}"
    if len(parts) == 3:
        host, port, user = parts
        return f"http://{user}@{host}:{port}"
    return f"http://{value}"


def mask_proxy(proxy_url):
    try:
        after_at = proxy_url.split("@")[-1]
        host_part = after_at.split(":")[0]
        port_part = after_at.split(":")[1] if ":" in after_at else ""
        octets = host_part.split(".")
        if len(octets) == 4:
            masked_host = f"{octets[0]}*****{octets[3]}"
        else:
            masked_host = "***"
        suffix = f":{port_part}" if port_part else ""
        return f"http://user:pass@{masked_host}{suffix}"
    except Exception:
        return "http://user:pass@***:***"


def countdown(seconds, label):
    start = time.time()
    while True:
        remaining = seconds - (time.time() - start)
        if remaining <= 0:
            print(f"\r{' ' * 70}\r", end="", flush=True)
            break
        h = int(remaining // 3600)
        m = int((remaining % 3600) // 60)
        s = int(remaining % 60)
        print(f"\r{YELLOW}{BOLD}{label} {h:02d}:{m:02d}:{s:02d}{RESET}", end="", flush=True)
        time.sleep(1)


def load_config():
    defaults = {"settings": {"sleep_seconds": 3600}}
    if not os.path.exists("config.json"):
        return defaults
    try:
        with open("config.json") as f:
            return json.load(f)
    except Exception:
        return defaults


def load_accounts():
    if not os.path.exists("data.txt"):
        log_red("File data.txt was not found.")
        sys.exit(1)
    lines = [l.strip() for l in open("data.txt").readlines() if l.strip()]
    if not lines:
        log_red("File data.txt is empty.")
        sys.exit(1)
    return lines


def load_proxies():
    if not os.path.exists("proxy.txt"):
        return []
    try:
        return [l.strip() for l in open("proxy.txt").readlines() if l.strip()]
    except Exception:
        return []


def get_proxy(proxies, idx):
    if not proxies:
        return None
    return proxies[idx % len(proxies)]


def parse_account(line):
    value = line.strip()
    if "tgWebAppData=" in value:
        value = value.split("tgWebAppData=", 1)[1]
        value = value.split("&tgWebAppVersion")[0].split("&tgWebAppPlatform")[0]
        from urllib.parse import unquote
        value = unquote(value)
    user_id = ""
    username = ""
    try:
        raw = (parse_qs(value).get("user") or [""])[0]
        if raw:
            info = json.loads(raw)
            user_id = str(info.get("id") or "")
            username = info.get("username") or info.get("first_name") or ""
    except Exception:
        pass
    return value, user_id, username


def build_device(user_id, username):
    model = "Linux armv81"
    user_agent = "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36"
    device_id = hashlib.md5(f"pirates-{user_id}".encode()).hexdigest()
    device_id = f"{device_id[0:8]}-{device_id[8:12]}-{device_id[12:16]}-{device_id[16:20]}-{device_id[20:32]}"
    info = {
        "userAgent": user_agent,
        "language": "en-US",
        "languages": "en-US,en",
        "platform": model,
        "hardwareConcurrency": 8,
        "deviceMemory": 8,
        "colorDepth": 24,
        "pixelRatio": 2,
        "touchPoints": 5,
        "webdriver": False,
        "timezone": "Asia/Jakarta",
        "resolution": "412x915",
        "deviceId": device_id,
        "canvasFingerprint": hashlib.sha256(f"pirates-canvas-{user_id}".encode()).hexdigest(),
        "webglVendor": "Google Inc. (ARM)",
        "webglRenderer": "Mali-G715-Immortalis MC11",
    }
    fingerprint = hashlib.sha256(json.dumps(info, separators=(",", ":")).encode()).hexdigest()
    return {
        "id": user_id,
        "deviceId": device_id,
        "fingerprint": fingerprint,
        "userAgent": user_agent,
        "raw_info": info,
    }


def load_devices():
    if not os.path.exists("device.json"):
        return {}
    try:
        with open("device.json") as f:
            loaded = json.load(f)
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        return {}


def save_devices(devices):
    try:
        with open("device.json.tmp", "w") as f:
            json.dump(devices, f, indent=2)
            f.write("\n")
        os.replace("device.json.tmp", "device.json")
    except Exception:
        pass


def device_for(user_id, username, devices):
    record = devices.get(user_id)
    if isinstance(record, dict) and record.get("fingerprint") and record.get("deviceId"):
        return record, False
    record = build_device(user_id, username)
    devices[user_id] = record
    save_devices(devices)
    return record, True


def build_headers(init_data, device):
    return {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": init_data,
        "x-device-id": device["deviceId"],
        "x-device-fingerprint": device["fingerprint"],
        "x-start-param": REF_CODE,
        "origin": "https://pirates.raeton.uk",
        "referer": "https://pirates.raeton.uk/",
        "user-agent": device["userAgent"],
    }


async def api_get(session, path, init_data, device, proxy=None):
    try:
        async with session.get(
            BASE_URL + path,
            headers=build_headers(init_data, device),
            proxy=proxy,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as r:
            raw = await r.read()
            return r.status, json.loads(raw)
    except Exception as e:
        log_red(f"Request to the server failed with {type(e).__name__}.")
        return None, None


async def api_post(session, path, payload, init_data, device, proxy=None):
    try:
        async with session.post(
            BASE_URL + path,
            headers=build_headers(init_data, device),
            json=payload if payload is not None else {},
            proxy=proxy,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as r:
            raw = await r.read()
            return r.status, json.loads(raw)
    except Exception as e:
        log_red(f"Request to the server failed with {type(e).__name__}.")
        return None, None


def error_text(data):
    if isinstance(data, dict):
        return str(data.get("detail") or data.get("message") or "")
    return ""


async def read_me(session, init_data, device, proxy):
    return await api_get(session, "/api/user/me", init_data, device, proxy)


async def send_telemetry(session, init_data, device, proxy):
    payload = {
        "fingerprint": device["fingerprint"],
        "device_id": device["deviceId"],
        "raw_info": device["raw_info"],
    }
    status, data = await api_post(session, "/api/user/telemetry", payload, init_data, device, proxy)
    if data and data.get("status") == "ok":
        log_green("Device telemetry was accepted by the server for this account.")
    else:
        log_yellow("Device telemetry was refused by the server on this run.")


async def complete_tutorial(session, init_data, device, proxy):
    status, data = await api_post(session, "/api/user/complete-tutorial", None, init_data, device, proxy)
    if data and data.get("status") == "success":
        reward = data.get("reward") or 0
        log_green(f"Tutorial bounty of {reward} Gold was credited by the server.")
        return
    reason = error_text(data)
    if reason:
        log_yellow(f"Tutorial bounty says: {reason}.")
    else:
        log_yellow("Tutorial bounty is already claimed on this account.")


async def collect_partner_loot(session, init_data, device, proxy):
    status, data = await api_post(session, "/api/partners/collect", None, init_data, device, proxy)
    if data and data.get("status") == "success":
        collected = data.get("collected") or 0
        log_green(f"Partner loot collection credited {collected} Gold on this account.")
        return
    reason = error_text(data)
    if reason:
        log_yellow(f"Partner loot collection says: {reason}.")
    else:
        log_yellow("Partner loot collection returned no new reward.")


async def claim_booty(session, init_data, device, proxy):
    status, data = await api_post(session, "/api/user/claim", None, init_data, device, proxy)
    if data and data.get("status") == "success":
        claimed = data.get("claimed") or 0
        log_green(f"Booty claim credited {claimed} Gold to this account.")
        return
    reason = error_text(data)
    if reason:
        log_yellow(f"Booty claim says: {reason}.")
    else:
        log_yellow("Booty claim returned no new reward on this run.")


async def check_subscription(session, init_data, device, proxy):
    status, data = await api_get(session, "/api/user/check_subscription", init_data, device, proxy)
    if data and data.get("is_subscribed"):
        log_green("Channel subscription is confirmed for this account.")
        return
    reason = (data or {}).get("reason") if isinstance(data, dict) else ""
    if reason:
        log_yellow(f"Channel subscription says: {reason}.")
    else:
        log_yellow("Channel subscription could not be confirmed on this run.")


def owned_levels(fleet):
    levels = set()
    for item in (fleet or {}).get("pirates") or []:
        try:
            levels.add(int(item.get("level")))
        except Exception:
            continue
    return levels


def cooldown_reason(reason):
    text = str(reason).lower()
    return "fast" in text or "wait" in text or "soon" in text


async def recruit_pirates(session, init_data, device, user, fleet, proxy):
    status, catalog = await api_get(session, "/api/pirates/catalog", init_data, device, proxy)
    if not catalog or not catalog.get("pirates"):
        log_yellow("Pirate catalog was not returned by the server.")
        return
    owned = owned_levels(fleet)
    balance = float(user.get("balance") or 0)
    recruits = 0
    for pirate in sorted(catalog["pirates"], key=lambda p: float(p.get("cost") or 0)):
        level = int(pirate.get("level") or 0)
        cost = float(pirate.get("cost") or 0)
        name = pirate.get("name") or "pirate"
        if not level or level in owned or cost > balance:
            continue
        if recruits:
            countdown(20, "Waiting before the next pirate recruit attempt")
        payload = {"level": level, "slot_index": level - 1}
        status, data = await api_post(session, "/api/pirates/buy", payload, init_data, device, proxy)
        if data and data.get("status") == "success":
            balance = float(data.get("new_balance") or balance - cost)
            owned.add(level)
            recruits += 1
            log_green(f"Pirate {name} was recruited into slot {level} of the crew.")
            continue
        reason = error_text(data)
        if reason and cooldown_reason(reason):
            log_yellow(f"Pirate {name} recruitment says: {reason}.")
            return
        if reason:
            log_yellow(f"Pirate {name} recruitment says: {reason}.")
        else:
            log_yellow(f"Pirate {name} could not be recruited on this run.")
    if not recruits:
        log_green("No new pirate was affordable for this account on this run.")


async def process_account(line, proxy, index):
    init_data, user_id, username = parse_account(line)
    if not init_data or not user_id:
        log_red(f"Credential line {index + 1} is not valid initData.")
        return

    devices = load_devices()
    device, pinned = device_for(user_id, username, devices)
    if pinned:
        log_green(f"Device identity was pinned for account {user_id} on this run.")
    else:
        log_green(f"Cached device identity was reused for account {user_id} now.")

    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        status, data = await read_me(session, init_data, device, proxy)
        user = (data or {}).get("user") if isinstance(data, dict) else None
        if not user:
            log_red("Failed to retrieve account state.")
            return

        name = user.get("username") or username or "captain"
        balance = float(user.get("balance") or 0)
        log_green(f"Captain {name} logged in with {balance} Gold in the treasury.")

        await send_telemetry(session, init_data, device, proxy)

        if not user.get("tutorial_completed"):
            await complete_tutorial(session, init_data, device, proxy)
        else:
            log_green("Tutorial bounty was already collected on this account.")

        await collect_partner_loot(session, init_data, device, proxy)
        await claim_booty(session, init_data, device, proxy)
        await check_subscription(session, init_data, device, proxy)

        status, data = await read_me(session, init_data, device, proxy)
        user = (data or {}).get("user") or user
        fleet = (data or {}).get("fleet") or {}
        await recruit_pirates(session, init_data, device, user, fleet, proxy)

        status, data = await read_me(session, init_data, device, proxy)
        user = (data or {}).get("user") or user
        fleet = (data or {}).get("fleet") or fleet
        log_green(
            f"Account totals {user.get('balance', 0)} Gold with "
            f"{fleet.get('total_pirates', 0)} pirates aboard."
        )


async def main_async(accounts, proxies, sleep_secs):
    cycle = 1
    while True:
        log_yellow(f"Starting automation cycle number {cycle}.")
        for idx, line in enumerate(accounts):
            if idx > 0:
                print()
            proxy_url = normalize_proxy(get_proxy(proxies, idx))
            if proxy_url:
                log_yellow(f"Using proxy {mask_proxy(proxy_url)}.")
            await process_account(line, proxy_url, idx)
        log_yellow(f"All accounts processed for cycle number {cycle}.")
        countdown(sleep_secs, "Next cycle starts in")
        cycle += 1
        show_banner(MY_PROJECT)


def main():
    show_banner(MY_PROJECT)

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    config = load_config()
    sleep_secs = config.get("settings", {}).get("sleep_seconds", 3600)
    accounts = load_accounts()
    proxies = load_proxies()
    asyncio.run(main_async(accounts, proxies, sleep_secs))


if __name__ == "__main__":
    main()
