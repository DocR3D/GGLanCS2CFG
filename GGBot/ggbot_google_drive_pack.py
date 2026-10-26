import os
import sys
import json
import shutil
import subprocess
import time
import re

sys.stdout.reconfigure(encoding='utf-8')

stats_dir = r"C:\Users\yonne\Desktop\GGLan\GGLan #19\Stats"
demos_dir = r"C:\Users\yonne\Desktop\GGLan\GGLan #19\Demos"
out_pack_dir = r"D:\GGLan_Google_Drive_Pack"
seven_zip = r"C:\Program Files\7-Zip\7z.exe"

with open(os.path.join(stats_dir, "json", "stats_gglan19_complete.json"), "r", encoding="utf-8") as f:
    match_data = json.load(f)

with open(os.path.join(stats_dir, "json", "stats_gglan19_ggrating.json"), "r", encoding="utf-8") as f:
    ggrating_data = json.load(f)

matches = match_data["matches"]
teams = match_data["teams"]
players = ggrating_data["players"]

# Map match ID to demo file
demo_files = os.listdir(demos_dir)
match_demo_map = {}
for m in matches:
    mid = str(m["match_id"])
    cands = [f for f in demo_files if f.startswith(mid + "_") and f.endswith(".dem")]
    if not cands and mid == "184":
        cands = [f for f in demo_files if "1555-de_ancient" in f and "YVAPALACHERCHER" in f]
    if cands:
        cands.sort(key=lambda x: os.path.getsize(os.path.join(demos_dir, x)), reverse=True)
        match_demo_map[mid] = cands[0]

# Subfolders in pack
teams_pack_dir = os.path.join(out_pack_dir, "Demos_Par_Equipe")
os.makedirs(teams_pack_dir, exist_ok=True)

# Copy root deliverables
print("=== PREPARATION DU PACK GOOGLE DRIVE GGLAN #19 ===")
print("1. Copie des rapports généraux à la racine...")
shutil.copy2(os.path.join(stats_dir, "rapport_stats_gglan19_ggrating.html"), os.path.join(out_pack_dir, "rapport_stats_gglan19_ggrating.html"))
shutil.copy2(os.path.join(stats_dir, "csv", "01_classement_general_joueurs_ggrating.csv"), os.path.join(out_pack_dir, "01_classement_general_joueurs_ggrating.csv"))
shutil.copy2(os.path.join(stats_dir, "csv", "02_classement_equipes.csv"), os.path.join(out_pack_dir, "02_classement_equipes.csv"))

# Root README
readme_root = """===============================================================
  GGLAN #19 - PACK OFFICIEL DES DEMOS ET STATISTIQUES CS2
===============================================================

Bienvenue sur le dossier officiel de partage de la GGLan #19 !

CONTENU DU DOSSIER :
--------------------
1. rapport_stats_gglan19_ggrating.html :
   -> Rapport interactif complet des statistiques du tournoi.
   -> Ouvrez-le dans n'importe quel navigateur (Chrome, Firefox, Edge).
   -> Cliquez sur les en-têtes de colonnes pour trier par ADR, KAST%, Rating, etc.

2. Demos_Par_Equipe/ :
   -> Contient une archive ZIP par équipe (ex: GGLan19_Demos_MANGEMORT.zip).
   -> Téléchargez simplement le ZIP correspondant à votre équipe !
   -> Chaque archive contient tous vos matchs .dem officiels + un récapitulatif texte.

Comment visionner une démo .dem CS2 ?
-------------------------------------
1. Extrayez le fichier .dem dans votre dossier CS2 :
   ex: steamapps/common/Counter-Strike Global Offensive/game/csgo/
2. Lancez Counter-Strike 2.
3. Appuyez sur Shift + F2 pour ouvrir le lecteur de démos GOTV (ou tapez 'playdemo nom_du_fichier' dans la console).
"""
with open(os.path.join(out_pack_dir, "README_GGLAN19.txt"), "w", encoding="utf-8") as f:
    f.write(readme_root)

# Temporary staging directory for building each zip
stage_dir = r"D:\GGLan_Staging_Temp"
if os.path.exists(stage_dir):
    shutil.rmtree(stage_dir)
os.makedirs(stage_dir, exist_ok=True)

# Clean team filename helper
def clean_filename(name):
    clean = re.sub(r'[^\w\-_\.]', '_', name)
    clean = re.sub(r'_+', '_', clean).strip('_')
    return clean

print("\n2. Création des 13 archives d'équipe...")
t_global_start = time.time()

