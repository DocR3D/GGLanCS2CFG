import os
import sys
import time
import json
import csv
import re
from datetime import datetime
import pandas as pd
import numpy as np
from demoparser2 import DemoParser

sys.stdout.reconfigure(encoding='utf-8')

stats_dir = r"C:\Users\yonne\Desktop\GGLan\GGLan #19\Stats"
demos_dir = r"C:\Users\yonne\Desktop\GGLan\GGLan #19\Demos"

# Load current consolidated data
with open(os.path.join(stats_dir, "json", "stats_gglan19_complete.json"), "r", encoding="utf-8") as f:
    base_data = json.load(f)

# Build SteamID -> Real Team mapping
steam_to_team = {}
for p in base_data["players"]:
    if p.get("team_name") and p["team_name"] not in ["a", "b", "-", ""]:
        steam_to_team[p["steamid"]] = p["team_name"]
        steam_to_team[p["pseudo"]] = p["team_name"]

# Helper to normalize SteamID to [U:1:X]
def to_steam3(sid):
    if not sid: return ""
    s = str(sid).strip()
    if s.startswith("[U:1:"): return s
    try:
        val = int(s)
        if val > 76561197960265728:
            return f"[U:1:{val - 76561197960265728}]"
        return f"[U:1:{val}]"
    except:
        return s

# Win probability lookup (alive_friendly, alive_enemy)
WIN_PROB = {
    (5, 5): 0.50,
    (5, 4): 0.73, (4, 5): 0.27,
    (5, 3): 0.88, (3, 5): 0.12,
    (5, 2): 0.95, (2, 5): 0.05,
    (5, 1): 0.99, (1, 5): 0.01,
    (4, 4): 0.50,
    (4, 3): 0.71, (3, 4): 0.29,
    (4, 2): 0.89, (2, 4): 0.11,
    (4, 1): 0.97, (1, 4): 0.03,
    (3, 3): 0.50,
    (3, 2): 0.75, (2, 3): 0.25,
    (3, 1): 0.95, (1, 3): 0.05,
    (2, 2): 0.50,
    (2, 1): 0.82, (1, 2): 0.18,
    (1, 1): 0.50,
    (1, 0): 1.00, (0, 1): 0.00
}

def get_win_prob(f, e):
    f = max(0, min(5, f))
    e = max(0, min(5, e))
    if f == 0: return 0.0
    if e == 0: return 1.0
    return WIN_PROB.get((f, e), 0.50)

WEAPON_TIER = {
    'glock': 'eco', 'usp_silencer': 'eco', 'hkp2000': 'eco', 'p250': 'eco',
    'cz75a': 'eco', 'tec9': 'eco', 'fiveseven': 'eco', 'deagle': 'eco_heavy',
    'dualberettas': 'eco', 'revolver': 'eco_heavy',
    'mac10': 'force', 'mp9': 'force', 'mp7': 'force', 'mp5sd': 'force',
    'ump45': 'force', 'bizon': 'force', 'p90': 'force',
    'nova': 'force', 'xm1014': 'force', 'mag7': 'force', 'sawedoff': 'force',
    'galilar': 'mid', 'famas': 'mid', 'ssg08': 'mid',
    'ak47': 'rifle', 'm4a1_silencer': 'rifle', 'm4a1': 'rifle', 'aug': 'rifle', 'sg556': 'rifle',
    'awp': 'awp', 'g3sg1': 'rifle', 'scar20': 'rifle', 'm249': 'rifle', 'negev': 'mid'
}

def get_duel_multiplier(k_w, v_w):
    k_tier = WEAPON_TIER.get(str(k_w).lower(), 'mid')
    v_tier = WEAPON_TIER.get(str(v_w).lower(), 'mid')
    if k_tier in ['eco', 'eco_heavy'] and v_tier in ['rifle', 'awp']:
        return 1.25
    if k_tier in ['rifle', 'awp'] and v_tier == 'eco':
        return 0.75
    return 1.00

