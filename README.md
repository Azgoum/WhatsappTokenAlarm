# Claude Token Monitor 🦀

Widget Windows always-on-top affichant ta consommation Claude.ai en temps réel, exactement comme sur https://claude.ai/settings/usage

![Screenshot](screenshot.png)

## Fonctionnalités

- **Affichage temps réel** : Session (5h) et usage hebdomadaire
- **Barres de progression** colorées selon le niveau (vert → orange → rouge)
- **Always-on-top** : toujours visible sur ton bureau
- **Réductible** : minimise en barre compacte
- **Notification WhatsApp** : reçois un message quand tes tokens sont dispo (via OpenClaw)
- **Auto-refresh** : mise à jour toutes les 2 minutes

## Prérequis

- Python 3.8+
- Firefox avec une session active sur claude.ai
- [OpenClaw](https://openclaw.ai) configuré avec WhatsApp (optionnel, pour les notifications)

## Installation

```bash
git clone https://github.com/ton-user/WhatsappTokenAlarm.git
cd WhatsappTokenAlarm
pip install -r requirements.txt
```

## Utilisation

### Lancement

Double-cliquer sur `start.bat` ou :

```bash
python token_monitor.py
```

### Important

**Tu dois être connecté sur claude.ai dans Firefox** pour que le widget puisse récupérer les données. Le widget utilise les cookies de ta session Firefox.

### Fonctionnement

1. Le widget récupère les données depuis l'API claude.ai
2. Affiche le % d'utilisation session et hebdomadaire
3. Affiche l'heure du prochain reset
4. Quand l'usage atteint 95%, une notification WhatsApp est programmée pour le reset

## Configuration

Le numéro WhatsApp est configuré dans `token_monitor.py` :

```python
self.whatsapp_number = '+33XXXXXXXXX'
```

## Fichiers

```
WhatsappTokenAlarm/
├── token_monitor.py   # Application principale
├── start.bat          # Lanceur Windows
├── requirements.txt   # Dépendances Python
├── state.json         # État persistant (auto-généré)
├── .gitignore
└── README.md
```

## API Claude.ai

Le widget utilise l'endpoint non-documenté :
```
GET https://claude.ai/api/organizations/{uuid}/usage
```

Qui retourne :
```json
{
  "five_hour": {
    "utilization": 75.0,
    "resets_at": "2026-02-06T13:00:00+00:00"
  },
  "seven_day": {
    "utilization": 42.0,
    "resets_at": "2026-02-09T08:00:00+00:00"
  }
}
```

## Dépendances

- **browser-cookie3** : pour lire les cookies Firefox
- **OpenClaw** (optionnel) : pour les notifications WhatsApp

## Licence

MIT
