# ⚡ GGBot - Moteur d'Analyse CS2 & GGRating 3.0 (HLTV 3.0)

GGBot est la suite d'analyse statistique et de calcul de performance de tournoi pour **Counter-Strike 2**.  
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

## 🚀 Utilisation

### 1. Analyser un match unique (.dem)
```bash
python ggbot_ggrating.py --demo "chemin/vers/votre_match.dem"
```
Affiche en console le tableau détaillé du match (GGRating 3.0, HLTV 1.0, ADR, KAST%, Swing/R, First K/D, Multi-kills).

### 2. Traiter un tournoi complet
```bash
python ggbot_batch_tournament.py
```
- Scanne automatiquement toutes les démos du dossier tournoi.
- Calcule les baselines du tournoi (moyennes KAST, ADR, KPR, Swing).
- Normalise le GGRating 3.0 à **1.00 de moyenne**.
- Génère le classement général en CSV et JSON.

### 3. Générer le Dashboard HTML interactif
```bash
python ggbot_html_dashboard.py
```
Crée un rapport HTML complet avec :
- Tri dynamique sur toutes les colonnes (ADR, KAST%, Swing, Frags, Ratings...).
- Barre de recherche en temps réel par joueur ou équipe.
- Comparaison côte à côte GGRating 3.0 vs HLTV 1.0.

---

## 📊 Livrables générés

- `01_classement_general_joueurs_ggrating.csv` : Statistiques complètes par joueur.
- `stats_gglan19_ggrating.json` : Données structurées et baselines du tournoi.
- `rapport_stats_gglan19_ggrating.html` : Dashboard interactif autonome (fonctionne 100% hors-ligne).