# Map match IDs to demos
demo_files = os.listdir(demos_dir)
match_demos = []
for m in base_data["matches"]:
    mid = str(m["match_id"])
    cands = [f for f in demo_files if f.startswith(mid + "_") and f.endswith(".dem")]
    if not cands and mid == "184":
        cands = [f for f in demo_files if "1555-de_ancient" in f and "YVAPALACHERCHER" in f]
    if cands:
        cands.sort(key=lambda x: os.path.getsize(os.path.join(demos_dir, x)), reverse=True)
        match_demos.append((m, os.path.join(demos_dir, cands[0])))

print(f"=== INITIALISATION DE GGRATING 3.0 (HLTV 3.0 CS2) ===")
print(f"Nombre de matchs vérifiés à parser : {len(match_demos)} démos\n")

# Global aggregation dictionary per player (keyed by steam3 or pseudo)
player_totals = {}

def get_or_create_player(sid, pseudo, team=""):
    key = sid if sid else pseudo
    if key not in player_totals:
        # Fallback team lookup
        real_team = team or steam_to_team.get(sid) or steam_to_team.get(pseudo) or "-"
        player_totals[key] = {
            "key": key,
            "steamid": sid,
            "pseudo": pseudo,
            "team_name": real_team,
            "matches_played": 0,
            "rounds_played": 0,
            "kills": 0,
            "deaths": 0,
            "assists": 0,
            "damage_raw": 0,
            "damage_eco": 0.0,
            "kills_eco": 0.0,
            "kast_rounds": 0,
            "survived_rounds": 0,
            "round_swing_sum": 0.0,
            "first_kills": 0,
            "first_deaths": 0,
            "k1": 0, "k2": 0, "k3": 0, "k4": 0, "k5": 0,
            "headshots": 0
        }
    return player_totals[key]

