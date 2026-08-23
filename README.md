# MemeCoinFinderByZig
# 🤖 Nino - Scanner de tokens Pump.fun

**Nino** est un bot d'analyse crypto en temps réel, conçu pour surveiller les nouveaux tokens lancés sur **Pump.fun** (blockchain Solana). Il croise les données de **Dexscreener** et **Birdeye** pour calculer un score de fiabilité, affiche un tableau de bord en direct dans le terminal et t'envoie des alertes détaillées sur Telegram quand une pépite potentielle est détectée.

---

## ✨ Fonctionnalités

- 📡 **Écoute en temps réel** : Connexion WebSocket à Pump.fun pour capturer les nouveaux tokens dès leur création.
- 📊 **Double analyse** :
  - **Dexscreener** : Market Cap, Volume 24h, Variation 5m → Score sur 4.
  - **Birdeye** : Liquidité, Nombre de détenteurs, Momentum du prix → Score sur 5 (vérification secondaire).
- 🖥️ **Dashboard dynamique** : Interface colorée dans le terminal (avec la bibliothèque `rich`) qui se met à jour en direct.
- 📨 **Alertes Telegram intelligentes** :
  - Envoi automatique uniquement si le token obtient un score **≥ 3/4** sur Dexscreener.
  - Message détaillé contenant les chiffres clés, les liens vers Dexscreener/Pump.fun et un avis personnalisé.
- ⏰ **Statut périodique** : Le bot t'envoie un message de "battement de cœur" sur Telegram toutes les 3 heures pour confirmer qu'il est actif.

---

## 🛠️ Prérequis

Avant de lancer le bot, assure-toi d'avoir :

- **Python 3.10** ou supérieur installé sur ta machine.
- Un **bot Telegram** et son token (à créer via [@BotFather](https://t.me/BotFather)).
- Une **clé API Birdeye** (gratuite, à récupérer sur [Birdeye](https://birdeye.so/)).

---

### 2. Installation du bot :

Ouvre un terminal (ou l'invite de commandes) et exécute ces **deux commandes** :
```bash
git clone https://github.com/OffNorth/MemeCoinFinderByZig.git
cd MemeCoinFinderByZig
```

Ensuite les dépendances du bot : 
```bash
pip install websockets requests aiohttp python-dotenv rich
```

On passe a la création du fichier .env , le fichier ou l'on pose le token du bot telegram, la clé api de birdeye et son chat id telegram.
```bash
nano .env
```
```bash
TOKEN=ton_token_telegram_ici
BIRDEYE_API_KEY=ta_cle_birdeye_ici
CHAT_ID=ton_id_telegram_ici
```

Ensuite pour le lancer vous n'avez qu'a faire : 
```bash
python bot.py
```







