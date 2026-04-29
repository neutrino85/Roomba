**Domoticz iRobot Roomba Plugin**  

[![GitHub stars](https://img.shields.io/github/stars/ton-compte/roomba-domoticz?style=social)](https://github.com/ton-compte/roomba-domoticz)  
[![Version](https://img.shields.io/badge/version-1.2.5-blue.svg)](https://github.com/ton-compte/roomba-domoticz/releases)  
[![Domoticz](https://img.shields.io/badge/Domoticz-%E2%89%A54.0-orange.svg)](https://www.domoticz.com/)  
[![Python](https://img.shields.io/badge/Python-3.7%2B-yellow.svg)](https://www.python.org/)

---

[🔗 Version française](#-version-française)

## 🇬🇧 **English Version**

This is a Domoticz plugin that allows you to control your local iRobot Roomba (models 600/900/i/s Wi‑Fi) through the `Roomba980-Python` library and `asyncio`. It automatically retrieves BLID/Password via an embedded web interface.

**Features**

- Full local control (start, pause, dock, etc.)  
- Automatic BLID/Password enrollment interface  
- Automatic creation of Domoticz devices  
- Self‑installing Python dependencies  
- Local storage of credentials  
- Asyncio worker – performant and thread‑safe  

### Devices created automatically  

| Device | Type | Description |
|--------|------|-------------|
| **State** | Text | Current phase (Running, Charging, …) |
| **Battery** | Custom | Charge level % |
| **Tank full** | Switch | Tank‑full detection |
| **Commands** | Selector Switch | Start, Pause, Dock, etc. |

### Quick installation (≈2 min)

```bash
# 1. Clone the plugin
cd ~/.domoticz/plugins
git clone https://github.com/neutrino85/Roomba.git Roomba
cd Roomba

# 2. Restart Domoticz
sudo systemctl restart domoticz
```

That’s it – the rest is automatic.

### First use  

1. **Add the hardware** → Configuration → Hardware → Add → *iRobot Roomba* → IP = local, BLID/Password = leave blank, Enrollment port = 8788.  
2. **Enroll credentials**  
   1. Activate the device.  
   2. Open `http://IP_Domoticz:8788`.  
   3. On the Roomba press **HOME** for 2–20 s → beep.  
   4. Click **“Get credentials”**.  
   5. Copy BLID & Password into Domoticz – they are saved automatically.  

⚠️ *Only one local connection is supported at a time.*

### Project layout  

```
Roomba/
├── plugin.py                     # Main Domoticz plugin
├── enrollment_server.py          # HTTP enrollment server
├── lib_manager.py                # Auto‑install dependencies
├── roomba/                       # Roomba980-Python library
├── credentials.json              # Saved credentials
└── README.md
```

### Auto‑installed dependencies  

| Package | Source | Role |
|---------|--------|------|
| `paho-mqtt` | PyPI | MQTT for Roomba |
| `roomba` | GitHub NickWaterton | Roomba protocol |

### Quick troubleshooting  

| Problem | Solution |
|---------|----------|
| “Library missing” | Click **Install dependencies** in the enrollment UI |
| Enrollment fails | Verify Roomba IP + Home button beep |
| Devices not created | Accept new devices when prompted |
| Detailed logs | Set Debug mode to 1 or 2 |

### Available commands  

```
Stop    → Immediate stop
Start   → Begin cleaning
Pause   → Pause
Resume  → Resume cleaning
Dock    → Return home
Reboot  → Restart Roomba
```

---

## 🇫🇷 **Version française**  

# Domoticz iRobot Roomba Plugin

[![GitHub stars](https://img.shields.io/github/stars/ton-compte/roomba-domoticz?style=social)](https://github.com/ton-compte/roomba-domoticz)  
[![Version](https://img.shields.io/badge/version-1.2.5-blue.svg)](https://github.com/ton-compte/roomba-domoticz/releases)  
[![Domoticz](https://img.shields.io/badge/Domoticz-%E2%89%A54.0-orange.svg)](https://www.domoticz.com/)  
[![Python](https://img.shields.io/badge/Python-3.7%2B-yellow.svg)](https://www.python.org/)

**Plugin Domoticz pour contrôler localement un iRobot Roomba** via la bibliothèque `Roomba980-Python` et `asyncio`. Récupération automatique des identifiants BLID/Password via une interface web intégrée.

## ✨ Fonctionnalités  

- ✅ Contrôle local complet (start, pause, dock, etc.).  
- ✅ Interface d’enrôlement BLID/Password automatique.  
- ✅ Devices Domoticz créés automatiquement.  
- ✅ Installation automatique des dépendances Python.  
- ✅ Sauvegarde locale des identifiants.  
- ✅ Worker asyncio performant et thread‑safe.

## 📱 Devices créés automatiquement  

| **Device** | **Type** | **Description** |
|-----------|----------|-----------------|
| **État** | Text | Phase courante (Running, Charging, etc.) |
| **Batterie** | Custom | Niveau de charge % |
| **Bac plein** | Switch | Détection bac plein |
| **Commandes** | Selector Switch | Start, Pause, Dock, etc. |

## 🛠️ Installation rapide (2 min)

```bash
# 1. Copier le plugin
cd ~/.domoticz/plugins
git clone https://github.com/neutrino85/Roomba.git Roomba
cd Roomba

# 2. Redémarrer Domoticz
sudo systemctl restart domoticz
```

**C'est tout !** Le plugin gère le reste automatiquement.

## 🚀 Première utilisation  

### 1. Ajouter le matériel Roomba  
```
Configuration → Matériel → Ajouter
Type: iRobot Roomba
IP Roomba: 192.168.x.x (adresse locale)
BLID/Password: (laisser vide)
Port Enrollment: 8788
```

### 2. Enrollment des identifiants  
1. **Active** le matériel.  
2. Ouvre `http://IP_Domoticz:8788`.  
3. Sur le Roomba : **HOME** 2s à 20s → bip.  
4. Clique **"Récupérer les identifiants"**.  
5. Copie **BLID** et **Password** dans Domoticz automatiquement.

```
⚠️ Note : Une seule connexion locale à la fois
```

## 📂 Structure du projet  

```
Roomba/
├── plugin.py              # Plugin principal Domoticz
├── enrollment_server.py   # Serveur HTTP enrollment  
├── lib_manager.py         # Installation auto dépendances
├── roomba/                # Bibliothèque Roomba980-Python
├── credentials.json       # Identifiants sauvegardés
└── README.md
```

## 🐛 Dépannage rapide  

| **Problème** | **Solution** |
|--------------|--------------|
| "Bibliothèque manquante" | Clique "Installer dépendances" dans l'interface enrôlement |
| Enrôlement échoue | Vérifie IP Roomba + bouton HOME bip |
| Devices non créés | Accepter les nouveaux dispositifs dans les paramètres de Domoticz |
| Logs détaillés | Mode Debug = 1 ou 2 dans paramètres |

## 📱 Commandes disponibles  

```
Stop    → Arrêt immédiat
Start   → Démarrage nettoyage  
Pause   → Pause
Resume  → Reprendre
Dock    → Retour base
Reboot  → Redémarrage Roomba
```

## 🙏 Auteurs & Credits  

- **Auteur** : Neutrino  
- **Bibliothèque Roomba** : [NickWaterton/Roomba980-Python](https://github.com/NickWaterton/Roomba980-Python)  
- **Fork roomba** : [neutrino85/Roomba980-Python](https://github.com/neutrino85/Roomba980-Python)

---