# Function to parse one demo and aggregate
def process_demo(match_info, demo_path, match_idx, total_count):
    mid = match_info["match_id"]
    map_name = match_info["maps_jouees"]
    ta = match_info["equipe_a"]
    tb = match_info["equipe_b"]
    
    t0 = time.time()
    try:
        parser = DemoParser(demo_path)
        rstarts = parser.parse_event("round_start").sort_values("tick").reset_index(drop=True)
        rends = parser.parse_event("round_end").sort_values("tick").reset_index(drop=True)
        rends = rends[rends["winner"].isin(["CT", "T"])].reset_index(drop=True)
        
        raw_rounds = []
        for i in range(len(rends)):
            r_end_tick = rends.iloc[i]["tick"]
            starts_before = rstarts[rstarts["tick"] < r_end_tick]
            r_start_tick = starts_before.iloc[-1]["tick"] if not starts_before.empty else (rends.iloc[i-1]["tick"] if i > 0 else 0)
            raw_rounds.append((r_start_tick, r_end_tick, rends.iloc[i]["winner"]))
            
        # Drop knife round if any
        if len(raw_rounds) > 1 and (raw_rounds[0][1] - raw_rounds[0][0] < 3000 or raw_rounds[0][1] < 5000):
            raw_rounds = raw_rounds[1:]
            
        if not raw_rounds:
            print(f"[{match_idx}/{total_count}] Match #{mid} ({map_name}) : Aucun round valide.")
            return
            
        round_intervals = [(idx + 1, s, e, w) for idx, (s, e, w) in enumerate(raw_rounds)]
        total_rnds = len(round_intervals)
        
        # Player teams
        sample_tick = raw_rounds[0][0] + 500
        try:
            ticks_df = parser.parse_ticks(["name", "team_num"], ticks=[sample_tick])
            t_players = ticks_df[ticks_df["team_num"] == 2]["name"].unique().tolist()
            ct_players = ticks_df[ticks_df["team_num"] == 3]["name"].unique().tolist()
        except:
            t_players, ct_players = [], []
            
        deaths_df = parser.parse_event("player_death")
        hurts_df = parser.parse_event("player_hurt")
        
        def assign_r(t):
            for r_num, s_tick, e_tick, _ in round_intervals:
                if s_tick <= t <= e_tick:
                    return r_num
            return None
            
        deaths_df["match_round"] = deaths_df["tick"].apply(assign_r)
        hurts_df["match_round"] = hurts_df["tick"].apply(assign_r)
        
        deaths = deaths_df[deaths_df["match_round"].notna()].sort_values("tick").reset_index(drop=True)
        hurts = hurts_df[hurts_df["match_round"].notna()].sort_values("tick").reset_index(drop=True)
        
        kills = deaths[
            (deaths["attacker_name"].notna()) & 
            (deaths["attacker_name"] != deaths["user_name"]) & 
            (deaths["attacker_name"] != "world")
        ].copy()
        
        # Collect match players
        all_match_players = set(kills["attacker_name"]).union(set(deaths["user_name"]))
        all_match_players.discard("world")
        all_match_players.discard(None)
        
        # Build steamid lookup for players in this match
        p_steam_lookup = {}
        for _, row in deaths.iterrows():
            att = row["attacker_name"]
            ast = row["attacker_steamid"]
            if att and ast: p_steam_lookup[att] = to_steam3(ast)
            vic = row["user_name"]
            vst = row["user_steamid"]
            if vic and vst: p_steam_lookup[vic] = to_steam3(vst)
            
        # Player team mapping
        p_side_map = {}
        for p in all_match_players:
            if p in ct_players: p_side_map[p] = "A"
            elif p in t_players: p_side_map[p] = "B"
            else: p_side_map[p] = "A"
            
        # Per match player records
        match_p_stats = {}
        for p in all_match_players:
            sid = p_steam_lookup.get(p, "")
            team_guess = ta if p_side_map.get(p) == "A" else tb
            rec = get_or_create_player(sid, p, team_guess)
            rec["matches_played"] += 1
            rec["rounds_played"] += total_rnds
            match_p_stats[p] = {
                "rec": rec,
                "kills": 0, "deaths": 0, "assists": 0,
                "dmg_raw": 0, "dmg_eco": 0.0, "kills_eco": 0.0,
                "kast_rnds": 0, "surv_rnds": 0, "swing_sum": 0.0,
                "fk": 0, "fd": 0, "hs": 0,
                "k1": 0, "k2": 0, "k3": 0, "k4": 0, "k5": 0
            }
            
        TRADE_TICKS = 320 # 5s
        
        # Process each round
        for r_num, s_tick, e_tick, winner_side in round_intervals:
            r_deaths = deaths[deaths["match_round"] == r_num].sort_values("tick").reset_index(drop=True)
            r_hurts = hurts[hurts["match_round"] == r_num].sort_values("tick").reset_index(drop=True)
            r_kills = kills[kills["match_round"] == r_num].sort_values("tick").reset_index(drop=True)
            
            alive_a = set([p for p in all_match_players if p_side_map.get(p) == "A"])
            alive_b = set([p for p in all_match_players if p_side_map.get(p) == "B"])
            
            # Damage calculation capped at 100 per victim
            victim_dmg = {}
            dmg_by_att = {}
            for _, h in r_hurts.iterrows():
                att = h["attacker_name"]
                vic = h["user_name"]
                dmg = h["dmg_health"]
                if not att or att == vic or att == "world" or att not in match_p_stats:
                    continue
                taken = victim_dmg.get(vic, 0)
                real_d = min(dmg, max(0, 100 - taken))
                victim_dmg[vic] = taken + real_d
                
                w_mult = get_duel_multiplier(h["weapon"], "rifle")
                if att not in dmg_by_att:
                    dmg_by_att[att] = {"raw": 0, "eco": 0.0, "to_vic": {}}
                dmg_by_att[att]["raw"] += real_d
                dmg_by_att[att]["eco"] += real_d * w_mult
                dmg_by_att[att]["to_vic"][vic] = dmg_by_att[att]["to_vic"].get(vic, 0) + real_d
                
            for att, d_val in dmg_by_att.items():
                if att in match_p_stats:
                    match_p_stats[att]["dmg_raw"] += d_val["raw"]
                    match_p_stats[att]["dmg_eco"] += d_val["eco"]
                    
            dead_in_round = set(r_deaths["user_name"].unique())
            for att, d_val in dmg_by_att.items():
                for vic, d_amt in d_val["to_vic"].items():
                    if vic in dead_in_round and d_amt >= 40:
                        k_vic = r_kills[r_kills["user_name"] == vic]
                        if k_vic.empty or k_vic.iloc[0]["attacker_name"] != att:
                            match_p_stats[att]["assists"] += 1
                            
            # Traded deaths
            traded_deaths = set()
            for idx_k, k_row in r_deaths.iterrows():
                vic = k_row["user_name"]
                killer = k_row["attacker_name"]
                k_tick = k_row["tick"]
                vic_side = p_side_map.get(vic)
                if killer and killer != "world" and killer != vic:
                    subseq = r_deaths[(r_deaths["tick"] > k_tick) & (r_deaths["tick"] <= k_tick + TRADE_TICKS)]
                    for _, s_row in subseq.iterrows():
                        if s_row["user_name"] == killer:
                            trader = s_row["attacker_name"]
                            if trader and p_side_map.get(trader) == vic_side:
                                traded_deaths.add(vic)
                                break
                                
            # Opening duel
            if not r_kills.empty:
                fk_att = r_kills.iloc[0]["attacker_name"]
                fk_vic = r_kills.iloc[0]["user_name"]
                if fk_att in match_p_stats: match_p_stats[fk_att]["fk"] += 1
                if fk_vic in match_p_stats: match_p_stats[fk_vic]["fd"] += 1
                
            # Round swing & kill events
            round_swing = {p: 0.0 for p in all_match_players}
            round_kills = {p: 0 for p in all_match_players}
            
            for _, k_row in r_deaths.iterrows():
                killer = k_row["attacker_name"]
                vic = k_row["user_name"]
                vic_side = p_side_map.get(vic)
                killer_side = p_side_map.get(killer)
                
                cnt_a = len(alive_a)
                cnt_b = len(alive_b)
                p_a_before = get_win_prob(cnt_a, cnt_b)
                
                if vic in alive_a: alive_a.remove(vic)
                if vic in alive_b: alive_b.remove(vic)
                
                cnt_a_after = len(alive_a)
                cnt_b_after = len(alive_b)
                p_a_after = get_win_prob(cnt_a_after, cnt_b_after)
                
                delta_a = p_a_after - p_a_before
                delta_b = -delta_a
                
                if killer and killer in match_p_stats and killer_side:
                    d_k = delta_a if killer_side == "A" else delta_b
                    w_mult = get_duel_multiplier(k_row.get("weapon"), "rifle")
                    round_swing[killer] += d_k * w_mult
                    match_p_stats[killer]["kills"] += 1
                    match_p_stats[killer]["kills_eco"] += 1.0 * w_mult
                    round_kills[killer] += 1
                    if k_row.get("headshot") == True:
                        match_p_stats[killer]["hs"] += 1
                        
                if vic and vic in match_p_stats and vic_side:
                    d_v = delta_a if vic_side == "A" else delta_b
                    round_swing[vic] += d_v
                    match_p_stats[vic]["deaths"] += 1
                    
            for p, k_cnt in round_kills.items():
                if k_cnt == 1: match_p_stats[p]["k1"] += 1
                elif k_cnt == 2: match_p_stats[p]["k2"] += 1
                elif k_cnt == 3: match_p_stats[p]["k3"] += 1
                elif k_cnt == 4: match_p_stats[p]["k4"] += 1
                elif k_cnt >= 5: match_p_stats[p]["k5"] += 1
                
            survivors = alive_a.union(alive_b)
            for p in all_match_players:
                has_k = round_kills.get(p, 0) > 0
                has_a = any(d_val.get("to_vic", {}).get(v, 0) >= 40 for v in dead_in_round) if p in dmg_by_att else False
                has_s = p in survivors
                has_t = p in traded_deaths
                
                if has_s: match_p_stats[p]["surv_rnds"] += 1
                if has_k or has_a or has_s or has_t:
                    match_p_stats[p]["kast_rnds"] += 1
                match_p_stats[p]["swing_sum"] += round_swing.get(p, 0.0)
                
        # Merge match stats into global records
        for p, s in match_p_stats.items():
            rec = s["rec"]
            rec["kills"] += s["kills"]
            rec["deaths"] += s["deaths"]
            rec["assists"] += s["assists"]
            rec["damage_raw"] += s["dmg_raw"]
            rec["damage_eco"] += s["dmg_eco"]
            rec["kills_eco"] += s["kills_eco"]
            rec["kast_rounds"] += s["kast_rnds"]
            rec["survived_rounds"] += s["surv_rnds"]
            rec["round_swing_sum"] += s["swing_sum"]
            rec["first_kills"] += s["fk"]
            rec["first_deaths"] += s["fd"]
            rec["headshots"] += s["hs"]
            rec["k1"] += s["k1"]
            rec["k2"] += s["k2"]
            rec["k3"] += s["k3"]
            rec["k4"] += s["k4"]
            rec["k5"] += s["k5"]
            
        elapsed = time.time() - t0
        print(f"[{match_idx:02d}/{total_count}] Match #{mid:<3} ({map_name:<10}) : {ta} vs {tb} ({total_rnds} rounds) [{elapsed:.2f}s]")
        
    except Exception as e:
        print(f"[{match_idx:02d}/{total_count}] Erreur sur Match #{mid} : {e}")

