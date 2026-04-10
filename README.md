# Domoticz iRobot Roomba Plugin

[![GitHub stars](https://img.shields.io/github/stars/ton-compte/roomba-domoticz?style=social)](https://github.com/ton-compte/roomba-domoticz)
[![Version](https://img.shields.io/badge/version-1.2.5-blue.svg)](https://github.com/ton-compte/roomba-domoticz/releases)
[![Domoticz](https://img.shields.io/badge/Domoticz-%E2%89%A54.0-orange.svg)](https://www.domoticz.com/)
[![Python](https://img.shields.io/badge/Python-3.7%2B-yellow.svg)](https://www.python.org/)

**Plugin Domoticz pour contrôler localement un iRobot Roomba** via la bibliothèque `Roomba980-Python` et `asyncio`. Récupération automatique des identifiants BLID/Password via une interface web intégrée.

## ✨ Fonctionnalités

- ✅ Contrôle local complet (start, pause, dock, etc.).
- ✅ Interface d'enrôlement BLID/Password automatique.
- ✅ Devices Domoticz créés automatiquement.
- ✅ Installation automatique des dépendances Python.
- ✅ Sauvegarde locale des identifiants.
- ✅ Worker asyncio performant et thread-safe.

## 📱 Devices créés automatiquement

| **Device** | **Type** | **Description** |
|------------|----------|-----------------|
| **État** | Text | Phase courante (Running, Charging, etc.) |
| **Batterie** | Custom | Niveau de charge % |
| **Bac plein** | Switch | Détection bac plein |
| **Commandes** | Selector Switch | Start, Pause, Dock, etc. |

## 🛠️ Installation rapide (2 min)

```bash
# 1. Copier le plugin
cd ~/.domoticz/plugins
git clone https://github.com/ton-compte/roomba-domoticz.git Roomba
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
5. Copie **BLID** et **Password** dans Domoticz automatique.

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

## 🔧 Dépendances (auto-installées)

| **Package** | **Source** | **Rôle** |
|-------------|------------|----------|
| `paho-mqtt` | PyPI | MQTT Roomba |
| `roomba` | GitHub NickWaterton | Protocole Roomba |

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

**Compatible Roomba 600/900/i/s WiFi** ✨
```