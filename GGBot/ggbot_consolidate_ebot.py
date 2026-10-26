import os
import sys
import gzip
import json
import csv
import re
from datetime import datetime
import pandas as pd
from demoparser2 import DemoParser

sys.stdout.reconfigure(encoding='utf-8')

stats_dir = r"C:\Users\yonne\Desktop\GGLan\GGLan #19\Stats"
demos_dir = r"C:\Users\yonne\Desktop\GGLan\GGLan #19\Demos"
backups_dir = r"C:\Users\yonne\Desktop\GGLan\GGLan #19\Backups_Rounds"
sql_gz = os.path.join(stats_dir, "database", "ebotv3_full_backup.sql.gz")

# 1. Load Base JSON Data
with open(os.path.join(stats_dir, "json", "stats_gglan19_complete.json"), "r", encoding="utf-8") as f:
    base_data = json.load(f)

# Filter base matches to the original 66 eBot matches
base_matches = [m for m in base_data["matches"] if int(m["match_id"]) not in [126, 181, 183, 184]]
base_players = {p["steamid"]: dict(p) for p in base_data["players"]}

# 2. Map SteamID / Pseudo to Real Team Names from SQL Dump
print("[1/5] Cartographie des vrais noms d'équipes depuis le dump SQL...")
match_teams = {}
with gzip.open(sql_gz, 'rt', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if 'insert into' in line.lower() and 'matchs' in line.lower():
            entries = line.split("),(")
            for e in entries:
                parts = e.strip("();").split(",")
                if len(parts) >= 10:
                    try:
                        mid = int(parts[0].replace("INSERT INTO `matchs` VALUES (", "").strip("` '\""))
                        ta = parts[6].strip(" '\"")
                        tb = parts[9].strip(" '\"")
                        match_teams[mid] = (ta, tb)
                    except:
                        pass

player_team_counts = {}
with gzip.open(sql_gz, 'rt', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if 'insert into' in line.lower() and 'players' in line.lower():
            entries = line.split("),(")
            for e in entries:
                parts = e.strip("();").split(",")
                if len(parts) >= 10:
                    try:
                        mid = int(parts[1].strip(" '\""))
                        side = parts[4].strip(" '\"").lower()
                        steamid = parts[6].strip(" '\"")
                        pseudo = parts[9].strip(" '\"")
                        if mid in match_teams and side in ['a', 'b']:
                            tname = match_teams[mid][0] if side == 'a' else match_teams[mid][1]
                            key = steamid if steamid else pseudo
                            if key not in player_team_counts:
                                player_team_counts[key] = {}
                            player_team_counts[key][tname] = player_team_counts[key].get(tname, 0) + 1
                    except:
                        pass

steam_to_real_team = {}
for k, counts in player_team_counts.items():
    best_t = max(counts.items(), key=lambda x: x[1])[0]
    steam_to_real_team[k] = best_t

# Update team names in base players
for sid, p in base_players.items():
    real_team = steam_to_real_team.get(sid) or steam_to_real_team.get(p["pseudo"])
    if real_team:
        p["team_name"] = real_team

# 3. Helper Functions for SteamID and HLTV Rating
def to_steam3(sid):
    if not sid:
        return ""
    sid_str = str(sid).strip()
    if sid_str.startswith("[U:1:"):
        return sid_str
    try:
        val = int(sid_str)
        if val > 76561197960265728:
            acc_id = val - 76561197960265728
            return f"[U:1:{acc_id}]"
        else:
            return f"[U:1:{val}]"
    except:
        return sid_str

def compute_hltv_rating(kills, deaths, rounds, k1, k2, k3, k4, k5):
    if rounds <= 0:
        return 0.0
    kill_rating = (kills / rounds) / 0.679
    surv_rating = (max(0, rounds - deaths) / rounds) / 0.317
    mk_score = (k1 + 4 * k2 + 9 * k3 + 16 * k4 + 25 * k5) / rounds
    mk_rating = mk_score / 1.207
    rating = (kill_rating + 0.7 * surv_rating + mk_rating) / 2.7
    return round(rating, 2)

# Helper to parse CS2 round backup files
def parse_backup_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    
    fh = re.search(r'"FirstHalfScore"\s*\{\s*"team1"\s*"(\d+)"\s*"team2"\s*"(\d+)"', text)
    sh = re.search(r'"SecondHalfScore"\s*\{\s*"team1"\s*"(\d+)"\s*"team2"\s*"(\d+)"', text)
    
    t1_score = int(fh.group(1)) + int(sh.group(1)) if fh and sh else 0
    t2_score = int(fh.group(2)) + int(sh.group(2)) if fh and sh else 0
    
    p1_block = re.search(r'"PlayersOnTeam1"\s*\{(.*?)"PlayersOnTeam2"', text, re.DOTALL)
    p2_block = re.search(r'"PlayersOnTeam2"\s*\{(.*?)\n\t\}', text, re.DOTALL)
    
    def extract_players(block_text):
        res = []
        if not block_text:
            return res
        player_blocks = re.findall(r'"(\d{8,10})"\s*\{(.*?)\}', block_text, re.DOTALL)
        for sid, pdata in player_blocks:
            name_m = re.search(r'"name"\s*"([^"]+)"', pdata)
            name = name_m.group(1) if name_m else sid
            kills_m = re.search(r'"kills"\s*"(\d+)"', pdata)
            kills = int(kills_m.group(1)) if kills_m else 0
            deaths_m = re.search(r'"deaths"\s*"(\d+)"', pdata)
            deaths = int(deaths_m.group(1)) if deaths_m else 0
            ast_m = re.search(r'"assists"\s*"(\d+)"', pdata)
            ast = int(ast_m.group(1)) if ast_m else 0
            hs_m = re.search(r'"enemyHSs"\s*"(\d+)"', pdata)
            hs = int(hs_m.group(1)) if hs_m else 0
            firstk_m = re.search(r'"firstKs"\s*"(\d+)"', pdata)
            first_k = int(firstk_m.group(1)) if firstk_m else 0
            
            k1_m = re.search(r'"enemyKs"\s*"(\d+)"', pdata)
            k2_m = re.search(r'"enemy2Ks"\s*"(\d+)"', pdata)
            k3_m = re.search(r'"enemy3Ks"\s*"(\d+)"', pdata)
            k4_m = re.search(r'"enemy4Ks"\s*"(\d+)"', pdata)
            k5_m = re.search(r'"enemy5Ks"\s*"(\d+)"', pdata)
            
            k2 = int(k2_m.group(1)) if k2_m else 0
            k3 = int(k3_m.group(1)) if k3_m else 0
            k4 = int(k4_m.group(1)) if k4_m else 0
            k5 = int(k5_m.group(1)) if k5_m else 0
            total_k = int(k1_m.group(1)) if k1_m else kills
            k1 = max(0, total_k - (2*k2 + 3*k3 + 4*k4 + 5*k5))
            
            res.append({
                "steamid": to_steam3(sid),
                "pseudo": name,
                "kills": kills,
                "deaths": deaths,
                "assists": ast,
                "hs": hs,
                "first_kills": first_k,
                "k1": k1, "k2": k2, "k3": k3, "k4": k4, "k5": k5
            })
        return res
        
    return {
        "score_1": t1_score,
        "score_2": t2_score,
        "team1_players": extract_players(p1_block.group(1) if p1_block else ""),
        "team2_players": extract_players(p2_block.group(1) if p2_block else "")
    }

# 4. Process Extra Matches
print("[2/5] Extraction et validation des 4 matchs complémentaires (#126, #181, #183, #184)...")
extra_matches = []
extra_player_stats = []

# Match 126
b126 = parse_backup_file(os.path.join(backups_dir, "Sully", "ebot_126_round24.txt"))
extra_matches.append({
    "match_id": "126",
    "date_match": "2026-10-24 15:30:00",
    "equipe_a": "NousDegorgeonsPoireaux",
    "score_a": "12",
    "score_b": "12",
    "equipe_b": "TEAM VINIWAZ",
    "vainqueur": "Égalité",
    "maps_jouees": "de_dust2",
    "ip_serveur": "10.100.100.241:27015"
})
for p in b126["team1_players"]:
    p["team_name"] = "NousDegorgeonsPoireaux"
    p["rounds"] = 24
    extra_player_stats.append(p)
for p in b126["team2_players"]:
    p["team_name"] = "TEAM VINIWAZ"
    p["rounds"] = 24
    extra_player_stats.append(p)

# Match 181
b181 = parse_backup_file(os.path.join(backups_dir, "Sully", "ebot_181_round23.txt"))
extra_matches.append({
    "match_id": "181",
    "date_match": "2026-10-25 14:35:00",
    "equipe_a": "OnVeutOffice (LeRetour)",
    "score_a": "13",
    "score_b": "10",
    "equipe_b": "FTBCN",
    "vainqueur": "OnVeutOffice (LeRetour)",
    "maps_jouees": "de_inferno",
    "ip_serveur": "10.100.100.241:27015"
})
for p in b181["team1_players"]:
    p["team_name"] = "OnVeutOffice (LeRetour)"
    p["rounds"] = 23
    extra_player_stats.append(p)
for p in b181["team2_players"]:
    p["team_name"] = "FTBCN"
    p["rounds"] = 23
    extra_player_stats.append(p)

# Match 183
b183 = parse_backup_file(os.path.join(backups_dir, "VM_ServeurMaxime", "a2083c11-aa0f-4cc8-a728-dd251b83910d", "ebot_183_round24.txt"))
extra_matches.append({
    "match_id": "183",
    "date_match": "2026-10-25 15:55:00",
    "equipe_a": "MANGEMORT",
    "score_a": "11",
    "score_b": "13",
    "equipe_b": "YVAPALACHERCHER",
    "vainqueur": "YVAPALACHERCHER",
    "maps_jouees": "de_cache",
    "ip_serveur": "10.100.100.201:27015"
})
for p in b183["team1_players"]:
    p["team_name"] = "MANGEMORT"
    p["rounds"] = 24
    extra_player_stats.append(p)
for p in b183["team2_players"]:
    p["team_name"] = "YVAPALACHERCHER"
    p["rounds"] = 24
    extra_player_stats.append(p)

# Match 184 (Ancient demo parse)
p184 = DemoParser(os.path.join(demos_dir, "auto-20261025-1555-de_ancient-eBot____YVAPALACHERCHER_vs_MANGEMORT.dem"))
rstarts = p184.parse_event("round_start").sort_values("tick").reset_index(drop=True)
rends = p184.parse_event("round_end").sort_values("tick").reset_index(drop=True)
rends = rends[rends["winner"].isin(["CT", "T"])].reset_index(drop=True)

rounds184 = []
for i in range(len(rends)):
    s_tick = rstarts.iloc[i]["tick"] if i < len(rstarts) else rends.iloc[i-1]["tick"]
    e_tick = rends.iloc[i]["tick"]
    rounds184.append((i+1, s_tick, e_tick, rends.iloc[i]["winner"]))

deaths184 = p184.parse_event("player_death")
def get_round_184(tick):
    for r_num, s_tick, e_tick, _ in rounds184:
        if s_tick <= tick <= e_tick:
            return r_num
    return None

deaths184["match_round"] = deaths184["tick"].apply(get_round_184)
valid_deaths184 = deaths184[deaths184["match_round"].notna()].copy()
kills184 = valid_deaths184[(valid_deaths184["attacker_name"].notna()) & 
                           (valid_deaths184["attacker_name"] != valid_deaths184["user_name"]) & 
                           (valid_deaths184["attacker_name"] != "world")].copy()

mk184 = kills184.groupby(["attacker_name", "match_round"]).size()
assists184 = valid_deaths184[valid_deaths184["assister_name"].notna()]["assister_name"].value_counts().to_dict()
firstk184 = kills184.sort_values("tick").groupby("match_round").first()["attacker_name"].value_counts().to_dict()

mangemort_p = ['Whrite', 'Pip✿_Nin✿', 'Preda', 'Kalette', 'Draf']
yva_p = ['attaboy', 'PunisheR', 'LeBigJim', 'MrCc_', 'Zedju']

extra_matches.append({
    "match_id": "184",
    "date_match": "2026-10-25 16:55:00",
    "equipe_a": "MANGEMORT",
    "score_a": "13",
    "score_b": "8",
    "equipe_b": "YVAPALACHERCHER",
    "vainqueur": "MANGEMORT",
    "maps_jouees": "de_ancient",
    "ip_serveur": "10.100.100.201:27015"
})

for pl in set(mangemort_p + yva_p):
    k = int((kills184["attacker_name"] == pl).sum())
    d = int((valid_deaths184["user_name"] == pl).sum())
    hs = int(((kills184["attacker_name"] == pl) & (kills184["headshot"] == True)).sum())
    ast = int(assists184.get(pl, 0))
    fk = int(firstk184.get(pl, 0))
    
    p_mk = mk184.get(pl, pd.Series(dtype=int))
    k1 = int((p_mk == 1).sum())
    k2 = int((p_mk == 2).sum())
    k3 = int((p_mk == 3).sum())
    k4 = int((p_mk == 4).sum())
    k5 = int((p_mk == 5).sum())
    
    sid = ""
    s1 = valid_deaths184[valid_deaths184["attacker_name"] == pl]["attacker_steamid"].dropna()
    if not s1.empty:
        sid = to_steam3(s1.iloc[0])
    else:
        s2 = valid_deaths184[valid_deaths184["user_name"] == pl]["user_steamid"].dropna()
        if not s2.empty:
            sid = to_steam3(s2.iloc[0])
            
    team_name = "MANGEMORT" if pl in mangemort_p else "YVAPALACHERCHER"
    extra_player_stats.append({
        "steamid": sid,
        "pseudo": pl,
        "team_name": team_name,
        "kills": k,
        "deaths": d,
        "assists": ast,
        "hs": hs,
        "first_kills": fk,
        "k1": k1, "k2": k2, "k3": k3, "k4": k4, "k5": k5,
        "rounds": 21
    })

# Combine matches
all_matches = sorted(base_matches + extra_matches, key=lambda m: int(m["match_id"]))

# 5. Merge Player Stats
print("[3/5] Agrégation des statistiques joueurs et calcul du HLTV Rating...")
# Create a matching lookup by steamid and pseudo
player_store = dict(base_players)

for ep in extra_player_stats:
    sid = ep["steamid"]
    pseudo = ep["pseudo"]
    
    matched = None
    if sid and sid in player_store:
        matched = player_store[sid]
    else:
        # Match by pseudo
        for p in player_store.values():
            if p["pseudo"].lower().replace(" ", "").replace("_", "") == pseudo.lower().replace(" ", "").replace("_", ""):
                matched = p
                break
                
    if matched:
        matched["matchs_joues"] = str(int(matched["matchs_joues"]) + 1)
        matched["total_rounds"] = str(int(matched["total_rounds"]) + ep["rounds"])
        matched["total_kills"] = str(int(matched["total_kills"]) + ep["kills"])
        matched["total_deaths"] = str(int(matched["total_deaths"]) + ep["deaths"])
        matched["assists"] = str(int(matched["assists"]) + ep["assists"])
        matched["headshots"] = str(int(matched["headshots"]) + ep["hs"])
        matched["first_kills"] = str(int(matched.get("first_kills", 0)) + ep["first_kills"])
        
        matched["frags_1k"] = str(int(matched.get("frags_1k", 0)) + ep["k1"])
        matched["frags_2k"] = str(int(matched.get("frags_2k", 0)) + ep["k2"])
        matched["frags_3k"] = str(int(matched.get("frags_3k", 0)) + ep["k3"])
        matched["frags_4k"] = str(int(matched.get("frags_4k", 0)) + ep["k4"])
        matched["frags_aces"] = str(int(matched.get("frags_aces", 0)) + ep["k5"])
        
        if ep["team_name"] and matched["team_name"] in ["a", "b", "-", ""]:
            matched["team_name"] = ep["team_name"]
    else:
        # New player
        player_store[sid or pseudo] = {
            "pseudo": pseudo,
            "steamid": sid,
            "team_name": ep["team_name"],
            "matchs_joues": "1",
            "total_rounds": str(ep["rounds"]),
            "total_kills": str(ep["kills"]),
            "total_deaths": str(ep["deaths"]),
            "assists": str(ep["assists"]),
            "headshots": str(ep["hs"]),
            "first_kills": str(ep["first_kills"]),
            "points": "0", "bombs_planted": "0", "bombs_defused": "0", "teamkills": "0",
            "frags_1k": str(ep["k1"]), "frags_2k": str(ep["k2"]), "frags_3k": str(ep["k3"]),
            "frags_4k": str(ep["k4"]), "frags_aces": str(ep["k5"])
        }

final_players = []
for p in player_store.values():
    tk = int(p["total_kills"])
    td = int(p["total_deaths"])
    mj = int(p["matchs_joues"])
    rnds = int(p["total_rounds"])
    hs = int(p["headshots"])
    
    if tk <= 0:
        continue
        
    p["diff_kd"] = str(tk - td)
    p["kd_ratio"] = str(round(tk / max(1, td), 2))
    p["hs_percent"] = str(round(hs / max(1, tk) * 100, 1))
    p["kills_per_match"] = str(round(tk / max(1, mj), 1))
    
    hltv = compute_hltv_rating(
        tk, td, rnds,
        int(p.get("frags_1k", 0)), int(p.get("frags_2k", 0)),
        int(p.get("frags_3k", 0)), int(p.get("frags_4k", 0)),
        int(p.get("frags_aces", 0))
    )
    p["hltv_rating"] = str(hltv)
    final_players.append(p)

final_players.sort(key=lambda p: float(p["hltv_rating"]), reverse=True)

# 6. Recompute Team Standings
print("[4/5] Calcul du classement général des équipes...")
teams_dict = {}
for m in all_matches:
    ta = m["equipe_a"]
    tb = m["equipe_b"]
    sa = int(m["score_a"])
    sb = int(m["score_b"])
    
    for tname, tscore, oppscore in [(ta, sa, sb), (tb, sb, sa)]:
        if tname not in teams_dict:
            teams_dict[tname] = {
                "team_name": tname,
                "matchs_joues": 0,
                "victoires": 0,
                "defaites": 0,
                "nuls": 0,
                "rounds_gagnes": 0,
                "rounds_perdus": 0
            }
        t = teams_dict[tname]
        t["matchs_joues"] += 1
        t["rounds_gagnes"] += tscore
        t["rounds_perdus"] += oppscore
        if tscore > oppscore:
            t["victoires"] += 1
        elif tscore < oppscore:
            t["defaites"] += 1
        else:
            t["nuls"] += 1

final_teams = []
for t in teams_dict.values():
    mj = t["matchs_joues"]
    v = t["victoires"]
    diff = t["rounds_gagnes"] - t["rounds_perdus"]
    winrate = round(v / mj * 100, 1) if mj > 0 else 0.0
    final_teams.append({
        "team_name": t["team_name"],
        "matchs_joues": str(mj),
        "victoires": str(v),
        "defaites": str(t["defaites"]),
        "nuls": str(t["nuls"]),
        "winrate_pct": str(winrate),
        "rounds_gagnes": str(t["rounds_gagnes"]),
        "rounds_perdus": str(t["rounds_perdus"]),
        "diff_rounds": str(diff)
    })

final_teams.sort(key=lambda t: (int(t["victoires"]), int(t["diff_rounds"])), reverse=True)

# 7. Summary Metrics
team_games = [int(t["matchs_joues"]) for t in final_teams]
avg_team_games = round(sum(team_games) / len(team_games), 1) if team_games else 0
min_team_games = min(team_games) if team_games else 0
max_team_games = max(team_games) if team_games else 0

player_games = [int(p["matchs_joues"]) for p in final_players]
avg_player_games = round(sum(player_games) / len(player_games), 1) if player_games else 0
min_player_games = min(player_games) if player_games else 0
max_player_games = max(player_games) if player_games else 0

summary = {
    "avg_team_games": avg_team_games,
    "min_team_games": min_team_games,
    "max_team_games": max_team_games,
    "avg_player_games": avg_player_games,
    "min_player_games": min_player_games,
    "max_player_games": max_player_games,
    "total_valid_matches": len(all_matches),
    "total_players": len(final_players),
    "total_teams": len(final_teams)
}

print(f"\nRésumé Global du Tournoi:")
print(f"  Total Matchs Validés : {summary['total_valid_matches']}")
print(f"  Total Équipes : {summary['total_teams']} (Moy: {summary['avg_team_games']} matchs, Min: {summary['min_team_games']}, Max: {summary['max_team_games']})")
print(f"  Total Joueurs : {summary['total_players']} (Moy: {summary['avg_player_games']} matchs, Min: {summary['min_player_games']}, Max: {summary['max_player_games']})")

# 8. Save CSV Files
print("[5/5] Export des fichiers CSV, JSON et Rapport HTML...")
h_players = [
    'pseudo', 'steamid', 'team_name', 'matchs_joues', 'hltv_rating', 'kd_ratio',
    'total_kills', 'total_deaths', 'diff_kd', 'assists', 'headshots', 'hs_percent',
    'kills_per_match', 'total_rounds', 'points', 'bombs_planted', 'bombs_defused', 'teamkills',
    'frags_1k', 'frags_2k', 'frags_3k', 'frags_4k', 'frags_aces', 'first_kills'
]
with open(os.path.join(stats_dir, "csv", "01_classement_general_joueurs.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(h_players)
    for p in final_players:
        w.writerow([p.get(c, '') for c in h_players])

h_teams = ['team_name', 'matchs_joues', 'victoires', 'defaites', 'nuls', 'winrate_pct', 'rounds_gagnes', 'rounds_perdus', 'diff_rounds']
with open(os.path.join(stats_dir, "csv", "02_classement_equipes.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(h_teams)
    for t in final_teams:
        w.writerow([t.get(c, '') for c in h_teams])

h_matchs = ['match_id', 'date_match', 'equipe_a', 'score_a', 'score_b', 'equipe_b', 'vainqueur', 'maps_jouees', 'ip_serveur']
with open(os.path.join(stats_dir, "csv", "03_liste_tous_les_matchs.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(h_matchs)
    for m in all_matches:
        w.writerow([m.get(c, '') for c in h_matchs])

# Save JSON
base_data["summary"] = summary
base_data["matches"] = all_matches
base_data["players"] = final_players
base_data["teams"] = final_teams
base_data["completed_from_demos"] = True
base_data["updated_at"] = datetime.now().isoformat()

with open(os.path.join(stats_dir, "json", "stats_gglan19_complete.json"), "w", encoding="utf-8") as f:
    json.dump(base_data, f, indent=2, ensure_ascii=False)

# 9. Generate HTML Report
def safe_float(v, default=0.0):
    try:
        return float(v) if v is not None and v != '' else default
    except:
        return default

def safe_int(v, default=0):
    try:
        return int(v) if v is not None and v != '' else default
    except:
        return default

top_hltv = sorted(final_players, key=lambda x: safe_float(x.get('hltv_rating')), reverse=True)[:10]
top_kills = sorted(final_players, key=lambda x: safe_int(x.get('total_kills')), reverse=True)[:10]
total_matches = len(all_matches)
total_kills = sum(safe_int(p.get('total_kills')) for p in final_players)
total_aces = sum(safe_int(p.get('frags_aces')) for p in final_players)

html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>GGLan #19 - Rapport Officiel des Statistiques eBot & Démos CS2</title>
    <style>
        :root {{
            --bg: #0f172a;
            --card-bg: #1e293b;
            --border: #334155;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #38bdf8;
            --accent: #f59e0b;
            --success: #10b981;
            --danger: #ef4444;
            --purple: #a855f7;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
        body {{ background-color: var(--bg); color: var(--text); padding: 2rem; line-height: 1.5; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        header {{ text-align: center; margin-bottom: 2.5rem; border-bottom: 1px solid var(--border); padding-bottom: 1.5rem; }}
        header h1 {{ font-size: 2.5rem; font-weight: 800; color: var(--primary); margin-bottom: 0.5rem; letter-spacing: -0.05em; }}
        header p {{ color: var(--text-muted); font-size: 1.1rem; }}
        
        .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.25rem; margin-bottom: 2rem; }}
        .kpi-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); }}
        .kpi-val {{ font-size: 2rem; font-weight: 800; color: var(--text); }}
        .kpi-label {{ color: var(--text-muted); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.25rem; }}
        
        .banner-filter {{ background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 10px; padding: 1rem 1.5rem; margin-bottom: 2rem; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 1rem; font-size: 0.95rem; }}
        .banner-filter strong {{ color: var(--primary); }}

        .section-title {{ font-size: 1.4rem; font-weight: 700; margin-bottom: 1rem; color: var(--text); display: flex; align-items: center; gap: 0.5rem; }}
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 2rem; }}
        @media(max-width: 900px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
        
        .card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; text-align: left; }}
        th {{ background: #0f172a; color: var(--primary); padding: 0.75rem 0.9rem; border-bottom: 2px solid var(--border); position: sticky; top: 0; white-space: nowrap; }}
        td {{ padding: 0.7rem 0.9rem; border-bottom: 1px solid var(--border); }}
        tr:hover td {{ background: rgba(56, 189, 248, 0.04); }}
        
        .rating-badge {{ display: inline-block; padding: 0.2rem 0.5rem; border-radius: 6px; font-weight: 700; font-size: 0.9rem; }}
        .rating-high {{ background: rgba(16, 185, 129, 0.2); color: var(--success); }}
        .rating-mid {{ background: rgba(56, 189, 248, 0.2); color: var(--primary); }}
        .rating-low {{ background: rgba(239, 68, 68, 0.2); color: var(--danger); }}

        .search-box {{ width: 100%; max-width: 350px; padding: 0.6rem 1rem; border-radius: 8px; border: 1px solid var(--border); background: #0f172a; color: var(--text); margin-bottom: 1rem; }}
        .search-box:focus {{ outline: none; border-color: var(--primary); }}
        .table-container {{ max-height: 520px; overflow-y: auto; border: 1px solid var(--border); border-radius: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>GGLan #19 - Statistiques Officielles Consolidées</h1>
            <p>eBot + Démos CS2 / Backups Rounds vérifiés • Rating HLTV 1.0 • 24 & 25 Octobre 2026</p>
        </header>

        <div class="banner-filter">
            <div>
                <strong>🎮 Matchs par Équipe :</strong> Moyenne = <strong>{summary['avg_team_games']}</strong> games (Min: {summary['min_team_games']} • Max: {summary['max_team_games']})
            </div>
            <div>
                <strong>👤 Matchs par Joueur :</strong> Moyenne = <strong>{summary['avg_player_games']}</strong> games (Min: {summary['min_player_games']} • Max: {summary['max_player_games']})
            </div>
            <div>
                <strong>⚙️ Statut Tournoi :</strong> 100% des matchs joués inclus (eBot + Démos/Backups #126, #181, #183, #184)
            </div>
        </div>
        
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-val" style="color: var(--primary);">{total_matches}</div>
                <div class="kpi-label">Matchs Officiels Joués</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-val" style="color: var(--success);">{len(final_players)}</div>
                <div class="kpi-label">Joueurs Qualifiés</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-val" style="color: var(--accent);">{len(final_teams)}</div>
                <div class="kpi-label">Équipes Engagées</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-val">{total_kills}</div>
                <div class="kpi-label">Total Frags (Kills)</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-val" style="color: #ec4899;">{total_aces}</div>
                <div class="kpi-label">Aces (5 Kills / Round)</div>
            </div>
        </div>

        <div class="grid-2">
            <!-- Top HLTV Rating -->
            <div class="card" style="margin-bottom:0;">
                <h2 class="section-title">⭐ Top 10 Rating HLTV 1.0</h2>
                <table>
                    <thead>
                        <tr><th>#</th><th>Pseudo</th><th>Équipe</th><th>Matchs</th><th>K/D</th><th>HS %</th><th>HLTV Rating</th></tr>
                    </thead>
                    <tbody>
    """
for i, p in enumerate(top_hltv, 1):
    r_val = safe_float(p.get('hltv_rating'))
    badge_cls = 'rating-high' if r_val >= 1.2 else ('rating-mid' if r_val >= 1.0 else 'rating-low')
    html += f"""<tr>
        <td><strong>{i}</strong></td>
        <td style="font-weight:600; color:var(--primary);">{p.get('pseudo')}</td>
        <td>{p.get('team_name') or '-'}</td>
        <td>{p.get('matchs_joues')}</td>
        <td>{p.get('kd_ratio')}</td>
        <td>{p.get('hs_percent')}%</td>
        <td><span class="rating-badge {badge_cls}">{r_val:.2f}</span></td>
    </tr>"""

html += """
                </tbody>
            </table>
        </div>

        <!-- Classement Equipes -->
        <div class="card" style="margin-bottom:0;">
            <h2 class="section-title">🥇 Classement des Équipes</h2>
            <table>
                <thead>
                    <tr><th>#</th><th>Équipe</th><th>MJ</th><th>V</th><th>D</th><th>N</th><th>Win %</th><th>Diff</th></tr>
                </thead>
                <tbody>
"""
for i, t in enumerate(final_teams, 1):
    diff = safe_int(t.get('diff_rounds'))
    diff_str = f"+{diff}" if diff > 0 else str(diff)
    html += f"""<tr>
        <td><strong>{i}</strong></td>
        <td style="font-weight:600;">{t.get('team_name')}</td>
        <td>{t.get('matchs_joues')}</td>
        <td style="color:var(--success); font-weight:bold;">{t.get('victoires')}</td>
        <td style="color:var(--danger);">{t.get('defaites')}</td>
        <td style="color:var(--text-muted);">{t.get('nuls')}</td>
        <td>{t.get('winrate_pct')}%</td>
        <td style="color:{'var(--success)' if diff >= 0 else 'var(--danger)'}; font-weight:600;">{diff_str}</td>
    </tr>"""

html += """
                </tbody>
            </table>
        </div>
    </div>

    <!-- Tableau complet de tous les joueurs -->
    <div class="card">
        <h2 class="section-title">👥 Statistiques Complètes des Joueurs (avec Rating HLTV)</h2>
        <input type="text" id="playerSearch" class="search-box" placeholder="Rechercher un joueur ou une équipe..." onkeyup="filterPlayers()">
        <div class="table-container">
            <table id="playersTable">
                <thead>
                    <tr>
                        <th>Pseudo</th><th>Équipe</th><th>Matchs</th><th>HLTV Rating</th><th>K/D</th><th>Kills</th><th>Morts</th>
                        <th>Diff</th><th>Assists</th><th>HS %</th><th>K/M</th><th>1k</th><th>2k</th><th>3k</th><th>4k</th><th>Aces</th><th>First Kills</th>
                    </tr>
                </thead>
                <tbody>
"""
for p in final_players:
    r_val = safe_float(p.get('hltv_rating'))
    badge_cls = 'rating-high' if r_val >= 1.2 else ('rating-mid' if r_val >= 1.0 else 'rating-low')
    html += f"""<tr>
        <td style="font-weight:600; color:var(--primary);">{p.get('pseudo')}</td>
        <td>{p.get('team_name') or '-'}</td>
        <td>{p.get('matchs_joues')}</td>
        <td><span class="rating-badge {badge_cls}">{r_val:.2f}</span></td>
        <td style="font-weight:600; color:{'var(--success)' if safe_float(p.get('kd_ratio')) >= 1.0 else 'var(--danger)'};">{p.get('kd_ratio')}</td>
        <td><strong>{p.get('total_kills')}</strong></td>
        <td>{p.get('total_deaths')}</td>
        <td style="font-weight:600; color:{'var(--success)' if safe_int(p.get('diff_kd')) >= 0 else 'var(--danger)'};">{p.get('diff_kd')}</td>
        <td>{p.get('assists')}</td>
        <td>{p.get('hs_percent')}%</td>
        <td>{p.get('kills_per_match')}</td>
        <td>{p.get('frags_1k')}</td>
        <td>{p.get('frags_2k')}</td>
        <td>{p.get('frags_3k')}</td>
        <td>{p.get('frags_4k')}</td>
        <td style="color:{'#ec4899' if safe_int(p.get('frags_aces')) > 0 else 'inherit'}; font-weight:{'bold' if safe_int(p.get('frags_aces')) > 0 else 'normal'};">{p.get('frags_aces')}</td>
        <td>{p.get('first_kills')}</td>
    </tr>"""

html += """
                </tbody>
            </table>
        </div>
    </div>

    <!-- Tous les Matchs Validés -->
    <div class="card">
        <h2 class="section-title">⚔️ Tous les Matchs Joués du Tournoi (70 Matchs)</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr><th>ID</th><th>Date</th><th>Équipe A</th><th>Score</th><th>Équipe B</th><th>Vainqueur</th><th>Map(s)</th></tr>
                </thead>
                <tbody>
"""
for m in all_matches:
    score_a = safe_int(m.get('score_a'))
    score_b = safe_int(m.get('score_b'))
    html += f"""<tr>
        <td>#{m.get('match_id')}</td>
        <td style="color:var(--text-muted); font-size:0.85rem;">{m.get('date_match')}</td>
        <td style="font-weight:600; text-align:right;">{m.get('equipe_a')}</td>
        <td style="text-align:center; font-weight:800; font-size:1.1rem; min-width:80px;">
            <span style="color:{'var(--success)' if score_a > score_b else ('var(--danger)' if score_a < score_b else 'inherit')}">{score_a}</span>
            -
            <span style="color:{'var(--success)' if score_b > score_a else ('var(--danger)' if score_b < score_a else 'inherit')}">{score_b}</span>
        </td>
        <td style="font-weight:600;">{m.get('equipe_b')}</td>
        <td style="color:var(--accent); font-weight:600;">{m.get('vainqueur')}</td>
        <td>{m.get('maps_jouees') or '-'}</td>
    </tr>"""

html += """
                </tbody>
            </table>
        </div>
    </div>
</div>

<script>
    function filterPlayers() {
        var input = document.getElementById("playerSearch");
        var filter = input.value.toLowerCase();
        var rows = document.getElementById("playersTable").getElementsByTagName("tbody")[0].getElementsByTagName("tr");
        for (var i = 0; i < rows.length; i++) {
            var pseudo = rows[i].cells[0].textContent.toLowerCase();
            var team = rows[i].cells[1].textContent.toLowerCase();
            if (pseudo.indexOf(filter) > -1 || team.indexOf(filter) > -1) {
                rows[i].style.display = "";
            } else {
                rows[i].style.display = "none";
            }
        }
    }
</script>
</body>
</html>
"""

with open(os.path.join(stats_dir, "rapport_stats_gglan19.html"), "w", encoding="utf-8") as f:
    f.write(html)

print("\nTous les livrables (CSV, JSON, Rapport HTML) ont été générés avec succès !")
