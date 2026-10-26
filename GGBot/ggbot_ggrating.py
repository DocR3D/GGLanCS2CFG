#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GGBot - Moteur d'évaluation GGRating 3.0 (Architecture HLTV 3.0 CS2)
Calculé à partir des fichiers GOTV .dem via demoparser2.

Piliers :
  1. eKPR (25%) : Frags pondérés par l'armure et l'équipement (duels éco vs fusils)
  2. eADR (25%) : Dégâts réels par round (plafonnés à 100/victime, hors overkills)
  3. eKAST (20%) : % rounds avec Kill, Assist (>=40 dmg), Survie ou Traded (<5.0s)
  4. Round Swing (12%) : Delta réel de probabilité de victoire par action (remplace l'Impact)
  5. Survie Utile (10%) : Survie active valorisée, saves passives pénalisées
  6. Multi-Kills (8%) : Poids rééquilibré des 2k, 3k, 4k, 5k
"""

import os
import sys
import time
import json
import csv
import argparse
from datetime import datetime
import pandas as pd
import numpy as np
from demoparser2 import DemoParser

sys.stdout.reconfigure(encoding='utf-8')

# Table de probabilité de victoire selon l'avantage numérique (friendly_alive, enemy_alive)
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

# Catégorisation des armes pour la pondération économique
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
        return 1.25 # Frag pistolet contre arme lourde
    if k_tier in ['rifle', 'awp'] and v_tier == 'eco':
        return 0.75 # Frag anti-éco facile
    return 1.00

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

def parse_single_demo(demo_path):
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
        
    # Élimination du knife round s'il existe
    if len(raw_rounds) > 1 and (raw_rounds[0][1] - raw_rounds[0][0] < 3000 or raw_rounds[0][1] < 5000):
        raw_rounds = raw_rounds[1:]
        
    if not raw_rounds:
        return None, 0
        
    round_intervals = [(idx + 1, s, e, w) for idx, (s, e, w) in enumerate(raw_rounds)]
    total_rounds = len(round_intervals)
    
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
    
    all_players = set(kills["attacker_name"]).union(set(deaths["user_name"]))
    all_players.discard("world")
    all_players.discard(None)
    
    p_steam = {}
    for _, row in deaths.iterrows():
        att, ast = row["attacker_name"], row["attacker_steamid"]
        if att and ast: p_steam[att] = to_steam3(ast)
        vic, vst = row["user_name"], row["user_steamid"]
        if vic and vst: p_steam[vic] = to_steam3(vst)
        
    p_side = {}
    for p in all_players:
        if p in ct_players: p_side[p] = "A"
        elif p in t_players: p_side[p] = "B"
        else: p_side[p] = "A"
        
    p_stats = {p: {
        "pseudo": p,
        "steamid": p_steam.get(p, ""),
        "kills": 0, "deaths": 0, "assists": 0,
        "damage_raw": 0, "damage_eco": 0.0, "kills_eco": 0.0,
        "kast_rounds": 0, "survived_rounds": 0, "round_swing_sum": 0.0,
        "first_kills": 0, "first_deaths": 0, "headshots": 0,
        "k1": 0, "k2": 0, "k3": 0, "k4": 0, "k5": 0,
        "rounds": total_rounds
    } for p in all_players}
    
    TRADE_TICKS = 320 # 5 secondes à 64 ticks
    
    for r_num, s_tick, e_tick, winner_side in round_intervals:
        r_deaths = deaths[deaths["match_round"] == r_num].sort_values("tick").reset_index(drop=True)
        r_hurts = hurts[hurts["match_round"] == r_num].sort_values("tick").reset_index(drop=True)
        r_kills = kills[kills["match_round"] == r_num].sort_values("tick").reset_index(drop=True)
        
        alive_a = set([p for p in all_players if p_side.get(p) == "A"])
        alive_b = set([p for p in all_players if p_side.get(p) == "B"])
        
        victim_dmg = {}
        dmg_by_att = {}
        for _, h in r_hurts.iterrows():
            att, vic, dmg = h["attacker_name"], h["user_name"], h["dmg_health"]
            if not att or att == vic or att == "world" or att not in p_stats: continue
            taken = victim_dmg.get(vic, 0)
            real_d = min(dmg, max(0, 100 - taken))
            victim_dmg[vic] = taken + real_d
            
            w_mult = get_duel_multiplier(h["weapon"], "rifle")
            if att not in dmg_by_att: dmg_by_att[att] = {"raw": 0, "eco": 0.0, "to_vic": {}}
            dmg_by_att[att]["raw"] += real_d
            dmg_by_att[att]["eco"] += real_d * w_mult
            dmg_by_att[att]["to_vic"][vic] = dmg_by_att[att]["to_vic"].get(vic, 0) + real_d
            
        for att, d_val in dmg_by_att.items():
            if att in p_stats:
                p_stats[att]["damage_raw"] += d_val["raw"]
                p_stats[att]["damage_eco"] += d_val["eco"]
                
        dead_in_round = set(r_deaths["user_name"].unique())
        for att, d_val in dmg_by_att.items():
            for vic, d_amt in d_val["to_vic"].items():
                if vic in dead_in_round and d_amt >= 40:
                    k_vic = r_kills[r_kills["user_name"] == vic]
                    if k_vic.empty or k_vic.iloc[0]["attacker_name"] != att:
                        p_stats[att]["assists"] += 1
                        
        traded_deaths = set()
        for idx_k, k_row in r_deaths.iterrows():
            vic, killer, k_tick = k_row["user_name"], k_row["attacker_name"], k_row["tick"]
            vic_side = p_side.get(vic)
            if killer and killer != "world" and killer != vic:
                subseq = r_deaths[(r_deaths["tick"] > k_tick) & (r_deaths["tick"] <= k_tick + TRADE_TICKS)]
                for _, s_row in subseq.iterrows():
                    if s_row["user_name"] == killer:
                        trader = s_row["attacker_name"]
                        if trader and p_side.get(trader) == vic_side:
                            traded_deaths.add(vic)
                            break
                            
        if not r_kills.empty:
            fk_att = r_kills.iloc[0]["attacker_name"]
            fk_vic = r_kills.iloc[0]["user_name"]
            if fk_att in p_stats: p_stats[fk_att]["first_kills"] += 1
            if fk_vic in p_stats: p_stats[fk_vic]["first_deaths"] += 1
            
        round_swing = {p: 0.0 for p in all_players}
        round_kills = {p: 0 for p in all_players}
        
        for _, k_row in r_deaths.iterrows():
            killer, vic = k_row["attacker_name"], k_row["user_name"]
            vic_side, killer_side = p_side.get(vic), p_side.get(killer)
            
            cnt_a, cnt_b = len(alive_a), len(alive_b)
            p_a_before = get_win_prob(cnt_a, cnt_b)
            
            if vic in alive_a: alive_a.remove(vic)
            if vic in alive_b: alive_b.remove(vic)
            
            cnt_a_after, cnt_b_after = len(alive_a), len(alive_b)
            p_a_after = get_win_prob(cnt_a_after, cnt_b_after)
            
            delta_a = p_a_after - p_a_before
            delta_b = -delta_a
            
            if killer and killer in p_stats and killer_side:
                d_k = delta_a if killer_side == "A" else delta_b
                w_mult = get_duel_multiplier(k_row.get("weapon"), "rifle")
                round_swing[killer] += d_k * w_mult
                p_stats[killer]["kills"] += 1
                p_stats[killer]["kills_eco"] += 1.0 * w_mult
                round_kills[killer] += 1
                if k_row.get("headshot") == True:
                    p_stats[killer]["headshots"] += 1
                    
            if vic and vic in p_stats and vic_side:
                d_v = delta_a if vic_side == "A" else delta_b
                round_swing[vic] += d_v
                p_stats[vic]["deaths"] += 1
                
        for p, k_cnt in round_kills.items():
            if k_cnt == 1: p_stats[p]["k1"] += 1
            elif k_cnt == 2: p_stats[p]["k2"] += 1
            elif k_cnt == 3: p_stats[p]["k3"] += 1
            elif k_cnt == 4: p_stats[p]["k4"] += 1
            elif k_cnt >= 5: p_stats[p]["k5"] += 1
            
        survivors = alive_a.union(alive_b)
        for p in all_players:
            has_k = round_kills.get(p, 0) > 0
            has_a = any(d_val.get("to_vic", {}).get(v, 0) >= 40 for v in dead_in_round) if p in dmg_by_att else False
            has_s = p in survivors
            has_t = p in traded_deaths
            if has_s: p_stats[p]["survived_rounds"] += 1
            if has_k or has_a or has_s or has_t: p_stats[p]["kast_rounds"] += 1
            p_stats[p]["round_swing_sum"] += round_swing.get(p, 0.0)
            
    return p_stats, total_rounds

def calculate_ggrating_scores(player_stats_list, baselines=None):
    if not baselines:
        ekprs = [p["kills_eco"] / max(1, p["rounds"]) for p in player_stats_list]
        eadrs = [p["damage_eco"] / max(1, p["rounds"]) for p in player_stats_list]
        kasts = [(p["kast_rounds"] / max(1, p["rounds"])) * 100.0 for p in player_stats_list]
        survs = [(p["survived_rounds"] / max(1, p["rounds"])) * 100.0 for p in player_stats_list]
        mks = [((p["k1"] + 4*p["k2"] + 9*p["k3"] + 16*p["k4"] + 25*p["k5"]) / max(1, p["rounds"])) for p in player_stats_list]
        swings = [p["round_swing_sum"] / max(1, p["rounds"]) for p in player_stats_list]
        
        baselines = {
            "mean_ekpr": np.mean(ekprs) or 0.69,
            "mean_eadr": np.mean(eadrs) or 75.0,
            "mean_kast": np.mean(kasts) or 77.0,
            "mean_surv": np.mean(survs) or 30.0,
            "mean_mk": np.mean(mks) or 1.25,
            "std_swing": np.std(swings) or 0.032
        }
        
    for p in player_stats_list:
        r = max(1, p["rounds"])
        e_kpr = p["kills_eco"] / r
        e_adr = p["damage_eco"] / r
        kast = (p["kast_rounds"] / r) * 100.0
        surv = (p["survived_rounds"] / r) * 100.0
        mk = (p["k1"] + 4*p["k2"] + 9*p["k3"] + 16*p["k4"] + 25*p["k5"]) / r
        sw = p["round_swing_sum"] / r
        
        s_kpr = e_kpr / baselines["mean_ekpr"]
        s_adr = e_adr / baselines["mean_eadr"]
        s_kast = kast / baselines["mean_kast"]
        s_surv = surv / baselines["mean_surv"]
        s_mk = mk / baselines["mean_mk"]
        s_swing = (sw / baselines["std_swing"]) * 0.20
        
        p["ggrating"] = round(
            0.25 * s_kpr + 0.25 * s_adr + 0.20 * s_kast + 
            0.10 * s_surv + 0.08 * s_mk + 0.12 * (1.0 + s_swing), 2
        )
        
        # HLTV 1.0
        k_r = (p["kills"] / r) / 0.679
        s_r = (max(0, r - p["deaths"]) / r) / 0.317
        mk_r = mk / 1.207
        p["hltv1"] = round((k_r + 0.7 * s_r + mk_r) / 2.7, 2)
        
        p["adr"] = round(p["damage_raw"] / r, 1)
        p["kast_pct"] = round(kast, 1)
        p["swing_pct"] = round(sw * 100.0, 1)
        p["kd_ratio"] = round(p["kills"] / max(1, p["deaths"]), 2)
        p["hs_pct"] = round(p["headshots"] / max(1, p["kills"]) * 100.0, 1)
        
    player_stats_list.sort(key=lambda x: x["ggrating"], reverse=True)
    return player_stats_list, baselines

def main():
    parser = argparse.ArgumentParser(description="GGBot GGRating 3.0 Calculator for CS2 Demos")
    parser.add_argument("--demo", type=str, help="Chemin vers un fichier .dem unique")
    parser.add_argument("--demos_dir", type=str, default=r"C:\Users\yonne\Desktop\GGLan\GGLan #19\Demos", help="Dossier contenant les démos GOTV")
    parser.add_argument("--output_csv", type=str, default=r"C:\Users\yonne\Desktop\GGLan\GGLan #19\Stats\csv\01_classement_general_joueurs_ggrating.csv")
    args = parser.parse_args()
    
    if args.demo:
        print(f"Analyse du fichier démo : {args.demo}")
        p_stats, total_rnds = parse_single_demo(args.demo)
        if p_stats:
            res, _ = calculate_ggrating_scores(list(p_stats.values()))
            df = pd.DataFrame(res)[["pseudo", "kills", "deaths", "kd_ratio", "adr", "kast_pct", "swing_pct", "hltv1", "ggrating"]]
            print(df.to_string(index=False))
        return
        
    print(f"Dossier démos : {args.demos_dir}")

if __name__ == "__main__":
    main()
