import os
import sys
import json
import re
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import shutil
import time

sys.stdout.reconfigure(encoding='utf-8')

base_url = "http://10.101.11.200"
stats_dir = r"C:\Users\yonne\Desktop\GGLan\GGLan #19\Stats"
ebot_dir = r"C:\Users\yonne\Desktop\GGLan\GGLan #19\eBot_Pages_Brutes"

matches_json_path = os.path.join(stats_dir, "json", "stats_gglan19_complete.json")
with open(matches_json_path, "r", encoding="utf-8") as f:
    complete_data = json.load(f)

matches = complete_data["matches"]
players = complete_data["players"]

matchs_dir = os.path.join(ebot_dir, "matchs")
stats_pages_dir = os.path.join(ebot_dir, "stats")
players_dir = os.path.join(ebot_dir, "players")

os.makedirs(matchs_dir, exist_ok=True)
os.makedirs(stats_pages_dir, exist_ok=True)
os.makedirs(players_dir, exist_ok=True)

print("=== EXPORTATION PUREMENT NATIVE EBOT (DESIGN 100% AUTHENTIQUE) ===")
print(f"Total Matchs : {len(matches)}")
print(f"Total Joueurs : {len(players)}")

def fetch_url(url, timeout=15):
    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"Erreur téléchargement {url}: {e}")
        return None

def clean_steamid_filename(steamid):
    clean = re.sub(r'[^\w\-_\.]', '_', steamid)
    return clean.strip('_')

# Map of steamid to filename
player_file_map = {}
for p in players:
    sid = p["steamid"]
    p_name = re.sub(r'[^\w\-_\.]', '_', p["pseudo"]).strip('_')
    fname = f"player_{p_name}_{clean_steamid_filename(sid)}.html"
    player_file_map[sid] = fname

def rewrite_ebot_native(html, depth=1):
    if not html:
        return ""
    rel = "../" if depth == 1 else ""
    
    # 1. Static assets paths
    html = html.replace('href="/css/', f'href="{rel}css/')
    html = html.replace('src="/js/', f'src="{rel}js/')
    html = html.replace('src="/images/', f'src="{rel}images/')
    html = html.replace('url(/images/', f'url({rel}images/')
    html = html.replace('url(http://10.101.11.200/images/', f'url({rel}images/')
    html = html.replace('href="/favicon.png"', f'href="{rel}favicon.png"')
    
    # 2. Native Navigation links
    html = html.replace('href="/"', f'href="{rel}index.html"')
    html = html.replace('href="/matchs/archived/1"', f'href="{rel}index.html"')
    html = html.replace('href="/matchs/current/1"', f'href="{rel}index.html"')
    html = html.replace('href="/matchs/current"', f'href="{rel}index.html"')
    html = html.replace('href="/stats"', f'href="{rel}stats/stats_overview.html"')
    html = html.replace('href="/stats/global"', f'href="{rel}stats/stats_global.html"')
    html = html.replace('href="/stats/maps"', f'href="{rel}stats/stats_maps.html"')
    html = html.replace('href="/stats/weapons"', f'href="{rel}stats/stats_weapons.html"')
    html = html.replace('href="/seasons"', f'href="{rel}index.html"')
    
    # 3. Match links
    html = re.sub(r'href="/matchs/view/(\d+)"', rf'href="{rel}matchs/match_\1.html"', html)
    
    # 4. Interactive goToMatch() search box from eBot sidebar
    html = html.replace('document.location.href = "/matchs/view/"+id;', f'document.location.href = "{rel}matchs/match_"+id+".html";')
    
    # 5. Player links
    for sid, fname in player_file_map.items():
        quoted_sid = urllib.parse.quote(sid)
        html = html.replace(f'href="/stats/players/{quoted_sid}"', f'href="{rel}players/{fname}"')
        html = html.replace(f'href="/stats/players/{sid}"', f'href="{rel}players/{fname}"')
    
    html = re.sub(r'href="/stats/players/([^"]+)"', rf'href="{rel}stats/stats_global.html"', html)
    
    return html

