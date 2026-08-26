# 🤖 Nino — Scanner de tokens Pump.fun

**Nino** surveille en temps réel les nouveaux tokens lancés sur **Pump.fun** (Solana), croise les données de **Dexscreener** et **Birdeye** pour calculer un score, affiche un dashboard en direct dans le terminal, et envoie une alerte Telegram quand un token dépasse le seuil configuré.

Fonctionne sur Linux, Windows et Termux (Android).

## ✨ Fonctionnalités

- 📡 Écoute en temps réel via WebSocket (Pump.fun)
- 📊 Score Dexscreener (`/4`) : Market Cap, Volume 24h, variation 5 min
- 🟣 Vérification secondaire Birdeye (`/5`) : liquidité, holders, momentum
- 🖥️ Dashboard coloré dans le terminal (`rich`)
- 📨 Alerte Telegram uniquement si le score Dex ≥ seuil configuré
- ⏰ Message de statut Telegram toutes les 3h
- 🌍 Alertes en français ou en anglais (`LANG=fr` ou `LANG=en` dans `.env`)


## 🛠️ Prérequis

- Python 3.10+
- Un bot Telegram (créé via [@BotFather](https://t.me/BotFather)) et son token
- (Optionnel mais recommandé) une clé API [Birdeye](https://birdeye.so/) gratuite pour la vérification secondaire

## 📥 Installation

```bash
git clone https://github.com/OffNorth/MemeCoinFinderByZig.git
cd MemeCoinFinderByZig
pip install -r requirements.txt
```

## 🔐 Configuration

Copie `.env.example` en `.env` :
```bash
cp .env.example .env
```

Puis renseigne tes valeurs :
```env
TOKEN=ton_token_telegram_ici
CHAT_ID=ton_chat_id_telegram_ici
BIRDEYE_API_KEY=ta_cle_birdeye_ici
LANG=fr
```

- **CHAT_ID** : envoie un message à ton bot sur Telegram, puis ouvre `https://api.telegram.org/bot<TON_TOKEN>/getUpdates` pour trouver `"chat":{"id": ...}`.
- **BIRDEYE_API_KEY** : laisse vide si tu ne veux pas la vérification secondaire — le bot fonctionnera uniquement avec le score Dexscreener.
- **LANG** : `fr` ou `en`, change la langue des messages Telegram.

⚠️ Ne publie jamais `.env` sur GitHub (déjà listé dans `.gitignore`).

## ▶️ Lancer le bot

```bash
python bot.py
```

## 📊 Fonctionnement du scoring

| Source | Indicateurs | Score |
|---|---|---|
| 🔵 Dexscreener | Market Cap, Volume 24h, Variation 5m | `/4` |
| 🟣 Birdeye | Liquidité, Holders, Momentum | `/5` |

Une alerte Telegram est envoyée dès qu'un token atteint **3/4 sur Dexscreener**. Le score n'est qu'un indicateur automatisé basé sur des données publiques — il ne détecte ni les rug pulls ni les scams, et ne garantit rien sur la fiabilité d'un token.

## 🚀 Faire tourner le bot en continu

**Linux / Termux** :
```bash
screen -S nino
python3 bot.py
# Détacher : CTRL+A puis D — revenir : screen -r nino
```

**Windows** : Planificateur de tâches, ou lance-le dans un terminal que tu laisses ouvert.

## 🛠️ Dépannage

| Problème | Solution |
|---|---|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| Rien ne s'affiche sur Telegram | Vérifie `TOKEN` et `CHAT_ID` dans `.env`, et que tu as bien envoyé un message au bot une fois |
| Pas de certification Birdeye | Vérifie que `BIRDEYE_API_KEY` est renseignée et valide |
| Erreurs détaillées | Consulte le fichier `nino.log`, créé automatiquement |

## ⚠️ Disclaimer

Nino est un outil de surveillance et d'analyse automatisée, **pas un conseil financier**. Les tokens Pump.fun sont extrêmement volatils et exposés aux rug pulls, scams et manipulations de marché. Utilise ce bot à tes propres risques et fais toujours tes propres recherches (DYOR).

## 👥 Contact

Telegram : zig47 · X/TikTok/Instagram : zigxbt

---

Si le projet te plaît, laisse une ⭐ au repository !
