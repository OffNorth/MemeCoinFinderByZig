import asyncio
import websockets
import json
import requests
import os
import aiohttp
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich import box

load_dotenv()

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY", "YOUR_API_KEY_HERE")

console = Console()
birdeye_semaphore = asyncio.Semaphore(1)

recent_tokens = []
MAX_DISPLAY = 10

# ==================== TELEGRAM FUNCTION ====================
def send_telegram(msg):
    print("📤 Sending to Telegram...")
    if BOT_TOKEN:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": msg}
            response = requests.post(url, json=payload, timeout=10)
            print(f"📤 Response: {response.status_code}")
            if response.status_code == 200:
                print("✅ Message sent!")
            else:
                print(f"❌ HTTP error: {response.status_code} - {response.text[:100]}")
        except Exception as e:
            print(f"❌ Exception: {e}")
    else:
        print("❌ BOT_TOKEN missing")


# ==================== PERIODIC STATUS ====================
async def periodic_status():
    """Sends a status message every 3 hours"""
    while True:
        await asyncio.sleep(10800)  # 3 hours
        message = (
            "👘 **Nino**: still online, watching for gems.\n"
            "🔍 Dashboard active, Dexscreener + Birdeye analysis.\n"
            "📨 I'll send you tokens as soon as they reach a score ≥ 3/4.\n"
            "⏳ Next status update in 3h."
        )
        send_telegram(message)
        console.print("[dim]📤 Periodic status sent to Telegram[/dim]")


# ==================== DEXSCREENER ====================
async def get_dexscreener_data(mint, max_attempts=5, delay=10):
    for attempt in range(max_attempts):
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        pairs = data.get("pairs", [])
                        if pairs:
                            pair = pairs[0]
                            return {
                                "market_cap": float(pair.get("marketCap", 0) or 0),
                                "volume_24h": float(pair.get("volume", {}).get("h24", 0) or 0),
                                "price_change_5m": float(pair.get("priceChange", {}).get("m5", 0) or 0),
                                "price": float(pair.get("priceUsd", 0) or 0)
                            }

                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay)

        except:
            if attempt < max_attempts - 1:
                await asyncio.sleep(delay)

    return None


def calculate_dex_score(data):
    if not data:
        return None

    score = 0
    market_cap = data.get("market_cap", 0)
    volume = data.get("volume_24h", 0)
    price_change = data.get("price_change_5m", 0)

    if market_cap > 50000:
        score += 1

    if market_cap > 200000:
        score += 1

    if volume > 20000:
        score += 1

    if 0 < price_change < 50:
        score += 1

    if score > 4:
        score = 4

    return {"score": score, "max_score": 4, "raw": data}


