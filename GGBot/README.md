# ⚡ GGBot - Moteur d'Analyse CS2 & GGRating 3.0 (HLTV 3.0)

GGBot est la suite complète d'analyse statistique, de calcul de performance et d'organisation de tournoi pour **Counter-Strike 2**.  
Il intègre le moteur **GGRating 3.0**, une implémentation complète de l'architecture **HLTV Rating 3.0** fonctionnant par extraction tick-par-tick des démos GOTV (`.dem`) via `demoparser2` (écrit en Rust).

---

## 🎯 Architecture de GGRating 3.0

Contrairement aux ratings historiques (comme le Rating 1.0 basé sur les frags bruts), **GGRating 3.0** contextualise chaque action à travers 6 piliers :

$$\text{GGRating} = 0.25 \cdot \text{eKPR} + 0.25 \cdot \text{eADR} + 0.20 \cdot \text{eKAST} + 0.12 \cdot \text{Swing} + 0.10 \cdot \text{Survie} + 0.08 \cdot \text{MultiKills}$$

1. **eKPR (Economy-Adjusted Kills - 25%) :**
   Pondération économique dynamique. Tuer un joueur équipé d'un fusil avec un pistolet octroie $+25\%$ de valeur. Les frags anti-éco faciles au fusil face à des pistolets sans armure sont dégonflés de $-25\%$.
2. **eADR (Economy-Adjusted Damage - 25%) :**
   Dégâts réels infligés par round (plafonnés à 100 max par victime, excluant les overkills et les tirs alliés), pondérés selon l'armure et l'économie adverse.
3. **eKAST (20%) :**
   Pourcentage de rounds utiles où le joueur a réalisé au moins une des actions suivantes :
   - **K** (Kill) : $\ge 1$ frag dans le round.
   - **A** (Assist) : $\ge 40$ dégâts réels infligés à un adversaire éliminé.
   - **S** (Survie) : En vie à la fin du round.
   - **T** (Traded) : Mort vengée par un coéquipier dans une fenêtre de moins de $5.0$ secondes ($320$ ticks à 64 tick).
4. **Round Swing (12% - Remplace l'Impact) :**
   Mesure en temps réel le delta de probabilité de victoire du round ($\Delta \text{Win\%}$) pour chaque action :
   - Opening kill en 5v5 : $+23\%$ pour le tueur, $-23\%$ pour la victime.
   - Duel gagné en clutch 1v2 : $+32\%$.
   - Dernier frag en 5v1 : $+1\%$.
5. **Survie Utile (10%) :**
   Valorise les rounds survécus utiles tout en pénalisant les *saves* passives dans les rounds mathématiquement perdus.
6. **Multi-Kills (8%) :**
   Fréquence des 2k, 3k, 4k et Aces, rééquilibrée pour éviter les doublons avec le Swing.

---

## 📦 Installation

```bash
git clone https://github.com/DocR3D/GGLanCS2CFG.git
cd GGLanCS2CFG/GGBot
pip install -r requirements.txt
```

Prérequis :
- Python 3.9+
- `demoparser2`
- `pandas`
- `numpy`

---

## 🚀 Outils de la Suite GGBot

### 1. `ggbot_ggrating.py` - Analyser un match unique (.dem)
```bash
python ggbot_ggrating.py --demo "chemin/vers/votre_match.dem"
```
Affiche en console le tableau détaillé du match (GGRating 3.0, HLTV 1.0, ADR, KAST%, Swing/R, First K/D, Multi-kills).

### 2. `ggbot_batch_tournament.py` - Traitement global du tournoi
```bash
python ggbot_batch_tournament.py
```
- Scanne automatiquement toutes les démos du dossier tournoi.
- Calcule les baselines du tournoi (moyennes KAST, ADR, KPR, Swing).
- Normalise le GGRating 3.0 à **1.00 de moyenne**.
- Génère le classement général en CSV et JSON.

### 3. `ggbot_fun_and_maps.py` - Statistiques de maps & Trophées insolites
```bash
python ggbot_fun_and_maps.py
```
- Analyse l'équilibrage CT / T de chaque carte jouée, le taux d'overtimes et les moyennes de rounds.
- Extrait les statistiques fun : massacre de poules sur Inferno, frags au couteau, électrocutions au Zeus x27, morts de la bombe C4, smoke hackers, no-scopes sniper, kills aveuglés (Ray Charles) et record de distance.

### 4. `ggbot_html_dashboard.py` - Générateur de Dashboard interactif
```bash
python ggbot_html_dashboard.py
```
Crée un rapport HTML autonome ultra-complet (`rapport_stats_gglan19_ggrating.html`) avec :
- **Tri dynamique par clic** sur toutes les colonnes (ADR, KAST%, Swing, Frags, Ratings, Différence de rounds...).
- Barre de recherche en temps réel par joueur ou équipe.
- Section dédiée à l'équilibrage CT / T des cartes jouées.
- Palmarès insolite & Fun Awards en cartes graphiques.
- Comparaison côte à côte GGRating 3.0 vs HLTV 1.0.

### 5. `ggbot_google_drive_pack.py` - Préparation du Pack de Partage Google Drive
```bash
python ggbot_google_drive_pack.py
```
- Construit automatiquement une archive ZIP par équipe contenant tous leurs matchs `.dem` officiels, le récapitulatif textuel de leurs rencontres et le dashboard HTML.
- Génère le README officiel pour les capitaines d'équipes et les joueurs.

---

## 📊 Livrables générés

- `01_classement_general_joueurs_ggrating.csv` : Statistiques complètes par joueur.
- `02_classement_equipes.csv` : Classement général des équipes.
- `stats_gglan19_ggrating.json` : Données structurées et baselines du tournoi.
- `stats_gglan19_fun_and_maps.json` : Données cartographiques et trophées insolites.
- `rapport_stats_gglan19_ggrating.html` : Dashboard interactif autonome (fonctionne 100% hors-ligne).
- `Demos_Par_Equipe/` : 13 archives ZIP prêtes à être partagées sur Google Drive.

