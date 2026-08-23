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
CHAT_ID = "1234"
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY", "TA_CLE_API_ICI")

console = Console()
semaphore_birdeye = asyncio.Semaphore(1)

tokens_recents = []
MAX_AFFICHAGE = 10

# ==================== FONCTION TELEGRAM ====================
def envoyer_telegram(msg):
    print("📤 Envoi à Telegram...")
    if BOT_TOKEN:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": msg}
            response = requests.post(url, json=payload, timeout=10)
            print(f"📤 Réponse : {response.status_code}")
            if response.status_code == 200:
                print("✅ Message envoyé !")
            else:
                print(f"❌ Erreur HTTP : {response.status_code} - {response.text[:100]}")
        except Exception as e:
            print(f"❌ Exception : {e}")
    else:
        print("❌ BOT_TOKEN manquant")

# ==================== STATUT PERIODIQUE ====================
async def statut_periodique():
    """Envoie un message de statut toutes les 3 heures"""
    while True:
        await asyncio.sleep(10800)  # 3 heures
        message = (
            "👘 **Nino** : toujours en ligne, je guette les pépites.\n"
            "🔍 Dashboard actif, analyses Dexscreener + Birdeye.\n"
            "📨 Je t'envoie les tokens dès qu'ils atteignent un score ≥ 3/4.\n"
            "⏳ Prochain statut dans 3h."
        )
        envoyer_telegram(message)
        console.print("[dim]📤 Statut périodique envoyé sur Telegram[/dim]")

# ==================== DEXSCREENER ====================
async def get_dexscreener_data(mint, essais_max=5, delai=10):
    for tentative in range(essais_max):
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
                    if tentative < essais_max - 1:
                        await asyncio.sleep(delai)
        except:
            if tentative < essais_max - 1:
                await asyncio.sleep(delai)
    return None