# Run parsing on all 70 demos
t_start = time.time()
for idx, (m_info, d_path) in enumerate(match_demos, 1):
    process_demo(m_info, d_path, idx, len(match_demos))

t_end = time.time()
print(f"\nParsing de 100% des démos terminé en {t_end - t_start:.1f} secondes !\n")

# Calculate overall rates
player_list = list(player_totals.values())
# Filter players with at least 1 kill or 10 rounds
player_list = [p for p in player_list if p["rounds_played"] >= 10 and p["kills"] > 0]

for p in player_list:
    r = max(1, p["rounds_played"])
    p["kpr"] = p["kills"] / r
    p["e_kpr"] = p["kills_eco"] / r
    p["dpr"] = p["deaths"] / r
    p["adr"] = p["damage_raw"] / r
    p["e_adr"] = p["damage_eco"] / r
    p["kast_pct"] = (p["kast_rounds"] / r) * 100.0
    p["surv_pct"] = (p["survived_rounds"] / r) * 100.0
    p["swing_per_round"] = p["round_swing_sum"] / r
    p["mk_score"] = (p["k1"] + 4*p["k2"] + 9*p["k3"] + 16*p["k4"] + 25*p["k5"]) / r
    p["kd_ratio"] = round(p["kills"] / max(1, p["deaths"]), 2)
    p["hs_pct"] = round(p["headshots"] / max(1, p["kills"]) * 100.0, 1)