# 1. Export Matchs (Design 100% d'origine sans bandeau)
def export_match(m):
    mid = str(m["match_id"])
    url = f"{base_url}/matchs/view/{mid}"
    raw = fetch_url(url)
    if raw:
        processed = rewrite_ebot_native(raw, depth=1)
        out_path = os.path.join(matchs_dir, f"match_{mid}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(processed)
        return mid, True
    return mid, False

print("\n1. Traitement des 70 pages de matchs (design natif eBot)...")
t0 = time.time()
with ThreadPoolExecutor(max_workers=6) as executor:
    results = list(executor.map(export_match, matches))
ok_matches = sum(1 for _, ok in results if ok)
print(f"-> {ok_matches}/{len(matches)} matchs traités en {time.time() - t0:.1f}s")

# 2. Export General Stats Pages (Design 100% d'origine)
stats_targets = [
    ("stats_weapons.html", f"{base_url}/stats/weapons"),
    ("stats_maps.html", f"{base_url}/stats/maps"),
    ("stats_global.html", f"{base_url}/stats/global"),
    ("stats_overview.html", f"{base_url}/stats")
]

print("\n2. Traitement des pages de statistiques (design natif eBot)...")
for fname, url in stats_targets:
    raw = fetch_url(url)
    if raw:
        processed = rewrite_ebot_native(raw, depth=1)
        out_path = os.path.join(stats_pages_dir, fname)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(processed)
        print(f"-> {fname} sauvegardé.")

# 3. Export Player Pages (Design 100% d'origine)
def export_player(p):
    sid = p["steamid"]
    fname = player_file_map[sid]
    quoted_sid = urllib.parse.quote(sid)
    url = f"{base_url}/stats/players/{quoted_sid}"
    raw = fetch_url(url)
    if raw:
        processed = rewrite_ebot_native(raw, depth=1)
        out_path = os.path.join(players_dir, fname)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(processed)
        return p["pseudo"], True
    return p["pseudo"], False

print(f"\n3. Traitement des {len(players)} fiches joueurs (design natif eBot)...")
t0 = time.time()
with ThreadPoolExecutor(max_workers=6) as executor:
    p_results = list(executor.map(export_player, players))
ok_p = sum(1 for _, ok in p_results if ok)
print(f"-> {ok_p}/{len(players)} joueurs traités en {time.time() - t0:.1f}s")

# 4. Generate Root index.html USING THE EXACT NATIVE EBOT TEMPLATE
print("\n4. Génération de l'index.html avec le template officiel eBot...")

# Build the 70 match rows in native eBot format
match_rows_html = ""
for m in matches:
    mid = str(m["match_id"])
    sa = int(m.get('score_a', 0))
    sb = int(m.get('score_b', 0))
    ta = m.get('equipe_a', '')
    tb = m.get('equipe_b', '')
    map_name = m.get('maps_jouees', '') or 'CS2'
    
    sa_str = f"{sa:02d}"
    sb_str = f"{sb:02d}"
    
    if sa > sb:
        score_html = f'<font color="green">{sa_str}</font> - <font color="red">{sb_str}</font>'
        color_a = "blue"
        color_b = "red"
    elif sb > sa:
        score_html = f'<font color="red">{sa_str}</font> - <font color="green">{sb_str}</font>'
        color_a = "red"
        color_b = "blue"
    else:
        score_html = f'<font color="blue">{sa_str}</font> - <font color="blue">{sb_str}</font>'
        color_a = "blue"
        color_b = "blue"
        
    match_rows_html += f"""
    <tr>
        <td width="30" style="padding-left: 10px;">
            <span style="float:left">#{mid}</span>
        </td>
        <td width="16">
            <i class="flag flag-fr"></i>
        </td>
        <td width="160" style="padding-left: 10px;">
            <span style="float:left"><font color="{color_a}">{ta}</font></span>
        </td>
        <td width="60">
            <div class="score" style="text-align:center;" id="score-{mid}">{score_html}</div>
        </td>
        <td width="160">
            <span style="text-align:right; float:right;"><font color="{color_b}">{tb}</font></span>
        </td>
        <td width="16">
            <i class="flag flag-fr"></i>
        </td>
        <td width="110" align="center">
            {map_name}
        </td>
        <td width="120">
            GGLan #19
        </td>
        <td width="30" align="center">
            <img id="flag-{mid}" src="images/icons/flag_green.png" />
        </td>
        <td>
            <div class="status status-{mid}">
                Finished
            </div>
        </td>
        <td style="padding-left: 5px; text-align:right;">
            <a href="matchs/match_{mid}.html"><button class="btn btn-inverse btn-mini">Show</button></a>
        </td>
    </tr>
    """

native_index_template = f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr" lang="fr">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <meta name="title" content="eBot :: Your ingame bot manager for CS2" />
        <title>eBot :: Your ingame bot manager for CS2 - GGLan #19</title>
        <link rel="shortcut icon" type="image/png" href="favicon.png" />

        <link rel="stylesheet" type="text/css" media="screen" href="css/bootstrap.min.css" />
        <link rel="stylesheet" type="text/css" media="screen" href="css/bootstrap-responsive.min.css" />
        <link rel="stylesheet" type="text/css" media="screen" href="css/tipsy.css" />
        <link rel="stylesheet" type="text/css" media="screen" href="css/datatable.bootstrap.css" />
        <link rel="stylesheet" type="text/css" media="screen" href="css/flags.css" />
        <link rel="stylesheet" type="text/css" media="screen" href="css/hubinfo.min.css" />
        <script type="text/javascript" src="js/jquery-1.8.2.min.js"></script>
        <script type="text/javascript" src="js/bootstrap.min.js"></script>
        <script type="text/javascript" src="js/jquery.validate.min.js"></script>
        <script type="text/javascript" src="js/jquery.tipsy.js"></script>
        <script type="text/javascript" src="js/jquery.tablesorter.min.js"></script>
        <script type="text/javascript" src="js/jquery.datatable.min.js"></script>
        <script type="text/javascript" src="js/datatable.bootstrap.js"></script>
        <script type="text/javascript" src="js/heatmap.js"></script>
        <script type="text/javascript" src="js/raphael-min.js"></script>
        <script type="text/javascript" src="js/jquery.iphone-switch.js"></script>
        <script type="text/javascript" src="js/hubinfo.min.js"></script>
        <style type="text/css">
            body {{
                padding-top: 60px;
                padding-bottom: 40px;
            }}
            .sidebar-nav {{
                padding: 9px 0;
            }}
        </style>
    </head>
    <body>
        <!-- Top Navbar Native eBot -->
        <div class="navbar navbar-inverse navbar-fixed-top">
            <div class="navbar-inner">
                <div class="container-fluid">
                    <a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                    </a>
                    <a class="brand" href="index.html">eBot-CSGO</a>
                    <div class="nav-collapse collapse">
                        <ul class="nav">
                            <li class="active"><a href="index.html">Home</a></li>
                            <li><a href="stats/stats_overview.html">Statistics</a></li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <div class="container-fluid">
            <div class="row-fluid">
                <!-- Left Sidebar Native eBot -->
                <div class="span2">
                    <div class="well sidebar-nav">
                        <script>
                            function goToMatch() {{
                                var id = $("#match_id_go").val();
                                if (id > 0)
                                    document.location.href = "matchs/match_"+id+".html";
                            }};
                        </script>
                        <ul class="nav nav-list">
                            <li class="nav-header">Main Menu</li>
                            <li class="active"><a href="index.html">Home</a></li>
                            <li><a href="stats/stats_overview.html">Statistics</a></li>
                            <li class="nav-header">Match Menu</li>
                            <li class="active"><a href="index.html">Archived Matches</a></li>
                            <li>
                                <div style="margin-top: 5px; margin-bottom: 5px;" class="input-append">
                                    <input class="span8" id="match_id_go" type="text" placeholder="Match ID">
                                    <button class="btn" type="button" onclick="goToMatch();">Go</button>
                                </div>
                            </li>
                            <li class="nav-header">Statistics</li>
                            <li><a href="stats/stats_global.html">Global Statistics</a></li>
                            <li><a href="stats/stats_maps.html">Statistics by Map</a></li>
                            <li><a href="stats/stats_weapons.html">Statistics by Weapon</a></li>
                        </ul>
                    </div>
                </div>

                <!-- Main Content Native eBot -->
                <div class="span10">
                    <div class="well">
                        <center><img src="images/ebot.png" alt="eBot CS2" /></center>
                    </div>

                    <div class="row-fluid">
                        <div class="span8">
                            <h5>Archived Matches - GGLan #19 (70 Matchs)</h5>
                            
                            <table class="table table-striped table-condensed" style="font-size: 0.9em">
                                <thead>
                                    <tr>
                                        <th>#ID</th>
                                        <th></th>
                                        <th>Team 1</th>
                                        <th style="text-align:center;">Score</th>
                                        <th style="text-align:right;">Team 2</th>
                                        <th></th>
                                        <th>Map</th>
                                        <th>Season</th>
                                        <th></th>
                                        <th>Status</th>
                                        <th></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {match_rows_html}
                                </tbody>
                            </table>
                        </div>

                        <div class="span4">
                            <h5>Informationen</h5>
                            <div class="well">
                                <p><i class="icon-arrow-right"></i> <strong>Archives officielles eBot :</strong> Retrouvez l'ensemble des 70 matchs, le détail round par round, les duels, les heatmaps et les classements du tournoi.</p>
                                <p><i class="icon-arrow-right"></i> Cliquez sur le bouton <strong>Show</strong> pour ouvrir la fiche complète d'une rencontre.</p>
                                <p><i class="icon-arrow-right"></i> Utilisez le menu de gauche pour consulter le <strong>Top Armes</strong>, les <strong>Stats par Maps</strong> et le <strong>Classement Global</strong>.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Footer Native eBot -->
            <footer class="footer">
                <p>&copy; <a target="_blank" href="http://www.esport-tools.net/ebot">eSport-tools</a> 2012-2023 - 3.4 - CS2 - By <a target="_blank" href="https://twitter.com/deStrO_BE">deStrO</a> - Propulsed by <a target="_blank" href="http://twitter.github.com/bootstrap">Bootstrap</a> & <a target="_blank" href="http://www.symfony-project.com">Symfony</a></p>
            </footer>
        </div>
    </body>
</html>
"""

with open(os.path.join(ebot_dir, "index.html"), "w", encoding="utf-8") as f:
    f.write(native_index_template)

print("-> index.html généré avec le design 100% natif eBot !")

# 5. Build ZIP archive of eBot_Pages_Brutes
print("\n5. Compression du pack eBot en archive ZIP...")
zip_out = os.path.join(r"D:\GGLan_Google_Drive_Pack", "GGLan19_Pages_Brutes_eBot.zip")
seven_zip = r"C:\Program Files\7-Zip\7z.exe"
cmd = [seven_zip, "a", "-tzip", "-mx=5", "-mmt=on", zip_out, "*"]
import subprocess
proc = subprocess.run(cmd, cwd=ebot_dir, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
if os.path.exists(zip_out):
    sz_mb = os.path.getsize(zip_out) / (1024 * 1024)
    print(f"-> Archive {zip_out} mise à jour avec succès ({sz_mb:.1f} Mo)")

print("\n=== TOUTES LES PAGES SONT A 100% AVEC LE DESIGN NATIF D'EBOT ! ===")