for idx, t_info in enumerate(teams, 1):
    tname = t_info["team_name"]
    clean_t = clean_filename(tname)
    zip_name = f"GGLan19_Demos_{clean_t}.zip"
    zip_final_path = os.path.join(teams_pack_dir, zip_name)
    
    # Team staging directory
    t_stage = os.path.join(stage_dir, clean_t)
    os.makedirs(t_stage, exist_ok=True)
    
    # Find all matches for this team
    team_matches = [m for m in matches if m["equipe_a"] == tname or m["equipe_b"] == tname]
    team_matches.sort(key=lambda m: int(m["match_id"]))
    
    # Write Recap_Matchs.txt
    recap = f"""===============================================================
  GGLAN #19 - RECAPITULATIF DES MATCHS : {tname}
===============================================================

BILAN DE L'EQUIPE :
-------------------
Matchs joués : {t_info['matchs_joues']}
Victoires    : {t_info['victoires']}
Défaites     : {t_info['defaites']}
Nuls         : {t_info.get('nuls', 0)}
Winrate      : {t_info['winrate_pct']}%
Rounds       : {t_info['rounds_gagnes']} gagnés / {t_info['rounds_perdus']} perdus (Diff: {int(t_info['diff_rounds']):+d})

LISTE DES DEMOS INCLUSES DANS CETTE ARCHIVE :
---------------------------------------------
"""
    files_to_compress = []
    
    for m in team_matches:
        mid = str(m["match_id"])
        dem_file = match_demo_map.get(mid)
        if not dem_file:
            continue
            
        sa, sb = int(m["score_a"]), int(m["score_b"])
        is_team_a = (m["equipe_a"] == tname)
        my_score = sa if is_team_a else sb
        opp_score = sb if is_team_a else sa
        opp_team = m["equipe_b"] if is_team_a else m["equipe_a"]
        
        if my_score > opp_score: res_str = "VICTOIRE"
        elif my_score < opp_score: res_str = "DEFAITE"
        else: res_str = "EGALITE"
        
        recap += f"Match #{mid:<3} | {m['date_match']} | vs {opp_team:<24} | {res_str} {my_score:>2}-{opp_score:<2} ({m['maps_jouees']})\n"
        recap += f"  -> Fichier : {dem_file}\n\n"
        
        src_dem = os.path.join(demos_dir, dem_file)
        dst_dem = os.path.join(t_stage, dem_file)
        # Create hardlink or copy to save space and speed
        try:
            os.link(src_dem, dst_dem)
        except:
            shutil.copy2(src_dem, dst_dem)
        files_to_compress.append(dem_file)
        
    recap += """
---------------------------------------------------------------
Pour lancer une démo dans CS2 :
1. Placez le fichier .dem dans : steamapps/common/Counter-Strike Global Offensive/game/csgo/
2. En jeu, ouvrez la console et tapez : playdemo <nom_du_fichier>
---------------------------------------------------------------
"""
    recap_file = f"Recap_Matchs_{clean_t}.txt"
    with open(os.path.join(t_stage, recap_file), "w", encoding="utf-8") as f:
        f.write(recap)
        
    # Copy html report into team folder too
    shutil.copy2(os.path.join(stats_dir, "rapport_stats_gglan19_ggrating.html"), os.path.join(t_stage, "rapport_stats_gglan19_ggrating.html"))
    
    # Run 7z to create zip
    t_start = time.time()
    cmd = [seven_zip, "a", "-tzip", "-mx=5", "-mmt=on", zip_final_path, "*"]
    proc = subprocess.run(cmd, cwd=t_stage, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    t_end = time.time()
    
    zip_size_mb = os.path.getsize(zip_final_path) / (1024 * 1024)
    print(f"[{idx:02d}/13] {tname:<25} : {len(team_matches):2} matchs -> {zip_name} ({zip_size_mb:.1f} Mo en {t_end - t_start:.1f}s)")
    
    # Clean staging team dir to save temp space
    shutil.rmtree(t_stage)

# Remove global staging dir
if os.path.exists(stage_dir):
    shutil.rmtree(stage_dir)

tot_time = time.time() - t_global_start
tot_zip_gb = sum(os.path.getsize(os.path.join(teams_pack_dir, f)) for f in os.listdir(teams_pack_dir)) / (1024 * 1024 * 1024)

print(f"\n=== PACK TERMINE AVEC SUCCES EN {tot_time:.1f} SECONDES ! ===")
print(f"Volume total des 13 archives ZIP : {tot_zip_gb:.2f} Go")
print(f"Emplacement physique : {out_pack_dir}")
print(f"Raccourci Bureau : C:\\Users\\yonne\\Desktop\\GGLan\\Google_Drive_Pack")