# Compute tournament baselines
mean_ekpr = np.mean([p["e_kpr"] for p in player_list])
mean_eadr = np.mean([p["e_adr"] for p in player_list])
mean_kast = np.mean([p["kast_pct"] for p in player_list])
mean_surv = np.mean([p["surv_pct"] for p in player_list])
mean_mk = np.mean([p["mk_score"] for p in player_list])
std_swing = np.std([p["swing_per_round"] for p in player_list]) or 0.04

print("=== MOYENNES DU TOURNOI (BASELINES GGRATING) ===")
print(f"  Moyenne eKPR : {mean_ekpr:.3f}")
print(f"  Moyenne eADR : {mean_eadr:.1f}")
print(f"  Moyenne KAST : {mean_kast:.1f}%")
print(f"  Moyenne Survie : {mean_surv:.1f}%")
print(f"  Moyenne Multi-Kills : {mean_mk:.3f}")
print(f"  Écart-type Swing : {std_swing*100:.2f}%\n")

# Calculate GGRating 3.0 and HLTV 1.0 for each player
for p in player_list:
    r = max(1, p["rounds_played"])
    # Sub-ratings normalized to tournament baselines
    s_kpr = p["e_kpr"] / mean_ekpr
    s_adr = p["e_adr"] / mean_eadr
    s_kast = p["kast_pct"] / mean_kast
    s_surv = p["surv_pct"] / mean_surv
    s_mk = p["mk_score"] / mean_mk
    s_swing = (p["swing_per_round"] / std_swing) * 0.20
    
    # GGRating 3.0 Composite
    # Weights: eKPR: 25%, eADR: 25%, eKAST: 20%, Surv: 10%, MK: 8%, Swing: 12%
    raw_ggrating = (
        0.25 * s_kpr +
        0.25 * s_adr +
        0.20 * s_kast +
        0.10 * s_surv +
        0.08 * s_mk +
        0.12 * (1.0 + s_swing)
    )
    p["ggrating"] = round(raw_ggrating, 2)
    
    # HLTV 1.0 standard formula
    k_r = (p["kills"] / r) / 0.679
    s_r = (max(0, r - p["deaths"]) / r) / 0.317
    mk_r = p["mk_score"] / 1.207
    p["hltv1"] = round((k_r + 0.7 * s_r + mk_r) / 2.7, 2)