# ==================== BIRDEYE ====================
async def get_birdeye_data(mint):
    if not BIRDEYE_API_KEY or BIRDEYE_API_KEY == "YOUR_API_KEY_HERE":
        return None

    async with birdeye_semaphore:
        await asyncio.sleep(1)

        url = f"https://public-api.birdeye.so/defi/token_overview?address={mint}"

        headers = {
            "accept": "application/json",
            "x-chain": "solana",
            "X-API-KEY": BIRDEYE_API_KEY
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=10
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", {})

                    elif response.status == 429:
                        await asyncio.sleep(5)
                        return None

                    else:
                        return None

        except:
            return None


def calculate_birdeye_score(data):
    if not data:
        return None

    score = 0

    liquidity = data.get("liquidity", 0) or 0
    market_cap = data.get("marketCap", 0) or 0
    holders = data.get("uniqueWallet1h", 0) or 0
    price_change = data.get("priceChange1hPercent")

    if liquidity > 50000:
        score += 1

    if market_cap > 100000:
        score += 1

    if holders > 500:
        score += 1

    if price_change is not None and -20 < price_change < 20:
        score += 1

    price_30m = data.get("history30mPrice")
    current_price = data.get("price")

    if (
        price_30m is not None
        and current_price is not None
        and price_30m > 0
    ):
        momentum = ((current_price - price_30m) / price_30m) * 100

        if momentum > 0:
            score += 1

    return {"score": score, "max_score": 5}


# ==================== DASHBOARD ====================
def build_dashboard():
    table = Table(
        title="🔥 PUMP.FUN SCANNER - LIVE",
        box=box.ROUNDED,
        style="bold cyan"
    )

    table.add_column("#", style="dim", width=4)
    table.add_column("Token", style="bold yellow", width=15)
    table.add_column("DEX", justify="center", width=8)
    table.add_column("Birdeye", justify="center", width=10)
    table.add_column("Market Cap", justify="right", width=14)
    table.add_column("Volume 24h", justify="right", width=14)
    table.add_column("Change 5m", justify="right", width=8)

    if not recent_tokens:
        table.add_row("⏳", "Waiting...", "-", "-", "-", "-", "-")
        return table

    for i, token in enumerate(recent_tokens[:MAX_DISPLAY], 1):

        dex_score = token.get("dex_score", 0)

        if dex_score >= 3:
            dex_display = f"[green]{dex_score}/4[/green]"
        elif dex_score >= 2:
            dex_display = f"[yellow]{dex_score}/4[/yellow]"
        else:
            dex_display = f"[red]{dex_score}/4[/red]"

        birdeye = token.get("birdeye_certified", False)

        birdeye_display = (
            "🏆 [green]Certified[/green]"
            if birdeye
            else "❌ [dim]No[/dim]"
        )

        market_cap = token.get("market_cap", 0)

        if market_cap > 200000:
            mc_display = f"[green]${market_cap:,.0f}[/green]"
        elif market_cap > 50000:
            mc_display = f"[yellow]${market_cap:,.0f}[/yellow]"
        else:
            mc_display = f"[red]${market_cap:,.0f}[/red]"

        volume = token.get("volume_24h", 0)

        if volume > 50000:
            vol_display = f"[green]${volume:,.0f}[/green]"
        elif volume > 20000:
            vol_display = f"[yellow]${volume:,.0f}[/yellow]"
        else:
            vol_display = f"[red]${volume:,.0f}[/red]"

        change = token.get("change_5m", 0)

        if change > 10:
            change_display = f"[green]+{change:.1f}%[/green]"
        elif change > 0:
            change_display = f"[yellow]+{change:.1f}%[/yellow]"
        elif change < 0:
            change_display = f"[red]{change:.1f}%[/red]"
        else:
            change_display = f"{change:.1f}%"

        name = token.get("name", "?")[:12]

        table.add_row(
            str(i),
            name,
            dex_display,
            birdeye_display,
            mc_display,
            vol_display,
            change_display
        )

    return table


# ==================== TOKEN PROCESSING ====================
async def process_token(mint, name, symbol):
    console.print(f"[cyan]🔄 Processing {symbol}...[/cyan]")

    dex_data = await get_dexscreener_data(mint)
    dex_score = calculate_dex_score(dex_data) if dex_data else None

    token_info = {
        "name": name,
        "symbol": symbol,
        "mint": mint,
        "dex_score": dex_score["score"] if dex_score else 0,
        "market_cap": dex_data.get("market_cap", 0) if dex_data else 0,
        "volume_24h": dex_data.get("volume_24h", 0) if dex_data else 0,
        "change_5m": dex_data.get("price_change_5m", 0) if dex_data else 0,
        "birdeye_certified": False,
        "timestamp": datetime.now()
    }

    if dex_score and dex_score["score"] >= 3:
        console.print(
            f"[cyan]🔍 Checking Birdeye for {symbol}...[/cyan]"
        )

        birdeye_data = await get_birdeye_data(mint)

        birdeye_score = (
            calculate_birdeye_score(birdeye_data)
            if birdeye_data
            else None
        )

        if birdeye_score and birdeye_score["score"] >= 3:
            token_info["birdeye_certified"] = True

            console.print(
                f"[green]✅ {symbol} Birdeye certified![/green]"
            )

    recent_tokens.insert(0, token_info)

    if len(recent_tokens) > MAX_DISPLAY:
        recent_tokens.pop()

    # ========== SEND IF DEX SCORE >= 3 ==========
    if dex_score and dex_score["score"] >= 3:

        console.print(
            f"[green]📨 {symbol} → sending to Telegram "
            f"(score {dex_score['score']}/4)[/green]"
        )

        alert = ""

        alert += "Hey you, listen up. 👀\n"
        alert += "I just came across a token worth keeping an eye on.\n\n"

        alert += f"🎯 **Name**: {name} (${symbol})\n"
        alert += f"🔗 [Dexscreener](https://dexscreener.com/solana/{mint})\n"
        alert += f"🛒 [Pump.fun](https://pump.fun/{mint})\n\n"

        if dex_score:
            score_display = (
                "🟢"
                if dex_score["score"] >= 4
                else "🟡"
            )

            alert += (
                f"📊 **Dex Score**: {score_display} "
                f"{dex_score['score']}/4\n"
            )

        if token_info["birdeye_certified"]:
            alert += (
                "🏆 **Birdeye**: ✅ Certified "
                "(score ≥ 3/5)\n"
            )
        else:
            alert += "🏆 **Birdeye**: ❌ Not certified yet\n"

        alert += "\n"

        if dex_data:
            market_cap = dex_data.get("market_cap", 0)
            volume = dex_data.get("volume_24h", 0)
            change_5m = dex_data.get("price_change_5m", 0)

            alert += "💰 **The numbers speak for themselves:**\n"

            alert += (
                f"   • Market Cap: "
                f"`${market_cap:,.0f}`\n"
            )

            alert += (
                f"   • Volume 24h: "
                f"`${volume:,.0f}`\n"
            )

            if change_5m > 0:
                alert += (
                    f"   • 5m Change: "
                    f"📈 `+{change_5m:.1f}%`\n"
                )

            elif change_5m < 0:
                alert += (
                    f"   • 5m Change: "
                    f"📉 `{change_5m:.1f}%`\n"
                )

            else:
                alert += (
                    f"   • 5m Change: "
                    f"➖ `{change_5m:.1f}%`\n"
                )

        alert += "\n"

        if (
            dex_score["score"] >= 4
            and token_info["birdeye_certified"]
        ):
            alert += (
                "💬 **My take:**\n"
                "Confirmed gem. Liquidity is there, the signals are green. "
                "I'm jumping in, but keep an eye on the order book."
            )

        elif (
            dex_score["score"] >= 3
            and token_info["birdeye_certified"]
        ):
            alert += (
                "💬 **My take:**\n"
                "Good fundamentals, but I want to see a little more volume "
                "before committing heavily. Watch the next 10 minutes."
            )

        elif dex_score["score"] >= 4:
            alert += (
                "💬 **My take:**\n"
                "The Dex score is solid, but liquidity is still low. "
                "I recommend watching the volume before jumping in. "
                "Entering too early can cost you dearly, don't get greedy."
            )

        else:
            alert += (
                "💬 **My take:**\n"
                "Average potential, the entry is risky. "
                "If you go in, use a very small position and get out quickly."
            )

        alert += (
            "\n\n⚠️ **Reminder**: only risk what you are willing to lose. "
            "Now it's your move."
        )

        send_telegram(alert)

    else:
        console.print(
            f"[dim]⏳ {symbol} ignored "
            f"(score {dex_score['score'] if dex_score else 0}/4)[/dim]"
        )


# ==================== BOT CORE ====================
async def listen():
    with Live(
        build_dashboard(),
        refresh_per_second=2,
        screen=True
    ) as live:

        # Start the periodic status task in the background
        asyncio.create_task(periodic_status())

        while True:
            try:
                uri = "wss://pumpportal.fun/api/data"

                async with websockets.connect(
                    uri,
                    ping_interval=None,
                    ping_timeout=None
                ) as websocket:

                    await websocket.send(
                        json.dumps({
                            "method": "subscribeNewToken"
                        })
                    )

                    console.print(
                        "[green]✅ BOT ACTIVE! Live dashboard...[/green]"
                    )

                    console.print(
                        "[yellow]⏳ Waiting for new Pump.fun tokens...[/yellow]"
                    )

                    console.print(
                        "[dim]📨 Telegram: only tokens with "
                        "DEX score ≥ 3/4[/dim]"
                    )

                    # Startup message on Telegram
                    send_telegram(
                        "👘 Nino is online. I'm watching for gems for you. 🔥"
                    )

                    while True:
                        try:
                            message = await websocket.recv()
                            data = json.loads(message)

                            mint = data.get("mint")

                            if not mint:
                                continue

                            name = data.get("name", "?")
                            symbol = data.get("symbol", "?")

                            asyncio.create_task(
                                process_token(
                                    mint,
                                    name,
                                    symbol
                                )
                            )

                            live.update(build_dashboard())

                        except websockets.ConnectionClosed:
                            console.print(
                                "[red]⚠️ WebSocket connection closed, "
                                "reconnecting...[/red]"
                            )
                            break

                        except json.JSONDecodeError:
                            continue

                        except Exception as e:
                            console.print(
                                f"[red]Error: {e}[/red]"
                            )
                            await asyncio.sleep(1)

            except Exception as e:
                console.print(
                    f"[red]❌ Connection error: {e}. "
                    f"Reconnecting in 5s...[/red]"
                )

                await asyncio.sleep(5)


if __name__ == "__main__":

    if not BOT_TOKEN:
        console.print(
            "[red]❌ Telegram token missing. "
            "Check your .env file[/red]"
        )
    else:
        asyncio.run(listen())