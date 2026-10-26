import os
import sys
import json
import base64
import re

sys.stdout.reconfigure(encoding='utf-8')

stats_dir = r"C:\Users\yonne\Desktop\GGLan\GGLan #19\Stats"
ebot_dir = r"C:\Users\yonne\Desktop\GGLan\GGLan #19\eBot_Pages_Brutes"

# Load extracted eBot data
with open("ebot_full_data.json", "r", encoding="utf-8") as f:
    ebot_data = json.load(f)

# Load verified GGLan 19 complete stats for score corrections
with open(os.path.join(stats_dir, "json", "stats_gglan19_complete.json"), "r", encoding="utf-8") as f:
    gglan_complete = json.load(f)

# Map verified scores for GGLan 19 matches
verified_matches_map = {str(m["match_id"]): m for m in gglan_complete["matches"]}

# Read CSS
css_content = ""
with open(os.path.join(ebot_dir, "css", "bootstrap.min.css"), "r", encoding="utf-8") as f:
    css_content = f.read()

# Read logo base64
logo_b64 = ""
logo_path = os.path.join(ebot_dir, "images", "ebot.png")
if os.path.exists(logo_path):
    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode("utf-8")

# Process matches for GGLan 19 vs Global
matches_all = ebot_data["matches"]

# Ensure GGLan 19 matches have accurate scores and map names
matches_gglan19 = []
for m in matches_all:
    mid = str(m["id"])
    if mid in verified_matches_map:
        vm = verified_matches_map[mid]
        m_copy = dict(m)
        m_copy["score_a"] = int(vm["score_a"])
        m_copy["score_b"] = int(vm["score_b"])
        m_copy["map_name"] = vm["maps_jouees"] or m["map_name"]
        m_copy["team_a"] = vm["equipe_a"]
        m_copy["team_b"] = vm["equipe_b"]
        m_copy["is_gglan19"] = True
        matches_gglan19.append(m_copy)

# Sort matches descending
matches_gglan19.sort(key=lambda x: int(x["id"]), reverse=True)
matches_all.sort(key=lambda x: int(x["id"]), reverse=True)

# Package all data into json string to embed
client_data = {
    "matches_gglan19": matches_gglan19,
    "matches_all": matches_all,
    "players_gglan": ebot_data["players_gglan"],
    "players_global": ebot_data["players_global"],
    "weapons_gglan": ebot_data["weapons_gglan"],
    "weapons_global": ebot_data["weapons_global"],
    "maps_gglan": ebot_data["maps_gglan"],
    "maps_global": ebot_data["maps_global"],
    "scoreboards": ebot_data["scoreboards"]
}
client_json_str = json.dumps(client_data, ensure_ascii=False)

html_template = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>eBot-CSGO :: Statistiques Officielles (Fichier Unique Autonome)</title>
    <style>
{css_content}

