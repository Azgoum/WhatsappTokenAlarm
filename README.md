# Claude Token Alarm 🦀

Widget Windows always-on-top qui surveille tes limites Claude Code et t'envoie une notification WhatsApp quand tes tokens sont de nouveau disponibles.

## Fonctionnalités

- **Widget always-on-top** : fenêtre compacte toujours visible sur ton bureau
- **Bouton "Limite atteinte"** : clique quand tu vois le message de limite Claude
- **Countdown timer** : affiche le temps restant avant la réinitialisation (5h)
- **Notification WhatsApp** : reçois un message automatique quand tes tokens sont dispo
- **Réductible** : minimise en barre compacte
- **Persistance** : l'état est sauvegardé, reprend le timer même après redémarrage

## Prérequis

- Python 3.8+
- [OpenClaw](https://openclaw.ai) configuré avec WhatsApp
- Tkinter (inclus avec Python sur Windows)

## Installation

```bash
git clone https://github.com/ton-user/WhatsappTokenAlarm.git
cd WhatsappTokenAlarm
```

## Utilisation

### Lancement

Double-cliquer sur `start.bat` ou :

```bash
python token_monitor.py
```

### Workflow

1. Utilise Claude Code normalement
2. Quand tu vois le message "limite atteinte", clique sur **⚠️ Limite atteinte**
3. Le compteur démarre (5 heures)
4. À la fin du countdown, tu reçois un WhatsApp : "🦀 Tes tokens Claude sont de nouveau disponibles!"
5. Clique sur **✓ Reset** pour effacer l'état

## Configuration

Le numéro WhatsApp par défaut est configuré dans `token_monitor.py`. Modifie la ligne :

```python
self.whatsapp_number = '+33611788514'
```

## Fichiers

```
WhatsappTokenAlarm/
├── token_monitor.py   # Application principale
├── start.bat          # Lanceur Windows
├── state.json         # État persistant (auto-généré)
├── .gitignore
└── README.md
```

## Dépendances externes

- **OpenClaw** : pour l'envoi de messages WhatsApp
  ```bash
  npm install -g openclaw
  openclaw setup
  ```

## Licence

MIT
