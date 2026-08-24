# MemeCoinFinderByZig
# 🤖 Nino — Scanner de tokens Pump.fun

**Nino** est un bot d'analyse crypto en temps réel conçu pour surveiller les nouveaux tokens lancés sur **Pump.fun** (blockchain Solana). 🪙

Il croise les données de **Dexscreener** et **Birdeye** afin de calculer un score de fiabilité, affiche un tableau de bord en direct dans le terminal et envoie des alertes détaillées sur Telegram lorsqu'une potentielle pépite est détectée. 🚀

Work on Linux Termux Windows

---

## ✨ Fonctionnalités

* 📡 **Écoute en temps réel**
  Connexion WebSocket à Pump.fun pour capturer les nouveaux tokens dès leur création.

* 📊 **Double analyse**

  * 🔵 **Dexscreener** : Market Cap, Volume 24h et variation sur 5 min → **Score sur 4**
  * 🟣 **Birdeye** : Liquidité, nombre de détenteurs et momentum du prix → **Score sur 5** (vérification secondaire)

* 🖥️ **Dashboard dynamique**
  Interface colorée dans le terminal grâce à la bibliothèque `rich`, avec une mise à jour en direct des tokens détectés.

* 📨 **Alertes Telegram intelligentes**

  * 🚨 Envoi automatique uniquement lorsqu'un token obtient un score **≥ 3/4 sur Dexscreener**.
  * 📈 Message détaillé contenant les chiffres clés.
  * 🔗 Liens directs vers **Dexscreener** et **Pump.fun**.
  * 💡 Avis personnalisé basé sur les données analysées.

* ⏰ **Statut périodique**
  Le bot envoie un message de « battement de cœur » sur Telegram toutes les **3 heures** afin de confirmer qu'il est toujours actif. ❤️

---

## 🛠️ Prérequis

Avant de lancer le bot, assure-toi d'avoir :

* 🐍 **Python 3.10** ou supérieur installé sur ta machine.
* 🤖 Un **bot Telegram** et son token, à créer via [@BotFather](https://t.me/BotFather).
* 🔑 Une **clé API Birdeye** (gratuite), disponible sur [Birdeye](https://birdeye.so/).
* 💻 Un terminal pour installer et lancer le bot.

---

## 📥 Installation

### 1. Cloner le projet

Ouvre un terminal et exécute les commandes suivantes :

```bash
git clone https://github.com/OffNorth/MemeCoinFinderByZig.git
cd MemeCoinFinderByZig
```

### 2. Installer les dépendances

Installe ensuite les différentes dépendances nécessaires au fonctionnement du bot :

```bash
pip install websockets requests aiohttp python-dotenv rich
```

---

## 🔐 Configuration

Il faut maintenant créer un fichier `.env`.
Ce fichier permettra de stocker de manière séparée les informations sensibles du bot : **token Telegram**, **clé API Birdeye** et **Chat ID Telegram**.

Crée le fichier avec :

Pour Termux/Linux :
```bash
nano .env
```

Pour Windows :
```bash
notepad .env
```

Puis ajoute les informations suivantes :

```env
TOKEN=ton_token_telegram_ici
BIRDEYE_API_KEY=ta_cle_birdeye_ici
CHAT_ID=ton_id_telegram_ici
```

> ⚠️ **Important :** ne partage jamais ton fichier `.env` publiquement et ne publie jamais tes clés API ou ton token Telegram sur GitHub.

💡 Il est également recommandé d'ajouter `.env` à ton fichier `.gitignore` :

```gitignore
.env
```

---

## 🚀 Lancer le bot

Une fois la configuration terminée, il ne reste plus qu'à lancer Nino :

Pour les francophones :

```bash
python bot.py
```

Pour les non-francophones : 

```bash
python botworld.py
```


Si tout est correctement configuré, le bot commencera à surveiller les nouveaux tokens Pump.fun en temps réel. 📡🔥

---

## 📊 Fonctionnement du scoring

Nino utilise plusieurs indicateurs afin d'évaluer les tokens détectés :

| Source         | Indicateurs                          |  Score |
| -------------- | ------------------------------------ | -----: |
| 🔵 Dexscreener | Market Cap, Volume 24h, Variation 5m | **/4** |
| 🟣 Birdeye     | Liquidité, Holders, Momentum         | **/5** |

🚨 Une alerte Telegram est envoyée lorsque le token atteint au minimum **3/4 sur Dexscreener**.

> ⚠️ **Attention :** le score est uniquement un indicateur automatisé et ne garantit en aucun cas qu'un token est fiable ou rentable. Les memecoins sont extrêmement volatils et comportent des risques importants.

---

## 💬 Telegram

Lorsqu'un token intéressant est détecté, Nino envoie automatiquement une alerte contenant notamment :

* 🪙 Nom et symbole du token
* 📊 Score Dexscreener
* 💰 Market Cap
* 📈 Volume
* 📉 Variation du prix
* 💧 Liquidité
* 👥 Nombre de holders
* ⚡ Momentum
* 🔗 Liens vers Dexscreener et Pump.fun
* 💡 Analyse et avis du bot

---

## ❤️ Statut du bot

Toutes les **3 heures**, Nino envoie automatiquement un message de statut sur Telegram afin de confirmer que le scanner fonctionne toujours correctement. 🤖💚

---

## ⚠️ Disclaimer

Nino est un **outil d'analyse et de surveillance**. Il ne constitue pas un conseil financier et ne garantit aucun rendement.

Les tokens Pump.fun et les memecoins peuvent être extrêmement risqués, volatils et sujets aux **rug pulls, scams et manipulations de marché**.

**Utilise ce bot à tes propres risques et fais toujours tes propres recherches (DYOR).** 🔎

---

## 👥 Contact

telegram : zig47

x : zigxbt

tiktok : zigxbt

instagram : zigxbt

---

## ⭐ Support

Si le projet te plaît, n'hésite pas à laisser une ⭐ au repository GitHub !

**Made with ❤️ for the Solana community.** 🟣🚀




