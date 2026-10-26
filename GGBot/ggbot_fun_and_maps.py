import os
import sys
import time
import json
import csv
import pandas as pd
import numpy as np
from demoparser2 import DemoParser

sys.stdout.reconfigure(encoding='utf-8')

stats_dir = r"C:\Users\yonne\Desktop\GGLan\GGLan #19\Stats"
demos_dir = r"C:\Users\yonne\Desktop\GGLan\GGLan #19\Demos"

with open(os.path.join(stats_dir, "json", "stats_gglan19_complete.json"), "r", encoding="utf-8") as f:
    match_data = json.load(f)

demo_files = os.listdir(demos_dir)
match_demos = []
for m in match_data["matches"]:
    mid = str(m["match_id"])
    cands = [f for f in demo_files if f.startswith(mid + "_") and f.endswith(".dem")]
    if not cands and mid == "184":
        cands = [f for f in demo_files if "1555-de_ancient" in f and "YVAPALACHERCHER" in f]
    if cands:
        cands.sort(key=lambda x: os.path.getsize(os.path.join(demos_dir, x)), reverse=True)
        match_demos.append((m, os.path.join(demos_dir, cands[0])))

print(f"=== EXTRACTION DES STATISTIQUES PAR MAPS, EQUIPES ET FUN (70 DEMOS) ===")

# Data structures
map_stats = {}
team_side_stats = {}
fun_stats = {
    "chicken_kills": {},      # player -> count
    "chicken_weapons": {},    # weapon -> count
    "knife_kills": [],        # list of {killer, victim, weapon, map, match_id}
    "taser_kills": [],        # list of {killer, victim, map, match_id}
    "bomb_deaths": {},        # player -> count
    "smoke_kills": {},        # player -> count
    "noscope_kills": {},      # player -> count
    "blind_kills": {},        # player -> count
    "wallbang_kills": {},     # player -> count (penetrated > 0)
    "suicides": {},           # player -> count
    "max_distance": {"dist": 0, "killer": "", "victim": "", "weapon": "", "map": "", "match_id": ""},
    "nemesis_pairs": {}       # (killer, victim) -> count
}

t0 = time.time()

