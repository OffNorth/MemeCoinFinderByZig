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

### 2. Télécharger le code

**Option A (recommandée)** : Via Git (si tu as Git installé)
```bash
git clone https://github.com/OffNorth/MemeCoinFinderByZig.git
cd MemeCoinFinderByZig
