"""
Nino — scanner de nouveaux tokens Pump.fun (Solana).
Croise Dexscreener + Birdeye et envoie une alerte Telegram quand un token
atteint le score minimum. Langue des messages Telegram réglable via .env (LANG=fr|en).
"""

import asyncio
import json
import logging
import os
from datetime import datetime

import aiohttp
import websockets
from dotenv import load_dotenv
from rich import box
from rich.console import Console
from rich.live import Live
from rich.table import Table

load_dotenv()

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
LANG = os.getenv("LANG", "fr").lower()

DEX_ALERT_THRESHOLD = 3     # score Dexscreener minimum pour alerter (sur 4)
BIRDEYE_CERT_THRESHOLD = 3  # score Birdeye minimum pour la mention "certifié" (sur 5)
STATUS_INTERVAL_SECONDS = 10800  # 3 heures
MAX_DISPLAY = 10
PUMPPORTAL_WS = "wss://pumpportal.fun/api/data"

console = Console()
birdeye_semaphore = asyncio.Semaphore(1)
recent_tokens: list[dict] = []

logging.basicConfig(
    filename="nino.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger("nino")

# ==================== TEXTES (FR / EN) ====================
TEXTS = {
    "fr": {
        "status": (
            "👘 **Nino** : toujours en ligne, je surveille les nouveaux tokens.\n"
            "🔍 Analyses Dexscreener + Birdeye actives.\n"
            f"📨 Alerte envoyée dès qu'un score ≥ {DEX_ALERT_THRESHOLD}/4 est atteint.\n"
            "⏳ Prochain statut dans 3h."
        ),
        "startup": "👘 Nino est en ligne et surveille les nouveaux tokens Pump.fun.",
        "intro": "Un nouveau token vient de passer les seuils de surveillance.\n\n",
        "name": "🎯 **Nom** : {name} (${symbol})\n",
        "dex_score": "📊 **Score Dex** : {emoji} {score}/4\n",
        "birdeye_yes": f"🏆 **Birdeye** : ✅ Certifié (score ≥ {BIRDEYE_CERT_THRESHOLD}/5)\n",
        "birdeye_no": "🏆 **Birdeye** : ❌ Pas encore certifié\n",
        "numbers": "💰 **Indicateurs :**\n",
        "mc": "   • Market Cap : `${mc:,.0f}`\n",
        "vol": "   • Volume 24h : `${vol:,.0f}`\n",
        "var_up": "   • Variation 5m : 📈 `+{v:.1f}%`\n",
        "var_down": "   • Variation 5m : 📉 `{v:.1f}%`\n",
        "var_flat": "   • Variation 5m : ➖ `{v:.1f}%`\n",
        "take_best": "💬 **Analyse automatique :**\nLes indicateurs Dex et Birdeye sont favorables sur les critères surveillés. Cela ne garantit rien : vérifie le carnet d'ordres et la liquidité avant toute décision.",
        "take_good": "💬 **Analyse automatique :**\nBonnes bases sur Dex et Birdeye, mais volume encore limité. À surveiller sur les prochaines minutes avant de te faire un avis.",
        "take_dex_only": "💬 **Analyse automatique :**\nScore Dex correct mais liquidité pas encore confirmée par Birdeye. Risque d'entrée précoce plus élevé.",
        "take_weak": "💬 **Analyse automatique :**\nSignaux faibles, risque élevé. Reste prudent si tu regardes ce token.",
        "reminder": "\n\n⚠️ **Rappel** : ceci est une analyse automatisée basée sur des indicateurs publics, pas un conseil financier. Les tokens Pump.fun sont très volatils et exposés aux rug pulls/scams. Ne risque que ce que tu peux perdre et fais tes propres recherches (DYOR).",
        "ignored": "ignoré",
        "waiting": "En attente...",
        "table_title": "🔥 SCANNER PUMP.FUN — LIVE",
        "col_change": "Var 5m",
        "no_token": "Token manquant, message ignoré",
        "ws_closed": "⚠️ Connexion WebSocket coupée, reconnexion...",
        "ws_error": "❌ Erreur de connexion : {e}. Nouvelle tentative dans 5s...",
        "active": "✅ Bot actif ! Dashboard en direct...",
        "waiting_tokens": "⏳ En attente des nouveaux tokens Pump.fun...",
        "alert_scope": f"📨 Telegram : uniquement les tokens avec score Dex ≥ {DEX_ALERT_THRESHOLD}/4",
        "missing_token": "❌ TOKEN Telegram manquant. Vérifie ton fichier .env",
        "certified": "🏆 Certifié",
        "not_certified": "❌ Non",
    },
    "en": {
        "status": (
            "👘 **Nino**: still online, watching new tokens.\n"
            "🔍 Dexscreener + Birdeye analysis active.\n"
            f"📨 Alert sent as soon as a token reaches a score ≥ {DEX_ALERT_THRESHOLD}/4.\n"
            "⏳ Next status update in 3h."
        ),
        "startup": "👘 Nino is online and watching new Pump.fun tokens.",
        "intro": "A new token just crossed the monitored thresholds.\n\n",
        "name": "🎯 **Name**: {name} (${symbol})\n",
        "dex_score": "📊 **Dex Score**: {emoji} {score}/4\n",
        "birdeye_yes": f"🏆 **Birdeye**: ✅ Certified (score ≥ {BIRDEYE_CERT_THRESHOLD}/5)\n",
        "birdeye_no": "🏆 **Birdeye**: ❌ Not certified yet\n",
        "numbers": "💰 **Indicators:**\n",
        "mc": "   • Market Cap: `${mc:,.0f}`\n",
        "vol": "   • Volume 24h: `${vol:,.0f}`\n",
        "var_up": "   • 5m Change: 📈 `+{v:.1f}%`\n",
        "var_down": "   • 5m Change: 📉 `{v:.1f}%`\n",
        "var_flat": "   • 5m Change: ➖ `{v:.1f}%`\n",
        "take_best": "💬 **Automated analysis:**\nDex and Birdeye indicators are favorable on the tracked criteria. This guarantees nothing: check the order book and liquidity before any decision.",
        "take_good": "💬 **Automated analysis:**\nGood fundamentals on Dex and Birdeye, but volume is still limited. Worth watching over the next few minutes before forming an opinion.",
        "take_dex_only": "💬 **Automated analysis:**\nDecent Dex score but liquidity not yet confirmed by Birdeye. Higher risk of an early entry.",
        "take_weak": "💬 **Automated analysis:**\nWeak signals, high risk. Be cautious if you're looking at this token.",
        "reminder": "\n\n⚠️ **Reminder**: this is an automated analysis based on public indicators, not financial advice. Pump.fun tokens are highly volatile and exposed to rug pulls/scams. Only risk what you can afford to lose and do your own research (DYOR).",
        "ignored": "ignored",
        "waiting": "Waiting...",
        "table_title": "🔥 PUMP.FUN SCANNER — LIVE",
        "col_change": "5m Change",
        "no_token": "Missing mint address, message ignored",
        "ws_closed": "⚠️ WebSocket connection closed, reconnecting...",
        "ws_error": "❌ Connection error: {e}. Retrying in 5s...",
        "active": "✅ Bot active! Live dashboard...",
        "waiting_tokens": "⏳ Waiting for new Pump.fun tokens...",
        "alert_scope": f"📨 Telegram: only tokens with Dex score ≥ {DEX_ALERT_THRESHOLD}/4",
        "missing_token": "❌ Telegram TOKEN missing. Check your .env file",
        "certified": "🏆 Certified",
        "not_certified": "❌ No",
    },
}
T = TEXTS.get(LANG, TEXTS["fr"])


# ==================== TELEGRAM ====================
async def send_telegram(session: aiohttp.ClientSession, msg: str) -> None:
    if not BOT_TOKEN or not CHAT_ID:
        log.error("BOT_TOKEN ou CHAT_ID manquant, message non envoyé.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                body = (await resp.text())[:200]
                log.error("Erreur Telegram HTTP %s : %s", resp.status, body)
    except Exception as e:
        log.error("Exception lors de l'envoi Telegram : %s", e)


async def periodic_status(session: aiohttp.ClientSession) -> None:
    """Envoie un message de statut à intervalle régulier."""
    while True:
        await asyncio.sleep(STATUS_INTERVAL_SECONDS)
        await send_telegram(session, T["status"])
        console.print("[dim]📤 Statut périodique envoyé[/dim]")


# ==================== DEXSCREENER ====================
async def get_dexscreener_data(session: aiohttp.ClientSession, mint: str, max_attempts=5, delay=10):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
    for attempt in range(max_attempts):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pairs = data.get("pairs") or []
                    if pairs:
                        pair = pairs[0]
                        return {
                            "market_cap": float(pair.get("marketCap") or 0),
                            "volume_24h": float(pair.get("volume", {}).get("h24") or 0),
                            "price_change_5m": float(pair.get("priceChange", {}).get("m5") or 0),
                            "price": float(pair.get("priceUsd") or 0),
                        }
        except Exception as e:
            log.warning("Dexscreener tentative %d échouée pour %s : %s", attempt + 1, mint, e)
        if attempt < max_attempts - 1:
            await asyncio.sleep(delay)
    return None


def calculate_dex_score(data: dict) -> dict:
    score = 0
    if data["market_cap"] > 50_000:
        score += 1
    if data["market_cap"] > 200_000:
        score += 1
    if data["volume_24h"] > 20_000:
        score += 1
    if 0 < data["price_change_5m"] < 50:
        score += 1
    return {"score": min(score, 4), "max_score": 4}


# ==================== BIRDEYE ====================
async def get_birdeye_data(session: aiohttp.ClientSession, mint: str):
    if not BIRDEYE_API_KEY:
        return None
    async with birdeye_semaphore:
        await asyncio.sleep(1)  # limite le débit vers l'API Birdeye
        url = f"https://public-api.birdeye.so/defi/token_overview?address={mint}"
        headers = {"accept": "application/json", "x-chain": "solana", "X-API-KEY": BIRDEYE_API_KEY}
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data", {})
                if resp.status == 429:
                    log.warning("Birdeye rate-limit atteint")
                return None
        except Exception as e:
            log.warning("Birdeye échoué pour %s : %s", mint, e)
            return None


def calculate_birdeye_score(data: dict) -> dict:
    score = 0
    liquidity = data.get("liquidity") or 0
    market_cap = data.get("marketCap") or 0
    holders = data.get("uniqueWallet1h") or 0
    price_change = data.get("priceChange1hPercent")

    if liquidity > 50_000:
        score += 1
    if market_cap > 100_000:
        score += 1
    if holders > 500:
        score += 1
    if price_change is not None and -20 < price_change < 20:
        score += 1

    price_30m, price_now = data.get("history30mPrice"), data.get("price")
    if price_30m and price_now and price_30m > 0 and (price_now - price_30m) / price_30m > 0:
        score += 1

    return {"score": score, "max_score": 5}


# ==================== DASHBOARD ====================
def _tier_color(value: float, high: float, low: float) -> str:
    """Vert si value > high, jaune si value > low, rouge sinon."""
    return "green" if value > high else "yellow" if value > low else "red"


def build_dashboard() -> Table:
    table = Table(title=T["table_title"], box=box.ROUNDED, style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Token", style="bold yellow", width=15)
    table.add_column("DEX", justify="center", width=8)
    table.add_column("Birdeye", justify="center", width=10)
    table.add_column("Market Cap", justify="right", width=14)
    table.add_column("Volume 24h", justify="right", width=14)
    table.add_column(T["col_change"], justify="right", width=8)

    if not recent_tokens:
        table.add_row("⏳", T["waiting"], "-", "-", "-", "-", "-")
        return table

    for i, token in enumerate(recent_tokens[:MAX_DISPLAY], 1):
        dex_score = token["dex_score"]
        dex_color = _tier_color(dex_score, 2, 1)
        dex_display = f"[{dex_color}]{dex_score}/4[/{dex_color}]"

        birdeye_display = T["certified"] if token["birdeye_certified"] else T["not_certified"]

        mc = token["market_cap"]
        mc_color = _tier_color(mc, 200_000, 50_000)
        mc_display = f"[{mc_color}]${mc:,.0f}[/{mc_color}]"

        vol = token["volume_24h"]
        vol_color = _tier_color(vol, 50_000, 20_000)
        vol_display = f"[{vol_color}]${vol:,.0f}[/{vol_color}]"

        var = token["change_5m"]
        if var > 0:
            var_display = f"[green]+{var:.1f}%[/green]" if var > 10 else f"[yellow]+{var:.1f}%[/yellow]"
        elif var < 0:
            var_display = f"[red]{var:.1f}%[/red]"
        else:
            var_display = "0.0%"

        table.add_row(str(i), token["name"][:12], dex_display, birdeye_display, mc_display, vol_display, var_display)
    return table


# ==================== ALERTE TELEGRAM ====================
def build_alert(name: str, symbol: str, mint: str, dex_score: dict, dex_data: dict, birdeye_certified: bool) -> str:
    score = dex_score["score"]
    alert = T["intro"]
    alert += T["name"].format(name=name, symbol=symbol)
    alert += f"🔗 [Dexscreener](https://dexscreener.com/solana/{mint})\n"
    alert += f"🛒 [Pump.fun](https://pump.fun/{mint})\n\n"
    alert += T["dex_score"].format(emoji="🟢" if score >= 4 else "🟡", score=score)
    alert += T["birdeye_yes"] if birdeye_certified else T["birdeye_no"]
    alert += "\n" + T["numbers"]
    alert += T["mc"].format(mc=dex_data["market_cap"])
    alert += T["vol"].format(vol=dex_data["volume_24h"])
    var = dex_data["price_change_5m"]
    alert += (T["var_up"] if var > 0 else T["var_down"] if var < 0 else T["var_flat"]).format(v=var)
    alert += "\n"

    if score >= 4 and birdeye_certified:
        alert += T["take_best"]
    elif score >= 3 and birdeye_certified:
        alert += T["take_good"]
    elif score >= 4:
        alert += T["take_dex_only"]
    else:
        alert += T["take_weak"]
    alert += T["reminder"]
    return alert


# ==================== TRAITEMENT D'UN TOKEN ====================
async def process_token(session: aiohttp.ClientSession, mint: str, name: str, symbol: str) -> None:
    dex_data = await get_dexscreener_data(session, mint)
    if not dex_data:
        return
    dex_score = calculate_dex_score(dex_data)

    birdeye_certified = False
    if dex_score["score"] >= DEX_ALERT_THRESHOLD:
        birdeye_data = await get_birdeye_data(session, mint)
        if birdeye_data:
            birdeye_score = calculate_birdeye_score(birdeye_data)
            birdeye_certified = birdeye_score["score"] >= BIRDEYE_CERT_THRESHOLD

    recent_tokens.insert(0, {
        "name": name, "symbol": symbol, "mint": mint,
        "dex_score": dex_score["score"],
        "market_cap": dex_data["market_cap"],
        "volume_24h": dex_data["volume_24h"],
        "change_5m": dex_data["price_change_5m"],
        "birdeye_certified": birdeye_certified,
        "timestamp": datetime.now(),
    })
    del recent_tokens[MAX_DISPLAY:]

    if dex_score["score"] >= DEX_ALERT_THRESHOLD:
        console.print(f"[green]📨 {symbol} → Telegram (score {dex_score['score']}/4)[/green]")
        alert = build_alert(name, symbol, mint, dex_score, dex_data, birdeye_certified)
        await send_telegram(session, alert)
    else:
        console.print(f"[dim]⏳ {symbol} {T['ignored']} (score {dex_score['score']}/4)[/dim]")


# ==================== CŒUR DU BOT ====================
async def listen() -> None:
    async with aiohttp.ClientSession() as session:
        with Live(build_dashboard(), refresh_per_second=2, screen=True) as live:
            asyncio.create_task(periodic_status(session))

            while True:
                try:
                    async with websockets.connect(PUMPPORTAL_WS, ping_interval=None, ping_timeout=None) as ws:
                        await ws.send(json.dumps({"method": "subscribeNewToken"}))
                        console.print(f"[green]{T['active']}[/green]")
                        console.print(f"[yellow]{T['waiting_tokens']}[/yellow]")
                        console.print(f"[dim]{T['alert_scope']}[/dim]")
                        await send_telegram(session, T["startup"])

                        while True:
                            try:
                                message = await ws.recv()
                                data = json.loads(message)
                                mint = data.get("mint")
                                if not mint:
                                    continue
                                asyncio.create_task(
                                    process_token(session, mint, data.get("name", "?"), data.get("symbol", "?"))
                                )
                                live.update(build_dashboard())
                            except websockets.ConnectionClosed:
                                console.print(f"[red]{T['ws_closed']}[/red]")
                                break
                            except json.JSONDecodeError:
                                continue
                except Exception as e:
                    console.print(f"[red]{T['ws_error'].format(e=e)}[/red]")
                    await asyncio.sleep(5)


if __name__ == "__main__":
    if not BOT_TOKEN:
        console.print(f"[red]{T['missing_token']}[/red]")
    else:
        asyncio.run(listen())
