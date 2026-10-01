<div align="center">

<img width="100%" alt="header" src="https://capsule-render.vercel.app/api?type=waving&height=210&text=Pirates%20Bot&fontAlign=50&fontAlignY=36&fontSize=56&desc=Pirates%7CBooty%7CReferral%7CMulti%20Account%7CCountdown"/>

<img alt="typing" src="https://readme-typing-svg.demolab.com?font=Inter&size=18&duration=3000&pause=650&center=true&vCenter=true&width=900&lines=Full%20daily%20cycle%20automation%20for%20the%20Pirates%20Miniapp;A%20stable%20device%20identity%20is%20pinned%20per%20account%20and%20reused%20on%20every%20run;The%20tutorial%20bounty%20is%20claimed%20and%20the%20partner%20loot%20is%20collected;The%20pirate%20crew%20is%20recruited%20with%20the%20affordable%20slots%20in%20the%20catalog;Multi%20account%20with%20proxy%20support%20and%20a%20live%20countdown%20between%20cycles"/>

<p>
  <img alt="python" src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white"/>
  <img alt="platform" src="https://img.shields.io/badge/Platform-Pirates%20Miniapp-111111"/>
  <img alt="multi-account" src="https://img.shields.io/badge/Multi--Account-Supported-111111"/>
  <img alt="proxy" src="https://img.shields.io/badge/Proxy-Supported-111111"/>
  <img alt="author" src="https://img.shields.io/badge/by-Yuurisandesu-111111"/>
</p>

<p>
  <b>Pirates Bot</b> is a full automation bot for the Pirates Telegram Miniapp.<br/>
  It runs the complete free daily cycle: the account state is read first, a stable device identity is pinned for the account and reused afterwards, the tutorial bounty is claimed, the partner loot is collected, the booty claim is settled, the channel subscription is confirmed and the crew is recruited with every affordable slot of the pirate catalog. Every credited amount is printed only after the server confirms it, and all accounts run one after another with proxy support and a live countdown between cycles.<br/>
  Built and distributed by <b>Yuurisandesu</b>.
</p>

</div>

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Bot](#running-the-bot)
- [Features](#features)
- [File Structure](#file-structure)
- [Disclaimer](#disclaimer)

---

## Requirements

- Python `3.12+`
- Git

---

## Installation

**Clone the repository:**

```bash
git clone https://github.com/Yuurisan-N1/Pirates-Miniapp.git
cd Pirates-Miniapp
```

**Install dependencies:**

```bash
pip install aiohttp yuurisan
```

---

## Configuration

### 1. Accounts (data.txt)

Fill `data.txt` with the Telegram WebApp `initData` string of each account, one per line:

```
query_id=AAH...&user=%7B%22id%22%3A7113873680...&auth_date=1759...&hash=9f2c...
query_id=AAH...&user=%7B%22id%22%3A6004380466...&auth_date=1759...&hash=c41a...
```

> `initData` can be obtained from the browser DevTools when opening Pirates on Telegram Web. The bot reads the Telegram user id out of the string itself; nothing is typed in by hand.

### 2. Proxy (proxy.txt)

Fill `proxy.txt` with proxies, one per line (optional, leave empty to run without proxy):

```
host:port
host:port:user:pass
http://user:pass@host:port
```

Proxies are assigned to accounts by index in round-robin order.

### 3. Bot Settings (config.json)

`sleep_seconds` controls how many seconds the bot waits between cycles. If `config.json` is missing, it is created automatically with a default of `3600` seconds.

```json
{
  "settings": {
    "sleep_seconds": 3600
  }
}
```

---

## Running the Bot

```bash
python bot.py
```

Press `Ctrl+C` at any time to stop the bot cleanly.

---

## Features

### Device Identity

The Miniapp binds every call to a device id and a device fingerprint that the server records on the first sight of the account. The bot pins that identity once per Telegram id and keeps it in `device.json`, so the same account always reports the same device even after the `initData` string is replaced or the bot is restarted, and accounts can never swap identities with each other. A first sight pins the identity and prints a green line, every later run reuses the cached record and prints a green reuse line instead.

### Account State

Every credential line is sent on the account state call and the closing summary is read from a fresh state call, so the bot prints the captain name, the Gold balance and the crew size exactly as the server returns them. A line that holds no valid initData is reported in red.

### Telemetry

The device id, the device fingerprint and the full raw device profile are submitted once per account on every cycle and the answer from the server is reported.

### Tutorial Bounty

When the account has not finished the guide yet, the tutorial bounty is claimed and the credited amount is printed only when the server answers with the reward value. An account that already collected it prints a green line instead of calling again.

### Partner Loot

The partner loot collection is called on every cycle and the collected amount is printed only when the server confirms it, together with the balance the server sent back.

### Booty Claim

The booty claim is called on every cycle and the credited amount is printed only when the server confirms it. An answer that carries no reward is reported in yellow with the reason string the server sent back.

### Channel Subscription

The channel subscription is confirmed on every cycle and the answer from the server is reported, so an account that is not subscribed yet is visible in the log instead of being silently accepted.

### Crew Recruitment

The pirate catalog is read from the server and the crew is recruited with every slot the account can still afford: the cheapest open slot is bought first and the loop keeps buying until the balance runs out, with a short countdown between two recruits so the server cooldown is respected, so the price, the daily income and the slot index all come from the server instead of being written into the bot. Every recruited pirate is printed in green with its name and slot, a server that asks the bot to slow down stops the loop with one yellow line, and a fresh state call afterwards prints the new balance and the crew size.

### Multi Account

All accounts in `data.txt` are processed one after another in the order they are listed within every cycle. The cycle number is logged at the start of each round, and each account block is separated by a blank line.

### Proxy Support

Proxies are loaded from `proxy.txt` and assigned to accounts by position in round-robin order. Proxy credentials are masked in log output. Running without proxies is fully supported.

### Auto Countdown

After all accounts complete a cycle, the bot displays a live `HH:MM:SS` countdown until the next cycle starts.

---

## File Structure

```text
Pirates-Miniapp/
├── bot.py          # Main bot, full daily cycle automation
├── config.json     # Sleep duration between cycles
├── data.txt        # Account initData, one per line
├── proxy.txt       # Proxy list, one per line (optional)
├── LICENSE         # License file
├── README.md       # This documentation
└── utils/
    └── banner.py   # Banner using yuurisan module
```

---

## Disclaimer

This tool is built for educational and technical exploration purposes. Use it wisely and at your own responsibility.

---

<div align="center">
<img width="100%" alt="footer" src="https://capsule-render.vercel.app/api?type=waving&height=120&section=footer"/>
</div>