for idx, (m, demo_path) in enumerate(match_demos, 1):
    mid = str(m["match_id"])
    map_raw = m["maps_jouees"]
    ta = m["equipe_a"]
    tb = m["equipe_b"]
    
    try:
        parser = DemoParser(demo_path)
        
        # Rounds
        rstarts = parser.parse_event("round_start").sort_values("tick").reset_index(drop=True)
        rends = parser.parse_event("round_end").sort_values("tick").reset_index(drop=True)
        rends = rends[rends["winner"].isin(["CT", "T"])].reset_index(drop=True)
        
        raw_rounds = []
        for i in range(len(rends)):
            r_end_tick = rends.iloc[i]["tick"]
            starts_before = rstarts[rstarts["tick"] < r_end_tick]
            r_start_tick = starts_before.iloc[-1]["tick"] if not starts_before.empty else (rends.iloc[i-1]["tick"] if i > 0 else 0)
            raw_rounds.append((r_start_tick, r_end_tick, rends.iloc[i]["winner"]))
            
        if len(raw_rounds) > 1 and (raw_rounds[0][1] - raw_rounds[0][0] < 3000 or raw_rounds[0][1] < 5000):
            raw_rounds = raw_rounds[1:]
            
        if not raw_rounds:
            continue
            
        round_intervals = [(r_idx + 1, s, e, w) for r_idx, (s, e, w) in enumerate(raw_rounds)]
        
        # Header for map
        header = parser.parse_header()
        map_name = header.get("map_name") or map_raw
        
        # Accumulate map stats
        if map_name not in map_stats:
            map_stats[map_name] = {
                "map_name": map_name,
                "matches_played": 0,
                "total_rounds": 0,
                "ct_rounds_won": 0,
                "t_rounds_won": 0,
                "overtimes_count": 0,
                "bomb_plants": 0,
                "bomb_defuses": 0,
                "bomb_explosions": 0
            }
        ms = map_stats[map_name]
        ms["matches_played"] += 1
        ms["total_rounds"] += len(round_intervals)
        
        for _, _, _, w in round_intervals:
            if w == "CT": ms["ct_rounds_won"] += 1
            elif w == "T": ms["t_rounds_won"] += 1
            
        if len(round_intervals) > 24:
            ms["overtimes_count"] += 1
            
        # Parse deaths
        deaths_df = parser.parse_event("player_death")
        
        def assign_r(t):
            for r_num, s_tick, e_tick, _ in round_intervals:
                if s_tick <= t <= e_tick:
                    return r_num
            return None
            
        deaths_df["match_round"] = deaths_df["tick"].apply(assign_r)
        v_deaths = deaths_df[deaths_df["match_round"].notna()].copy()
        
        # Player teams
        sample_tick = raw_rounds[0][0] + 500
        try:
            ticks_df = parser.parse_ticks(["name", "team_num"], ticks=[sample_tick])
            t_players = ticks_df[ticks_df["team_num"] == 2]["name"].unique().tolist()
            ct_players = ticks_df[ticks_df["team_num"] == 3]["name"].unique().tolist()
        except:
            t_players, ct_players = [], []
            
        for _, d in v_deaths.iterrows():
            killer = d.get("attacker_name")
            vic = d.get("user_name")
            wep = str(d.get("weapon") or "").lower()
            wep_orig = str(d.get("weapon") or "")
            is_hs = d.get("headshot") == True
            is_smoke = d.get("thrusmoke") == True
            is_noscope = d.get("noscope") == True
            is_blind = d.get("attackerblind") == True
            pen = int(d.get("penetrated") or 0)
            dist = float(d.get("distance") or 0.0)
            
            # Bomb death
            if wep == "planted_c4" and vic:
                fun_stats["bomb_deaths"][vic] = fun_stats["bomb_deaths"].get(vic, 0) + 1
                
            # Suicide (non bomb)
            if (killer == vic or killer == "world") and wep != "planted_c4" and vic:
                fun_stats["suicides"][vic] = fun_stats["suicides"].get(vic, 0) + 1
                
            # Real kills by players
            if killer and vic and killer != vic and killer != "world":
                # Knife kill
                if "knife" in wep or "bayonet" in wep:
                    fun_stats["knife_kills"].append({
                        "killer": killer, "victim": vic, "weapon": wep_orig,
                        "map": map_name, "match_id": mid
                    })
                # Taser kill
                if wep == "taser":
                    fun_stats["taser_kills"].append({
                        "killer": killer, "victim": vic,
                        "map": map_name, "match_id": mid
                    })
                # Smoke kill
                if is_smoke:
                    fun_stats["smoke_kills"][killer] = fun_stats["smoke_kills"].get(killer, 0) + 1
                # Noscope kill
                if is_noscope:
                    fun_stats["noscope_kills"][killer] = fun_stats["noscope_kills"].get(killer, 0) + 1
                # Blind kill
                if is_blind:
                    fun_stats["blind_kills"][killer] = fun_stats["blind_kills"].get(killer, 0) + 1
                # Wallbang kill
                if pen > 0:
                    fun_stats["wallbang_kills"][killer] = fun_stats["wallbang_kills"].get(killer, 0) + 1
                # Distance max
                if dist > fun_stats["max_distance"]["dist"]:
                    fun_stats["max_distance"] = {
                        "dist": round(dist, 1),
                        "killer": killer, "victim": vic, "weapon": wep_orig,
                        "map": map_name, "match_id": mid
                    }
                # Nemesis
                pair = (killer, vic)
                fun_stats["nemesis_pairs"][pair] = fun_stats["nemesis_pairs"].get(pair, 0) + 1

        # Check chickens in other_death
        try:
            od = parser.parse_event("other_death")
            if not od.empty and "othertype" in od.columns:
                chickens = od[od["othertype"] == "chicken"]
                for _, ch in chickens.iterrows():
                    c_att = ch.get("attacker_name")
                    c_wep = str(ch.get("weapon") or "unknown")
                    if c_att and c_att != "world":
                        fun_stats["chicken_kills"][c_att] = fun_stats["chicken_kills"].get(c_att, 0) + 1
                        fun_stats["chicken_weapons"][c_wep] = fun_stats["chicken_weapons"].get(c_wep, 0) + 1
        except:
            pass

        # Bomb plants & defuses from round_end
        for _, _, _, r_w in round_intervals:
            pass

    except Exception as e:
        print(f"[{idx:02d}/70] Erreur Match #{mid} : {e}")

    if idx % 10 == 0 or idx == len(match_demos):
        print(f"[{idx:02d}/70] Démos analysées... ({time.time() - t0:.1f}s)")

t_total = time.time() - t0
print(f"\nExtraction terminée en {t_total:.1f} secondes !")

# Process map statistics
map_list = []
for m_name, m_info in map_stats.items():
    tot = max(1, m_info["total_rounds"])
    ct_w = m_info["ct_rounds_won"]
    t_w = m_info["t_rounds_won"]
    ct_pct = round(ct_w / tot * 100, 1)
    t_pct = round(t_w / tot * 100, 1)
    avg_rnds = round(tot / max(1, m_info["matches_played"]), 1)
    map_list.append({
        "map_name": m_name,
        "matches_played": m_info["matches_played"],
        "total_rounds": tot,
        "avg_rounds": avg_rnds,
        "ct_wins": ct_w,
        "t_wins": t_w,
        "ct_win_pct": ct_pct,
        "t_win_pct": t_pct,
        "overtimes": m_info["overtimes_count"],
        "bias": "Équilibré" if abs(ct_pct - 50) <= 2 else ("Avantage CT" if ct_pct > 50 else "Avantage T")
    })

map_list.sort(key=lambda x: x["matches_played"], reverse=True)

