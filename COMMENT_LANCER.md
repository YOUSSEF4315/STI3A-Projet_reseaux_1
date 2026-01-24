# Comment Lancer MedievAIl BAIttle GenerAIl

## 🚀 Méthodes de Lancement

### Option 1: Launcher Interactif (RECOMMANDÉ)
```bash
python launch.py
```
Menu interactif avec toutes les options disponibles.

---

### Option 2: Menu GUI

#### Menu Plein Écran (Par défaut)
```bash
python run_menu.py
# ou
python -m view.menu
```

#### Menu Fenêtré (Si problème avec plein écran)
```bash
python run_menu_windowed.py
```

---

### Option 3: Simulation Visuelle
```bash
python visual_simulation.py
```
Lance directement une bataille avec interface graphique.

---

### Option 4: Simulation Console
```bash
python main.py
```
Mode texte avec affichage dans le terminal.

---

### Option 5: Vue Terminal (Curses)
```bash
python run_terminal.py
```
Interface texte avancée avec ncurses.

---

### Option 6: CLI Battle (Ligne de commande)
```bash
# Lancer une bataille
python -m presenter.battle run Scenario_Standard Daft Braindead

# Mode terminal
python -m presenter.battle run Scenario_Standard Daft Braindead -t

# Tournoi
python -m presenter.battle tourney -G Daft Braindead GeneralStrategus -N 10

# Charger une sauvegarde
python -m presenter.battle load quicksave.pkl
```

---

## 🔧 Diagnostic et Dépannage

### Problème avec le menu ?

1. **Lancer le diagnostic:**
```bash
python diagnose_menu.py
```

2. **Si le plein écran ne fonctionne pas:**
   - Utilisez la version fenêtrée: `python run_menu_windowed.py`
   - Ou option 2 dans le launcher

3. **Erreurs d'import:**
   - Vérifiez que vous êtes dans le bon répertoire
   - Vérifiez que pygame est installé: `pip install pygame`

---

## 📁 Structure des Fichiers de Lancement

```
MedievAIl_Battle_GenerAIl/
├── launch.py              # ⭐ Launcher interactif
├── run_menu.py            # Menu GUI plein écran
├── run_menu_windowed.py   # Menu GUI fenêtré
├── visual_simulation.py   # Simulation graphique
├── main.py                # Simulation console
├── run_terminal.py        # Vue terminal
└── diagnose_menu.py       # Diagnostic
```

---

## 🎮 Contrôles du Menu

### Dans le Menu
- **Souris**: Navigation et sélection
- **Clic**: Sélectionner les options

### Pendant une Bataille
- **P**: Pause / Lecture
- **ESPACE**: Pas à pas
- **Molette**: Zoom
- **Clic gauche/droit**: Déplacer la caméra
- **M**: Afficher/Cacher la minimap
- **Flèches**: Déplacer la caméra
- **F11/F12**: Sauvegarde/Chargement rapide
- **ESC**: Retour au menu

---

## 🐛 Problèmes Courants

### "Module not found"
```bash
# Vérifiez que vous êtes dans le bon répertoire
cd d:\Paul\Algo\github

# Vérifiez la structure MVP
ls model/ view/ presenter/
```

### "Pygame not installed"
```bash
pip install pygame
```

### "Can't create display"
- Essayez la version fenêtrée du menu
- Vérifiez vos drivers graphiques
- Essayez sur un seul moniteur si vous en avez plusieurs

### Menu se ferme immédiatement
- Lancez depuis le terminal pour voir les erreurs
- Utilisez `diagnose_menu.py` pour identifier le problème

---

## 📊 Modes de Jeu Disponibles

1. **GUI Menu**: Interface complète avec sélection IA/scénario
2. **Visual Simulation**: Bataille pré-configurée avec rendu graphique
3. **Console Simulation**: Bataille en mode texte avec statistiques
4. **Terminal View**: Interface curses pour observation détaillée
5. **CLI Battle**: Contrôle complet via ligne de commande

---

## ✅ Vérification Rapide

```bash
# Test complet
python diagnose_menu.py

# Test imports
python -c "from view.menu import MainMenu; print('OK')"

# Test scénario
python test_menu.py
```

---

## 💡 Recommandations

- **Première fois**: Utilisez `python launch.py` (option 1 ou 2)
- **Développement**: Utilisez `python visual_simulation.py`
- **Tests IA**: Utilisez `python -m presenter.battle tourney`
- **Problèmes**: Utilisez `python diagnose_menu.py`