# Sort by GGRating descending
player_list.sort(key=lambda x: x["ggrating"], reverse=True)

print("=== TOP 15 GGRATING 3.0 (HLTV 3.0 CS2) ===")
print(f"{'#':<3} | {'Pseudo':<15} | {'Équipe':<22} | {'MJ':<2} | {'GGRating':<8} | {'HLTV 1.0':<8} | {'ADR':<5} | {'KAST%':<6} | {'Swing/R':<7} | {'K/D':<4}")
print("-" * 105)
for i, p in enumerate(player_list[:15], 1):
    sw_str = f"{p['swing_per_round']*100:+.1f}%"
    print(f"{i:<3} | {p['pseudo']:<15} | {p['team_name']:<22} | {p['matches_played']:<2} | {p['ggrating']:<8.2f} | {p['hltv1']:<8.2f} | {p['adr']:<5.1f} | {p['kast_pct']:<5.1f}% | {sw_str:<7} | {p['kd_ratio']:<4.2f}")

# Save CSV
h_out = [
    'pseudo', 'steamid', 'team_name', 'matchs_joues', 'total_rounds',
    'ggrating_3_0', 'hltv_rating_1_0', 'kd_ratio', 'adr',
    'kast_percent', 'round_swing_percent', 'opening_duel_kd',
    'total_kills', 'total_deaths', 'diff_kd', 'assists', 'headshots', 'hs_percent',
    'kills_per_round', 'survived_percent',
    'frags_1k', 'frags_2k', 'frags_3k', 'frags_4k', 'frags_aces'
]

rows_out = []
for p in player_list:
    rows_out.append([
        p['pseudo'], p['steamid'], p['team_name'], p['matches_played'], p['rounds_played'],
        f"{p['ggrating']:.2f}", f"{p['hltv1']:.2f}", f"{p['kd_ratio']:.2f}", f"{p['adr']:.1f}",
        f"{p['kast_pct']:.1f}%", f"{p['swing_per_round']*100:+.1f}%", f"{p['first_kills']}/{p['first_deaths']}",
        p['kills'], p['deaths'], p['kills'] - p['deaths'], p['assists'], p['headshots'], f"{p['hs_pct']:.1f}%",
        f"{p['kpr']:.2f}", f"{p['surv_pct']:.1f}%",
        p['k1'], p['k2'], p['k3'], p['k4'], p['k5']
    ])

csv_path = os.path.join(stats_dir, "csv", "01_classement_general_joueurs_ggrating.csv")
with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(h_out)
    w.writerows(rows_out)

print(f"\nFichier CSV généré : {csv_path}")

# Save JSON
json_path = os.path.join(stats_dir, "json", "stats_gglan19_ggrating.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump({
        "metadata": {
            "title": "GGLan #19 - Classement Officiel GGRating 3.0",
            "model": "HLTV Rating 3.0 Architecture",
            "pillars": ["eKPR (25%)", "eADR (25%)", "eKAST (20%)", "Survival (10%)", "Multi-Kills (8%)", "Round Swing (12%)"],
            "total_matches_parsed": len(match_demos),
            "generated_at": datetime.now().isoformat()
        },
        "baselines": {
            "mean_ekpr": round(float(mean_ekpr), 3),
            "mean_eadr": round(float(mean_eadr), 1),
            "mean_kast": round(float(mean_kast), 1),
            "mean_surv": round(float(mean_surv), 1),
            "std_swing": round(float(std_swing), 3)
        },
        "players": [dict(p) for p in player_list]
    }, f, indent=2, ensure_ascii=False)

print(f"Fichier JSON généré : {json_path}")