# Top Fun Categories
top_chickens = sorted(fun_stats["chicken_kills"].items(), key=lambda x: x[1], reverse=True)[:10]
top_bomb_deaths = sorted(fun_stats["bomb_deaths"].items(), key=lambda x: x[1], reverse=True)[:10]
top_smoke = sorted(fun_stats["smoke_kills"].items(), key=lambda x: x[1], reverse=True)[:10]
top_noscope = sorted(fun_stats["noscope_kills"].items(), key=lambda x: x[1], reverse=True)[:10]
top_blind = sorted(fun_stats["blind_kills"].items(), key=lambda x: x[1], reverse=True)[:10]
top_wallbang = sorted(fun_stats["wallbang_kills"].items(), key=lambda x: x[1], reverse=True)[:10]
top_suicides = sorted(fun_stats["suicides"].items(), key=lambda x: x[1], reverse=True)[:10]
top_nemesis = sorted(fun_stats["nemesis_pairs"].items(), key=lambda x: x[1], reverse=True)[:10]
knife_kills = fun_stats["knife_kills"]
taser_kills = fun_stats["taser_kills"]

print("\n=== 🗺️ STATISTIQUES DES MAPS CS2 ===")
print(f"{'Map':<15} | {'Matchs':<6} | {'Rounds':<6} | {'Moy/Match':<9} | {'CT Win%':<8} | {'T Win%':<8} | {'Tendance':<12}")
print("-" * 75)
for m in map_list:
    print(f"{m['map_name']:<15} | {m['matches_played']:<6} | {m['total_rounds']:<6} | {m['avg_rounds']:<9.1f} | {m['ct_win_pct']:<7.1f}% | {m['t_win_pct']:<7.1f}% | {m['bias']}")

print("\n=== 🐔 TOP 5 BOUCHERS DE POULES ===")
for p, c in top_chickens[:5]:
    print(f"  {p:<20} : {c} poules massacrées")

print("\n=== 🔪 KILLS AU COUTEAU ===")
print(f"Total : {len(knife_kills)} cuts réussis !")
for k in knife_kills[:8]:
    print(f"  {k['killer']} a cutté {k['victim']} ({k['weapon']}) sur {k['map']} (Match #{k['match_id']})")

print("\n=== ⚡ KILLS AU TASER (ZEUS x27) ===")
print(f"Total : {len(taser_kills)} zeus !")
for z in taser_kills:
    print(f"  {z['killer']} a électrocuté {z['victim']} sur {z['map']} (Match #{z['match_id']})")

print("\n=== 💣 TOP 5 MORTS DE L'EXPLOSION DU C4 (KAMIKAZES) ===")
for p, c in top_bomb_deaths[:5]:
    print(f"  {p:<20} : {c} fois explosé par la bombe")

print("\n=== 💨 TOP 5 SMOKE HACKERS (KILLS A TRAVERS LA SMOKE) ===")
for p, c in top_smoke[:5]:
    print(f"  {p:<20} : {c} kills à travers la fumée")

print("\n=== 🎯 TOP 5 NO-SCOPE SNIPER ===")
for p, c in top_noscope[:5]:
    print(f"  {p:<20} : {c} no-scopes")

print("\n=== 🕶️ TOP 5 RAY CHARLES (KILLS TOTALEMENT AVEUGLE) ===")
for p, c in top_blind[:5]:
    print(f"  {p:<20} : {c} kills en étant flashé")

print("\n=== 🏹 RECORD DU TIR LE PLUS LOIN ===")
md = fun_stats["max_distance"]
print(f"  {md['dist']} mètres par {md['killer']} sur {md['victim']} ({md['weapon']}) sur {md['map']} (Match #{md['match_id']})")

print("\n=== 🥊 TOP 5 PIRES NEMESIS (DUELS UNILATERAUX) ===")
for (k, v), c in top_nemesis[:5]:
    print(f"  {k} a tué {v} {c} fois !")

# Save fun stats to JSON
out_fun_json = os.path.join(stats_dir, "json", "stats_gglan19_fun_and_maps.json")
with open(out_fun_json, "w", encoding="utf-8") as f:
    json.dump({
        "maps": map_list,
        "fun_awards": {
            "top_chickens": [{"pseudo": p, "count": c} for p, c in top_chickens],
            "knife_kills": knife_kills,
            "taser_kills": taser_kills,
            "top_bomb_deaths": [{"pseudo": p, "count": c} for p, c in top_bomb_deaths],
            "top_smoke": [{"pseudo": p, "count": c} for p, c in top_smoke],
            "top_noscope": [{"pseudo": p, "count": c} for p, c in top_noscope],
            "top_blind": [{"pseudo": p, "count": c} for p, c in top_blind],
            "top_wallbang": [{"pseudo": p, "count": c} for p, c in top_wallbang],
            "top_suicides": [{"pseudo": p, "count": c} for p, c in top_suicides],
            "max_distance": md,
            "top_nemesis": [{"killer": k, "victim": v, "count": c} for (k, v), c in top_nemesis]
        }
    }, f, indent=2, ensure_ascii=False)

print(f"\nDonnées fun & maps enregistrées dans : {out_fun_json}")