def calculer_score_dex(data):
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
    if not BIRDEYE_API_KEY or BIRDEYE_API_KEY == "TA_CLE_API_ICI":
        return None
    async with semaphore_birdeye:
        await asyncio.sleep(1)
        url = f"https://public-api.birdeye.so/defi/token_overview?address={mint}"
        headers = {
            "accept": "application/json",
            "x-chain": "solana",
            "X-API-KEY": BIRDEYE_API_KEY
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
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

def calculer_score_birdeye(data):
    if not data:
        return None
    score = 0
    liquidite = data.get("liquidity", 0) or 0
    market_cap = data.get("marketCap", 0) or 0
    holders = data.get("uniqueWallet1h", 0) or 0
    price_change = data.get("priceChange1hPercent")
    if liquidite > 50000:
        score += 1
    if market_cap > 100000:
        score += 1
    if holders > 500:
        score += 1
    if price_change is not None and -20 < price_change < 20:
        score += 1
    price_30m = data.get("history30mPrice")
    price_actuel = data.get("price")
    if price_30m is not None and price_actuel is not None and price_30m > 0:
        momentum = ((price_actuel - price_30m) / price_30m) * 100
        if momentum > 0:
            score += 1
    return {"score": score, "max_score": 5}

# ==================== DASHBOARD ====================
def build_dashboard():
    table = Table(title="🔥 SCANNER PUMP.FUN - LIVE", box=box.ROUNDED, style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Token", style="bold yellow", width=15)
    table.add_column("DEX", justify="center", width=8)
    table.add_column("Birdeye", justify="center", width=10)
    table.add_column("Market Cap", justify="right", width=14)
    table.add_column("Volume 24h", justify="right", width=14)
    table.add_column("Var 5m", justify="right", width=8)
    if not tokens_recents:
        table.add_row("⏳", "En attente...", "-", "-", "-", "-", "-")
        return table
    for i, token in enumerate(tokens_recents[:MAX_AFFICHAGE], 1):
        dex_score = token.get("dex_score", 0)
        if dex_score >= 3:
            dex_display = f"[green]{dex_score}/4[/green]"
        elif dex_score >= 2:
            dex_display = f"[yellow]{dex_score}/4[/yellow]"
        else:
            dex_display = f"[red]{dex_score}/4[/red]"
        birdeye = token.get("birdeye_certifie", False)
        birdeye_display = "🏆 [green]Certifié[/green]" if birdeye else "❌ [dim]Non[/dim]"
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
        var = token.get("var_5m", 0)
        if var > 10:
            var_display = f"[green]+{var:.1f}%[/green]"
        elif var > 0:
            var_display = f"[yellow]+{var:.1f}%[/yellow]"
        elif var < 0:
            var_display = f"[red]{var:.1f}%[/red]"
        else:
            var_display = f"{var:.1f}%"
        nom = token.get("nom", "?")[:12]
        table.add_row(str(i), nom, dex_display, birdeye_display, mc_display, vol_display, var_display)
    return table

# ==================== TRAITEMENT D'UN TOKEN ====================
async def traiter_token(mint, nom, symbole):
    console.print(f"[cyan]🔄 Traitement de {symbole}...[/cyan]")
    
    dex_data = await get_dexscreener_data(mint)
    dex_score = calculer_score_dex(dex_data) if dex_data else None
    
    token_info = {
        "nom": nom,
        "symbole": symbole,
        "mint": mint,
        "dex_score": dex_score['score'] if dex_score else 0,
        "market_cap": dex_data.get("market_cap", 0) if dex_data else 0,
        "volume_24h": dex_data.get("volume_24h", 0) if dex_data else 0,
        "var_5m": dex_data.get("price_change_5m", 0) if dex_data else 0,
        "birdeye_certifie": False,
        "timestamp": datetime.now()
    }
    
    if dex_score and dex_score['score'] >= 3:
        console.print(f"[cyan]🔍 Vérification Birdeye pour {symbole}...[/cyan]")
        birdeye_data = await get_birdeye_data(mint)
        birdeye_score = calculer_score_birdeye(birdeye_data) if birdeye_data else None
        if birdeye_score and birdeye_score['score'] >= 3:
            token_info["birdeye_certifie"] = True
            console.print(f"[green]✅ {symbole} certifié Birdeye ![/green]")
    
    tokens_recents.insert(0, token_info)
    if len(tokens_recents) > MAX_AFFICHAGE:
        tokens_recents.pop()
    
    # ========== ENVOI SI DEX SCORE >= 3 ==========
    if dex_score and dex_score['score'] >= 3:
        console.print(f"[green]📨 {symbole} → envoi Telegram (score {dex_score['score']}/4)[/green]")
        alert = ""
        alert += f"Hé toi, écoute-moi bien. 👀\n"
        alert += f"Je viens de tomber sur un token qui mérite qu'on s'y attarde.\n\n"
        alert += f"🎯 **Nom** : {nom} (${symbole})\n"
        alert += f"🔗 [Dexscreener](https://dexscreener.com/solana/{mint})\n"
        alert += f"🛒 [Pump.fun](https://pump.fun/{mint})\n\n"
        if dex_score:
            score_display = "🟢" if dex_score['score'] >= 4 else "🟡"
            alert += f"📊 **Score Dex** : {score_display} {dex_score['score']}/4\n"
        if token_info["birdeye_certifie"]:
            alert += f"🏆 **Birdeye** : ✅ Certifié (score ≥ 3/5)\n"
        else:
            alert += f"🏆 **Birdeye** : ❌ Pas encore certifié\n"
        alert += "\n"
        if dex_data:
            market_cap = dex_data.get('market_cap', 0)
            volume = dex_data.get('volume_24h', 0)
            var_5m = dex_data.get('price_change_5m', 0)
            alert += "💰 **Les chiffres parlent d'eux-mêmes :**\n"
            alert += f"   • Market Cap : `${market_cap:,.0f}`\n"
            alert += f"   • Volume 24h : `${volume:,.0f}`\n"
            if var_5m > 0:
                alert += f"   • Variation 5m : 📈 `+{var_5m:.1f}%`\n"
            elif var_5m < 0:
                alert += f"   • Variation 5m : 📉 `{var_5m:.1f}%`\n"
            else:
                alert += f"   • Variation 5m : ➖ `{var_5m:.1f}%`\n"
        alert += "\n"
        if dex_score['score'] >= 4 and token_info["birdeye_certifie"]:
            alert += "💬 **Mon avis :**\nPépite confirmée. La liquidité est là, les signaux sont verts. Je fonce, mais toi, garde un œil sur le carnet d'ordres."
        elif dex_score['score'] >= 3 and token_info["birdeye_certifie"]:
            alert += "💬 **Mon avis :**\nBonnes bases, mais je veux voir un peu plus de volume avant de m'engager à fond. Surveille les 10 prochaines minutes."
        elif dex_score['score'] >= 4:
            alert += "💬 **Mon avis :**\nLe score Dex est solide, mais la liquidité est encore faible. Je te conseille de surveiller le volume avant de sauter dedans. Un entry trop tôt peut te coûter cher, ne sois pas trop gourmand."
        else:
            alert += "💬 **Mon avis :**\nPotentiel moyen, l'entrée est risquée. Si tu y vas, ce sera avec une toute petite position, et tu sors vite."
        alert += "\n\n⚠️ **Rappel** : ne joue que ce que tu es prêt à perdre. Maintenant, à toi de jouer."
        envoyer_telegram(alert)
    else:
        console.print(f"[dim]⏳ {symbole} ignoré (score {dex_score['score'] if dex_score else 0}/4)[/dim]")

# ==================== CŒUR DU BOT ====================
async def ecouter():
    with Live(build_dashboard(), refresh_per_second=2, screen=True) as live:
        # Lancer la tâche de statut périodique en arrière-plan
        asyncio.create_task(statut_periodique())
        while True:
            try:
                uri = "wss://pumpportal.fun/api/data"
                async with websockets.connect(uri, ping_interval=None, ping_timeout=None) as websocket:
                    await websocket.send(json.dumps({"method": "subscribeNewToken"}))
                    console.print("[green]✅ BOT ACTIF ! Dashboard en direct...[/green]")
                    console.print("[yellow]⏳ En attente des nouveaux tokens Pump.fun...[/yellow]")
                    console.print("[dim]📨 Telegram : uniquement les tokens avec DEX score ≥ 3/4[/dim]")
                    # Message de démarrage sur Telegram
                    envoyer_telegram("👘 Nino est en ligne. Je guette les pépites pour toi. 🔥")
                    while True:
                        try:
                            message = await websocket.recv()
                            data = json.loads(message)
                            mint = data.get("mint")
                            if not mint:
                                continue
                            nom = data.get('name', '?')
                            symbole = data.get('symbol', '?')
                            asyncio.create_task(traiter_token(mint, nom, symbole))
                            live.update(build_dashboard())
                        except websockets.ConnectionClosed:
                            console.print("[red]⚠️ Connexion WebSocket coupée, reconnexion...[/red]")
                            break
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            console.print(f"[red]Erreur: {e}[/red]")
                            await asyncio.sleep(1)
            except Exception as e:
                console.print(f"[red]❌ Erreur connexion: {e}. Reconnexion dans 5s...[/red]")
                await asyncio.sleep(5)

if __name__ == "__main__":
    if not BOT_TOKEN:
        console.print("[red]❌ Token Telegram manquant. Vérifie .env[/red]")
    else:
        asyncio.run(ecouter()) 