/* Compléments de style natifs eBot */
body {{
    padding-top: 60px;
    padding-bottom: 40px;
    background-color: #f8fafc;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}}
.navbar-fixed-top {{
    position: fixed;
    right: 0;
    left: 0;
    z-index: 1030;
    margin-bottom: 0;
}}
.sidebar-nav {{
    padding: 12px 0;
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}}
.sidebar-nav .nav-list > li > a {{
    padding: 6px 15px;
    font-size: 13px;
    color: #334155;
    cursor: pointer;
}}
.sidebar-nav .nav-list > li.active > a {{
    background-color: #0088cc;
    color: #ffffff;
    font-weight: 600;
}}
.sidebar-nav .nav-header {{
    font-size: 11px;
    text-transform: uppercase;
    color: #94a3b8;
    padding: 8px 15px 4px;
}}
.well-custom {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 15px;
    margin-bottom: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}}
.table-custom {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
}}
th.sortable {{
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
}}
th.sortable:hover {{
    background-color: #f1f5f9;
}}
th.sortable::after {{
    content: " ⇅";
    opacity: 0.35;
    font-size: 0.85em;
}}
th.sort-asc::after {{
    content: " ▲";
    opacity: 1;
    color: #f59e0b;
}}
th.sort-desc::after {{
    content: " ▼";
    opacity: 1;
    color: #f59e0b;
}}
.flag-box {{
    display: inline-block;
    width: 16px;
    height: 11px;
    background: #002395;
    position: relative;
    vertical-align: middle;
    margin-right: 4px;
    border: 1px solid rgba(0,0,0,0.2);
}}
.flag-box::before {{
    content: "";
    position: absolute;
    left: 5px;
    width: 6px;
    height: 100%;
    background: #ffffff;
}}
.flag-box::after {{
    content: "";
    position: absolute;
    right: 0;
    width: 5px;
    height: 100%;
    background: #ed2939;
}}
.badge-status-finished {{
    background-color: #468847;
}}
.badge-status-other {{
    background-color: #f89406;
}}
.modal-backdrop-custom {{
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    z-index: 1040;
    background-color: rgba(0,0,0,0.65);
    display: none;
}}
.modal-custom {{
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 1050;
    width: 90%;
    max-width: 950px;
    max-height: 85vh;
    background-color: #ffffff;
    border: 1px solid #999;
    border-radius: 8px;
    box-shadow: 0 5px 25px rgba(0,0,0,0.5);
    display: none;
    flex-direction: column;
}}
.modal-header-custom {{
    padding: 12px 20px;
    border-bottom: 1px solid #eee;
    background: #f8fafc;
    border-radius: 8px 8px 0 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.modal-body-custom {{
    padding: 20px;
    overflow-y: auto;
}}
.modal-footer-custom {{
    padding: 12px 20px;
    border-top: 1px solid #eee;
    background: #f8fafc;
    border-radius: 0 0 8px 8px;
    text-align: right;
}}
.filter-bar {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 10px 15px;
    margin-bottom: 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
}}
    </style>
</head>
<body>
    <!-- Top Navbar Native eBot -->
    <div class="navbar navbar-inverse navbar-fixed-top">
        <div class="navbar-inner">
            <div class="container-fluid">
                <a class="brand" href="#" onclick="showTab('matches'); return false;">eBot-CSGO</a>
                <ul class="nav">
                    <li id="nav-item-matches" class="active"><a href="#" onclick="showTab('matches'); return false;">Matchs</a></li>
                    <li id="nav-item-players"><a href="#" onclick="showTab('players'); return false;">Classement Joueurs</a></li>
                    <li id="nav-item-maps"><a href="#" onclick="showTab('maps'); return false;">Stats Maps</a></li>
                    <li id="nav-item-weapons"><a href="#" onclick="showTab('weapons'); return false;">Top Armes</a></li>
                </ul>
                <div style="float: right; line-height: 38px; color: #94a3b8; font-size: 12px;">
                    <span style="color:#38bdf8;">⚡ Fichier Unique Autonome</span> • 100% Hors-Ligne
                </div>
            </div>
        </div>
    </div>

    <div class="container-fluid">
        <div class="row-fluid">
            <!-- Sidebar eBot Native -->
            <div class="span2">
                <div class="sidebar-nav">
                    <ul class="nav nav-list">
                        <li class="nav-header">Filtre Tournoi / Saison</li>
                        <li style="padding: 0 12px 10px;">
                            <select id="seasonSelect" style="width: 100%; font-weight: 600;" onchange="onSeasonChange(this.value)">
                                <option value="gglan19" selected>GGLan #19 (Tournoi)</option>
                                <option value="global">Toutes les stats (Global)</option>
                            </select>
                        </li>
                        <li class="nav-header">Menu Principal</li>
                        <li id="side-item-matches" class="active"><a onclick="showTab('matches')"><i class="icon-th-list"></i> Matchs Archivés</a></li>
                        <li>
                            <div style="margin: 5px 12px 8px;" class="input-append">
                                <input style="width: 80px;" id="match_id_go" type="text" placeholder="# ID" onkeypress="if(event.keyCode==13) goToMatch();">
                                <button class="btn btn-small" type="button" onclick="goToMatch();">Go</button>
                            </div>
                        </li>
                        <li class="nav-header">Statistiques</li>
                        <li id="side-item-players"><a onclick="showTab('players')"><i class="icon-user"></i> Classement Joueurs</a></li>
                        <li id="side-item-maps"><a onclick="showTab('maps')"><i class="icon-map-marker"></i> Statistiques Maps</a></li>
                        <li id="side-item-weapons"><a onclick="showTab('weapons')"><i class="icon-fire"></i> Top par Armes</a></li>
                    </ul>
                </div>

                <div class="well-custom" style="margin-top: 15px; font-size: 11.5px; line-height: 1.5; color: #64748b;">
                    <strong>💡 Info Partage :</strong><br>
                    Ce fichier HTML est <strong>100% autonome</strong>. Vous pouvez l'envoyer par Discord, email ou le stocker sur une clé USB : il s'ouvrira immédiatement dans n'importe quel navigateur sans serveur web !
                </div>
            </div>

            <!-- Main Content Area -->
            <div class="span10">
                <!-- Header Logo eBot -->
                <div class="well-custom" style="text-align: center; padding: 15px;">
                    <img src="data:image/png;base64,{logo_b64}" alt="eBot CS2" style="max-height: 55px;" />
                </div>

                <!-- Scope Banner & Search Bar -->
                <div class="filter-bar">
                    <div>
                        <span id="scopeTitle" style="font-size: 15px; font-weight: 700; color: #1e293b;">🎯 GGLan #19 - Tournoi Officiel</span>
                        <span id="scopeSubtitle" style="color: #64748b; font-size: 12.5px; margin-left: 8px;">(70 Matchs Validés • 86 Joueurs qualifiés)</span>
                    </div>
                    <div>
                        <input type="text" id="globalSearch" placeholder="🔍 Rechercher joueur, équipe, map..." style="margin: 0; width: 260px;" onkeyup="onSearch(this.value)">
                    </div>
                </div>

                <!-- TAB 1: MATCHS -->
                <div id="tab-matches" class="tab-content-panel">
                    <div class="row-fluid">
                        <div class="span8">
                            <h5 style="margin-top:0;">Liste des Matchs Archivés</h5>
                            <table class="table table-striped table-condensed table-custom" id="tableMatches">
                                <thead>
                                    <tr>
                                        <th class="sortable" onclick="sortTable('tableMatches', 0)">#ID</th>
                                        <th></th>
                                        <th class="sortable" onclick="sortTable('tableMatches', 2)">Équipe 1</th>
                                        <th style="text-align:center;">Score</th>
                                        <th class="sortable" style="text-align:right;" onclick="sortTable('tableMatches', 4)">Équipe 2</th>
                                        <th></th>
                                        <th class="sortable" onclick="sortTable('tableMatches', 6)">Map</th>
                                        <th class="sortable" onclick="sortTable('tableMatches', 7)">Saison</th>
                                        <th>Statut</th>
                                        <th style="text-align:right;">Scoreboard</th>
                                    </tr>
                                </thead>
                                <tbody id="matchesTbody">
                                    <!-- Injected via JS -->
                                </tbody>
                            </table>
                        </div>
                        <div class="span4">
                            <h5>Informationen</h5>
                            <div class="well-custom" style="font-size: 12.5px; line-height: 1.6; color: #475569;">
                                <p><i class="icon-arrow-right"></i> <strong>Archives officielles eBot :</strong> Toutes les statistiques de matchs enregistrées par le serveur eBot de la LAN.</p>
                                <p><i class="icon-arrow-right"></i> Cliquez sur le bouton noir <strong>Show</strong> pour ouvrir instantanément la feuille de match officielle avec le détail des rounds et le tableau des joueurs.</p>
                                <p><i class="icon-arrow-right"></i> Changez de saison à tout moment dans le menu de gauche pour basculer entre la GGLan #19 et les statistiques globales.</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- TAB 2: CLASSEMENT JOUEURS -->
                <div id="tab-players" class="tab-content-panel" style="display:none;">
                    <div class="row-fluid">
                        <div class="span12">
                            <h5 style="margin-top:0;">Classement Général des Joueurs eBot</h5>
                            <table class="table table-striped table-condensed table-custom" id="tablePlayers">
                                <thead>
                                    <tr>
                                        <th class="sortable" onclick="sortTable('tablePlayers', 0)">#</th>
                                        <th class="sortable" onclick="sortTable('tablePlayers', 1)">Pseudo</th>
                                        <th class="sortable" onclick="sortTable('tablePlayers', 2)">Matchs</th>
                                        <th class="sortable" onclick="sortTable('tablePlayers', 3)">Kills</th>
                                        <th class="sortable" onclick="sortTable('tablePlayers', 4)">Morts</th>
                                        <th class="sortable" onclick="sortTable('tablePlayers', 5)">Ratio K/D</th>
                                        <th class="sortable" onclick="sortTable('tablePlayers', 6)">Assists</th>
                                        <th class="sortable" onclick="sortTable('tablePlayers', 7)">HS</th>
                                        <th class="sortable" onclick="sortTable('tablePlayers', 8)">HS %</th>
                                        <th class="sortable" onclick="sortTable('tablePlayers', 9)">Points</th>
                                        <th class="sortable" onclick="sortTable('tablePlayers', 10)">First Kills</th>
                                        <th class="sortable" onclick="sortTable('tablePlayers', 11)">Aces</th>
                                    </tr>
                                </thead>
                                <tbody id="playersTbody">
                                    <!-- Injected via JS -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- TAB 3: STATS MAPS -->
                <div id="tab-maps" class="tab-content-panel" style="display:none;">
                    <div class="row-fluid">
                        <div class="span12">
                            <h5 style="margin-top:0;">Statistiques Officielles des Cartes Jouées</h5>
                            <table class="table table-striped table-condensed table-custom" id="tableMaps">
                                <thead>
                                    <tr>
                                        <th class="sortable" onclick="sortTable('tableMaps', 0)">Carte</th>
                                        <th class="sortable" onclick="sortTable('tableMaps', 1)">Fois Jouée</th>
                                        <th class="sortable" onclick="sortTable('tableMaps', 2)">Rounds Totaux</th>
                                        <th class="sortable" onclick="sortTable('tableMaps', 3)">Victoires CT</th>
                                        <th class="sortable" onclick="sortTable('tableMaps', 4)">Victoires T</th>
                                        <th class="sortable" onclick="sortTable('tableMaps', 5)">CT Win %</th>
                                        <th class="sortable" onclick="sortTable('tableMaps', 6)">T Win %</th>
                                    </tr>
                                </thead>
                                <tbody id="mapsTbody">
                                    <!-- Injected via JS -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- TAB 4: TOP ARMES -->
                <div id="tab-weapons" class="tab-content-panel" style="display:none;">
                    <div class="row-fluid">
                        <div class="span12">
                            <h5 style="margin-top:0;">Statistiques Officielles par Arme (Top Frags)</h5>
                            <table class="table table-striped table-condensed table-custom" id="tableWeapons">
                                <thead>
                                    <tr>
                                        <th class="sortable" onclick="sortTable('tableWeapons', 0)">#</th>
                                        <th class="sortable" onclick="sortTable('tableWeapons', 1)">Arme</th>
                                        <th class="sortable" onclick="sortTable('tableWeapons', 2)">Frags Totaux</th>
                                        <th class="sortable" onclick="sortTable('tableWeapons', 3)">Headshots</th>
                                        <th class="sortable" onclick="sortTable('tableWeapons', 4)">HS %</th>
                                    </tr>
                                </thead>
                                <tbody id="weaponsTbody">
                                    <!-- Injected via JS -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer Native eBot -->
        <hr>
        <footer style="text-align: center; color: #94a3b8; font-size: 12px; margin-top: 20px;">
            <p>&copy; eSport-tools 2012-2023 - 3.4 - CS2 - By deStrO - Propulsed by Bootstrap & Symfony</p>
        </footer>
    </div>

    <!-- MODAL SCOREBOARD MATCH -->
    <div id="modalBackdrop" class="modal-backdrop-custom" onclick="closeModal()"></div>
    <div id="matchModal" class="modal-custom">
        <div class="modal-header-custom">
            <div>
                <h4 id="modalMatchTitle" style="margin: 0; color: #1e293b;">Feuille de Match</h4>
                <div id="modalMatchSubtitle" style="font-size: 13px; color: #64748b; margin-top: 2px;"></div>
            </div>
            <button type="button" class="close" onclick="closeModal()" style="font-size: 24px; font-weight: bold; line-height: 1; border: none; background: transparent; cursor: pointer;">&times;</button>
        </div>
        <div class="modal-body-custom">
            <h5 id="modalTeamATitle" style="color: #0088cc; margin-top: 0;"></h5>
            <table class="table table-striped table-condensed table-custom" style="margin-bottom: 20px;">
                <thead>
                    <tr>
                        <th>Joueur</th>
                        <th>Kills</th>
                        <th>Morts</th>
                        <th>Ratio K/D</th>
                        <th>Assists</th>
                        <th>HS</th>
                        <th>HS %</th>
                        <th>1k</th>
                        <th>2k</th>
                        <th>3k</th>
                        <th>4k</th>
                        <th>Aces</th>
                        <th>FK</th>
                    </tr>
                </thead>
                <tbody id="modalTeamATbody"></tbody>
            </table>

            <h5 id="modalTeamBTitle" style="color: #ed2939; margin-top: 15px;"></h5>
            <table class="table table-striped table-condensed table-custom">
                <thead>
                    <tr>
                        <th>Joueur</th>
                        <th>Kills</th>
                        <th>Morts</th>
                        <th>Ratio K/D</th>
                        <th>Assists</th>
                        <th>HS</th>
                        <th>HS %</th>
                        <th>1k</th>
                        <th>2k</th>
                        <th>3k</th>
                        <th>4k</th>
                        <th>Aces</th>
                        <th>FK</th>
                    </tr>
                </thead>
                <tbody id="modalTeamBTbody"></tbody>
            </table>
        </div>
        <div class="modal-footer-custom">
            <button class="btn btn-inverse" onclick="closeModal()">Fermer</button>
        </div>
    </div>

    <!-- EMBEDDED DATA & CLIENT SCRIPT -->
    <script>
        var DATA = {client_json_str};
        var currentSeason = "gglan19";
        var currentTab = "matches";

        document.addEventListener("DOMContentLoaded", function() {{
            renderAll();
        }});

        function onSeasonChange(val) {{
            currentSeason = val;
            var title = document.getElementById("scopeTitle");
            var sub = document.getElementById("scopeSubtitle");
            if (val === "gglan19") {{
                title.textContent = "🎯 GGLan #19 - Tournoi Officiel";
                sub.textContent = "(70 Matchs Validés • 86 Joueurs qualifiés)";
            }} else {{
                title.textContent = "🌍 Toutes les Statistiques (Global / Tout eBot)";
                sub.textContent = "(144 Matchs Totaux • 120 Joueurs enregistrés)";
            }}
            renderAll();
        }}

        function showTab(tabName) {{
            currentTab = tabName;
            var tabs = ["matches", "players", "maps", "weapons"];
            tabs.forEach(function(t) {{
                document.getElementById("tab-" + t).style.display = (t === tabName) ? "block" : "none";
                var navIt = document.getElementById("nav-item-" + t);
                var sideIt = document.getElementById("side-item-" + t);
                if (navIt) navIt.className = (t === tabName) ? "active" : "";
                if (sideIt) sideIt.className = (t === tabName) ? "active" : "";
            }});
        }}

        function renderAll() {{
            renderMatches();
            renderPlayers();
            renderMaps();
            renderWeapons();
        }}

        function renderMatches() {{
            var tbody = document.getElementById("matchesTbody");
            tbody.innerHTML = "";
            var matches = (currentSeason === "gglan19") ? DATA.matches_gglan19 : DATA.matches_all;

            matches.forEach(function(m) {{
                var tr = document.createElement("tr");
                var sa = parseInt(m.score_a) || 0;
                var sb = parseInt(m.score_b) || 0;
                var saStr = sa < 10 ? "0" + sa : "" + sa;
                var sbStr = sb < 10 ? "0" + sb : "" + sb;

                var scoreHtml = "";
                var colA = "#0088cc", colB = "#ed2939";
                if (sa > sb) {{
                    scoreHtml = '<font color="green">' + saStr + '</font> - <font color="red">' + sbStr + '</font>';
                    colA = "green"; colB = "red";
                }} else if (sb > sa) {{
                    scoreHtml = '<font color="red">' + saStr + '</font> - <font color="green">' + sbStr + '</font>';
                    colA = "red"; colB = "green";
                }} else {{
                    scoreHtml = '<font color="blue">' + saStr + '</font> - <font color="blue">' + sbStr + '</font>';
                }}

                tr.innerHTML = 
                    '<td width="35" style="padding-left: 10px;"><strong>#' + m.id + '</strong></td>' +
                    '<td width="16"><div class="flag-box"></div></td>' +
                    '<td width="160"><span style="float:left; font-weight:600;"><font color="' + colA + '">' + m.team_a + '</font></span></td>' +
                    '<td width="65" style="text-align:center; font-weight:bold; font-size:1.05em;">' + scoreHtml + '</td>' +
                    '<td width="160"><span style="float:right; font-weight:600;"><font color="' + colB + '">' + m.team_b + '</font></span></td>' +
                    '<td width="16"><div class="flag-box"></div></td>' +
                    '<td width="110" align="center"><strong>' + m.map_name + '</strong></td>' +
                    '<td width="120" style="color:#64748b; font-size:0.9em;">' + m.season_name + '</td>' +
                    '<td width="70"><span class="badge ' + (m.status == 0 ? 'badge-status-finished' : 'badge-status-other') + '">Finished</span></td>' +
                    '<td style="text-align:right;"><button class="btn btn-inverse btn-mini" onclick="openMatchModal(\\'' + m.id + '\\')">Show</button></td>';
                tbody.appendChild(tr);
            }});
        }}

        function renderPlayers() {{
            var tbody = document.getElementById("playersTbody");
            tbody.innerHTML = "";
            var players = (currentSeason === "gglan19") ? DATA.players_gglan : DATA.players_global;

            players.forEach(function(p, idx) {{
                var tr = document.createElement("tr");
                var kd = parseFloat(p.kd) || 0;
                var kdColor = kd >= 1.0 ? "#468847" : "#b94a48";
                tr.innerHTML = 
                    '<td>' + (idx + 1) + '</td>' +
                    '<td style="font-weight:600; color:#0088cc;">' + p.pseudo + '</td>' +
                    '<td>' + p.mj + '</td>' +
                    '<td><strong>' + p.k + '</strong></td>' +
                    '<td>' + p.d + '</td>' +
                    '<td style="font-weight:bold; color:' + kdColor + ';">' + kd.toFixed(2) + '</td>' +
                    '<td>' + p.a + '</td>' +
                    '<td>' + p.hs + '</td>' +
                    '<td>' + p.hs_pct + '%</td>' +
                    '<td>' + p.pts + '</td>' +
                    '<td>' + p.fk + '</td>' +
                    '<td style="color:' + (p.aces > 0 ? '#d9534f' : 'inherit') + '; font-weight:' + (p.aces > 0 ? 'bold' : 'normal') + ';">' + p.aces + '</td>';
                tbody.appendChild(tr);
            }});
        }}

        function renderMaps() {{
            var tbody = document.getElementById("mapsTbody");
            tbody.innerHTML = "";
            var maps = (currentSeason === "gglan19") ? DATA.maps_gglan : DATA.maps_global;

            maps.forEach(function(m) {{
                var tr = document.createElement("tr");
                tr.innerHTML = 
                    '<td style="font-weight:bold; color:#0088cc;">' + m.map_name + '</td>' +
                    '<td><strong>' + m.fois_jouee + '</strong></td>' +
                    '<td>' + m.total_rounds + '</td>' +
                    '<td style="color:#0088cc; font-weight:600;">' + m.ct_wins + '</td>' +
                    '<td style="color:#ed2939; font-weight:600;">' + m.t_wins + '</td>' +
                    '<td style="font-weight:bold; color:#0088cc;">' + m.ct_win_pct + '%</td>' +
                    '<td style="font-weight:bold; color:#ed2939;">' + m.t_win_pct + '%</td>';
                tbody.appendChild(tr);
            }});
        }}

        function renderWeapons() {{
            var tbody = document.getElementById("weaponsTbody");
            tbody.innerHTML = "";
            var weapons = (currentSeason === "gglan19") ? DATA.weapons_gglan : DATA.weapons_global;

            weapons.forEach(function(w, idx) {{
                var tr = document.createElement("tr");
                tr.innerHTML = 
                    '<td>' + (idx + 1) + '</td>' +
                    '<td style="font-weight:bold;">' + w.arme + '</td>' +
                    '<td><strong>' + w.k + '</strong></td>' +
                    '<td>' + w.hs + '</td>' +
                    '<td>' + w.hs_pct + '%</td>';
                tbody.appendChild(tr);
            }});
        }}

        function openMatchModal(mid) {{
            var matches = (currentSeason === "gglan19") ? DATA.matches_gglan19 : DATA.matches_all;
            var m = matches.find(function(x) {{ return String(x.id) === String(mid); }});
            if (!m) return;

            document.getElementById("modalMatchTitle").textContent = "Match #" + m.id + " : " + m.team_a + " (" + m.score_a + ") vs (" + m.score_b + ") " + m.team_b;
            document.getElementById("modalMatchSubtitle").textContent = "Map : " + m.map_name + " • Saison : " + m.season_name + " • Date : " + m.created_at;

            var teamATbody = document.getElementById("modalTeamATbody");
            var teamBTbody = document.getElementById("modalTeamBTbody");
            teamATbody.innerHTML = "";
            teamBTbody.innerHTML = "";

            document.getElementById("modalTeamATitle").textContent = "Équipe : " + m.team_a + " (" + m.score_a + " rounds)";
            document.getElementById("modalTeamBTitle").textContent = "Équipe : " + m.team_b + " (" + m.score_b + " rounds)";

            var players = DATA.scoreboards[String(mid)] || [];
            
            // Distribute players
            players.forEach(function(p) {{
                var tr = document.createElement("tr");
                var kd = parseFloat(p.kd) || 0;
                var kdCol = kd >= 1.0 ? "#468847" : "#b94a48";
                tr.innerHTML = 
                    '<td style="font-weight:600;">' + p.pseudo + '</td>' +
                    '<td><strong>' + p.k + '</strong></td>' +
                    '<td>' + p.d + '</td>' +
                    '<td style="font-weight:bold; color:' + kdCol + ';">' + kd.toFixed(2) + '</td>' +
                    '<td>' + p.a + '</td>' +
                    '<td>' + p.hs + '</td>' +
                    '<td>' + p.hs_pct + '%</td>' +
                    '<td>' + p.k1 + '</td>' +
                    '<td>' + p.k2 + '</td>' +
                    '<td>' + p.k3 + '</td>' +
                    '<td>' + p.k4 + '</td>' +
                    '<td style="color:' + (p.k5 > 0 ? '#d9534f' : 'inherit') + '; font-weight:' + (p.k5 > 0 ? 'bold' : 'normal') + ';">' + p.k5 + '</td>' +
                    '<td>' + p.fk + '</td>';

                if (p.team_name === m.team_a || p.team_name === 'a') {{
                    teamATbody.appendChild(tr);
                }} else {{
                    teamBTbody.appendChild(tr);
                }}
            }});

            document.getElementById("modalBackdrop").style.display = "block";
            document.getElementById("matchModal").style.display = "flex";
        }}

        function closeModal() {{
            document.getElementById("modalBackdrop").style.display = "none";
            document.getElementById("matchModal").style.display = "none";
        }}

        function goToMatch() {{
            var input = document.getElementById("match_id_go").value.trim();
            if (input) {{
                openMatchModal(input);
            }}
        }}

        function onSearch(val) {{
            val = val.toLowerCase();
            var activeTableId = (currentTab === "matches") ? "tableMatches" : ((currentTab === "players") ? "tablePlayers" : ((currentTab === "maps") ? "tableMaps" : "tableWeapons"));
            var rows = document.getElementById(activeTableId).getElementsByTagName("tbody")[0].getElementsByTagName("tr");
            for (var i = 0; i < rows.length; i++) {{
                var txt = rows[i].textContent.toLowerCase();
                rows[i].style.display = txt.indexOf(val) > -1 ? "" : "none";
            }}
        }}

        var sortOrders = {{}};
        function sortTable(tableId, colIndex) {{
            var table = document.getElementById(tableId);
            var tbody = table.querySelector("tbody");
            var rows = Array.from(tbody.querySelectorAll("tr"));
            var key = tableId + "_" + colIndex;
            var isAsc = !sortOrders[key];
            sortOrders[key] = isAsc;

            var ths = table.querySelectorAll("th.sortable");
            ths.forEach(function(th) {{ th.classList.remove("sort-asc", "sort-desc"); }});

            var clickedTh = table.querySelectorAll("th")[colIndex];
            if (clickedTh) {{
                clickedTh.classList.add(isAsc ? "sort-asc" : "sort-desc");
            }}

            rows.sort(function(a, b) {{
                var tA = a.cells[colIndex].innerText.trim();
                var tB = b.cells[colIndex].innerText.trim();
                if (tA.startsWith("#")) tA = tA.substring(1);
                if (tB.startsWith("#")) tB = tB.substring(1);
                if (tA.endsWith("%")) tA = tA.replace("%", "");
                if (tB.endsWith("%")) tB = tB.replace("%", "");
                var nA = parseFloat(tA);
                var nB = parseFloat(tB);
                if (!isNaN(nA) && !isNaN(nB)) {{
                    return isAsc ? (nA - nB) : (nB - nA);
                }}
                return isAsc ? tA.localeCompare(tB, 'fr') : tB.localeCompare(tA, 'fr');
            }});

            rows.forEach(function(r) {{ tbody.appendChild(r); }});
        }}
    </script>
</body>
</html>
"""

# Output paths
dest_desktop = r"C:\Users\yonne\Desktop\GGLan\ebot_stats_standalone.html"
dest_gdrive = r"D:\GGLan_Google_Drive_Pack\ebot_stats_standalone.html"
dest_stats = os.path.join(stats_dir, "ebot_stats_standalone.html")
dest_repo = r"c:\Users\yonne\Documents\antigravity\delightful-bell\GGLanCS2CFG\GGBot\ebot_stats_standalone.html"

with open(dest_desktop, "w", encoding="utf-8") as f:
    f.write(html_template)

with open(dest_gdrive, "w", encoding="utf-8") as f:
    f.write(html_template)

with open(dest_stats, "w", encoding="utf-8") as f:
    f.write(html_template)

with open(dest_repo, "w", encoding="utf-8") as f:
    f.write(html_template)

sz_kb = os.path.getsize(dest_desktop) / 1024
print(f"=== FICHIER UNIQUE EBOT GENERE AVEC SUCCES : {sz_kb:.1f} Ko ===")
print(f"1. Bureau : {dest_desktop}")
print(f"2. Google Drive Pack : {dest_gdrive}")
print(f"3. Stats : {dest_stats}")
