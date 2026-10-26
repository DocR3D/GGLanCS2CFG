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

print("=== DEBUT DE L'EXPORTATION DES PAGES BRUTES EBOT ===")
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

def rewrite_html_depth1(html, banner_title="GGLan #19 - Archive eBot"):
    if not html:
        return ""
    
    # Static assets depth 1 (from matchs/, stats/, players/)
    html = html.replace('href="/css/', 'href="../css/')
    html = html.replace('src="/js/', 'src="../js/')
    html = html.replace('src="/images/', 'src="../images/')
    html = html.replace('url(/images/', 'url(../images/')
    html = html.replace('url(http://10.101.11.200/images/', 'url(../images/')
    html = html.replace('href="/favicon.png"', 'href="../favicon.png"')
    
    # Internal links
    html = html.replace('href="/"', 'href="../index.html"')
    html = html.replace('href="/stats"', 'href="../stats/stats_overview.html"')
    html = html.replace('href="/stats/global"', 'href="../stats/stats_global.html"')
    html = html.replace('href="/stats/maps"', 'href="../stats/stats_maps.html"')
    html = html.replace('href="/stats/weapons"', 'href="../stats/stats_weapons.html"')
    
    # Rewrite match links
    html = re.sub(r'href="/matchs/view/(\d+)"', r'href="../matchs/match_\1.html"', html)
    
    # Rewrite player links
    for sid, fname in player_file_map.items():
        quoted_sid = urllib.parse.quote(sid)
        html = html.replace(f'href="/stats/players/{quoted_sid}"', f'href="../players/{fname}"')
        html = html.replace(f'href="/stats/players/{sid}"', f'href="../players/{fname}"')
    
    # In case unmapped player links exist
    html = re.sub(r'href="/stats/players/([^"]+)"', r'href="../stats/stats_global.html"', html)
    
    # Add top navigation banner
    banner = f"""
    <div style="background:#0f172a; color:#38bdf8; padding:10px 20px; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; font-size:14px; border-bottom:2px solid #38bdf8; display:flex; justify-content:space-between; align-items:center; position:sticky; top:0; z-index:99999; box-shadow:0 2px 8px rgba(0,0,0,0.5);">
        <span>📌 <strong>{banner_title}</strong> (Sauvegarde officielle 100% hors-ligne)</span>
        <div style="display:flex; gap:15px;">
            <a href="../stats/stats_weapons.html" style="color:#f59e0b; text-decoration:none; font-weight:600;">🔫 Top Armes</a>
            <a href="../stats/stats_maps.html" style="color:#10b981; text-decoration:none; font-weight:600;">🗺️ Stats Maps</a>
            <a href="../stats/stats_global.html" style="color:#c084fc; text-decoration:none; font-weight:600;">🌍 Classement Global</a>
            <a href="../index.html" style="background:#38bdf8; color:#0f172a; padding:3px 10px; border-radius:4px; text-decoration:none; font-weight:bold;">← Accueil Portail eBot</a>
        </div>
    </div>
    """
    
    # Insert banner after <body>
    if "<body" in html:
        parts = html.split("<body", 1)
        # find end of body tag
        body_rest = parts[1]
        tag_end = body_rest.find(">")
        html = parts[0] + "<body" + body_rest[:tag_end+1] + banner + body_rest[tag_end+1:]
    else:
        html = banner + html
        
    return html

# 1. Fetch Matches
def export_match(m):
    mid = str(m["match_id"])
    ta, tb = m["equipe_a"], m["equipe_b"]
    mp = m["maps_jouees"] or "CS2"
    url = f"{base_url}/matchs/view/{mid}"
    raw = fetch_url(url)
    if raw:
        banner = f"Match #{mid} : {ta} ({m['score_a']}) vs ({m['score_b']}) {tb} - {mp}"
        processed = rewrite_html_depth1(raw, banner)
        out_path = os.path.join(matchs_dir, f"match_{mid}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(processed)
        return mid, True
    return mid, False

print("\n1. Téléchargement des 70 pages de matchs...")
t0 = time.time()
with ThreadPoolExecutor(max_workers=6) as executor:
    results = list(executor.map(export_match, matches))
ok_matches = sum(1 for _, ok in results if ok)
print(f"-> {ok_matches}/{len(matches)} matchs exportés en {time.time() - t0:.1f}s")

# 2. Fetch General Stats Pages
stats_targets = [
    ("stats_weapons.html", f"{base_url}/stats/weapons", "Statistiques Officielles des Armes eBot (Top Kills, HS%)"),
    ("stats_maps.html", f"{base_url}/stats/maps", "Statistiques Officielles des Cartes eBot (Fois jouées, Winrate CT/T)"),
    ("stats_global.html", f"{base_url}/stats/global", "Classement Général des Joueurs eBot (Frags, Morts, Ratios, Entry Kills)"),
    ("stats_overview.html", f"{base_url}/stats", "Vue d'Ensemble des Statistiques du Tournoi eBot")
]

print("\n2. Téléchargement des pages de statistiques globales et d'armes...")
for fname, url, banner in stats_targets:
    raw = fetch_url(url)
    if raw:
        processed = rewrite_html_depth1(raw, banner)
        out_path = os.path.join(stats_pages_dir, fname)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(processed)
        print(f"-> {fname} exporté avec succès.")

# 3. Fetch Player Pages
def export_player(p):
    sid = p["steamid"]
    pseudo = p["pseudo"]
    fname = player_file_map[sid]
    quoted_sid = urllib.parse.quote(sid)
    url = f"{base_url}/stats/players/{quoted_sid}"
    raw = fetch_url(url)
    if raw:
        banner = f"Fiche Joueur : {pseudo} ({p['team_name']}) - {sid}"
        processed = rewrite_html_depth1(raw, banner)
        out_path = os.path.join(players_dir, fname)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(processed)
        return pseudo, True
    return pseudo, False

print(f"\n3. Téléchargement des fiches individuelles des {len(players)} joueurs...")
t0 = time.time()
with ThreadPoolExecutor(max_workers=6) as executor:
    p_results = list(executor.map(export_player, players))
ok_p = sum(1 for _, ok in p_results if ok)
print(f"-> {ok_p}/{len(players)} fiches joueurs exportées en {time.time() - t0:.1f}s")

# 4. Generate Portal index.html at root of eBot_Pages_Brutes
index_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>GGLan #19 - Portail Officiel des Pages Brutes eBot</title>
    <link rel="stylesheet" type="text/css" href="css/bootstrap.min.css">
    <link rel="stylesheet" type="text/css" href="css/bootstrap-responsive.min.css">
    <style>
        body {{
            background-color: #0b0f19;
            color: #f1f5f9;
            padding: 2rem;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }}
        .container-custom {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        header {{
            text-align: center;
            margin-bottom: 2.5rem;
            border-bottom: 1px solid #222f4c;
            padding-bottom: 1.5rem;
        }}
        header h1 {{
            font-size: 2.6rem;
            font-weight: 800;
            color: #38bdf8;
            margin-bottom: 0.5rem;
        }}
        header p {{
            color: #94a3b8;
            font-size: 1.15rem;
        }}
        .stats-nav {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2.5rem;
        }}
        .nav-card {{
            background: #151d30;
            border: 1px solid #222f4c;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            transition: transform 0.2s, border-color 0.2s;
            text-decoration: none;
            display: block;
        }}
        .nav-card:hover {{
            transform: translateY(-3px);
            border-color: #38bdf8;
            text-decoration: none;
        }}
        .nav-card-icon {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}
        .nav-card-title {{
            font-size: 1.3rem;
            font-weight: 700;
            color: #f1f5f9;
            margin-bottom: 0.25rem;
        }}
        .nav-card-desc {{
            color: #94a3b8;
            font-size: 0.9rem;
        }}
        .card-table {{
            background: #151d30;
            border: 1px solid #222f4c;
            border-radius: 12px;
            padding: 1.5rem;
        }}
        .search-box {{
            width: 100%;
            max-width: 400px;
            padding: 0.65rem 1.1rem;
            border-radius: 8px;
            border: 1px solid #222f4c;
            background: #0b0f19;
            color: #f1f5f9;
            margin-bottom: 1.25rem;
            font-size: 0.95rem;
        }}
        .search-box:focus {{
            outline: none;
            border-color: #38bdf8;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.92rem;
            text-align: left;
        }}
        th {{
            background: #0e1526;
            color: #38bdf8;
            padding: 0.85rem 1rem;
            border-bottom: 2px solid #222f4c;
            cursor: pointer;
            user-select: none;
        }}
        th:hover {{
            background: #1b2640;
            color: #fff;
        }}
        th::after {{ content: ' ⇅'; font-size: 0.8rem; opacity: 0.35; margin-left: 5px; }}
        th.sorted-asc::after {{ content: ' ▲'; opacity: 1; color: #f59e0b; }}
        th.sorted-desc::after {{ content: ' ▼'; opacity: 1; color: #f59e0b; }}
        td {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #222f4c;
        }}
        tr:hover td {{
            background: rgba(56, 189, 248, 0.05);
        }}
        .btn-ebot {{
            background: #38bdf8;
            color: #0b0f19;
            font-weight: 700;
            padding: 0.35rem 0.85rem;
            border-radius: 6px;
            text-decoration: none;
            display: inline-block;
            transition: background 0.2s;
            font-size: 0.85rem;
        }}
        .btn-ebot:hover {{
            background: #7dd3fc;
            text-decoration: none;
            color: #0b0f19;
        }}
    </style>
</head>
<body>
    <div class="container-custom">
        <header>
            <h1>⚡ GGLan #19 - Portail des Pages Brutes eBot</h1>
            <p>Exportation intégrale des pages officielles du serveur eBot • Consultation 100% Hors-Ligne</p>
        </header>

        <!-- Navigation Sections -->
        <div class="stats-nav">
            <a href="stats/stats_weapons.html" class="nav-card">
                <div class="nav-card-icon">🔫</div>
                <div class="nav-card-title">Top par Armes</div>
                <div class="nav-card-desc">Frags par arme, Headshots, Efficacité (AK, M4, AWP, Deagle...)</div>
            </a>
            <a href="stats/stats_maps.html" class="nav-card">
                <div class="nav-card-icon">🗺️</div>
                <div class="nav-card-title">Stats par Maps</div>
                <div class="nav-card-desc">Nombre de fois jouées, Rounds totaux et Winrate CT / T</div>
            </a>
            <a href="stats/stats_global.html" class="nav-card">
                <div class="nav-card-icon">🌍</div>
                <div class="nav-card-title">Classement Global</div>
                <div class="nav-card-desc">Tableau de bord de tous les joueurs et scores individuels eBot</div>
            </a>
            <a href="stats/stats_overview.html" class="nav-card">
                <div class="nav-card-icon">📊</div>
                <div class="nav-card-title">Vue d'Ensemble</div>
                <div class="nav-card-desc">Statistiques générales du tournoi eBot</div>
            </a>
        </div>

        <!-- Tous les Matchs -->
        <div class="card-table">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; margin-bottom:1rem;">
                <h3 style="margin:0; font-size:1.4rem; color:#f1f5f9;">⚔️ Toutes les Pages de Matchs eBot (70 Matchs)</h3>
                <span style="color:#94a3b8; font-size:0.9rem;">Cliquez sur un en-tête pour trier les colonnes</span>
            </div>
            <input type="text" id="searchMatch" class="search-box" placeholder="🔍 Rechercher un match, une équipe ou une map..." onkeyup="filterMatches()">
            <div style="max-height: 600px; overflow-y: auto; border: 1px solid #222f4c; border-radius: 8px;">
                <table id="matchTable">
                    <thead>
                        <tr>
                            <th onclick="sortTable(0)">ID</th>
                            <th onclick="sortTable(1)">Date & Heure</th>
                            <th onclick="sortTable(2)">Équipe A</th>
                            <th onclick="sortTable(3)">Score</th>
                            <th onclick="sortTable(4)">Équipe B</th>
                            <th onclick="sortTable(5)">Vainqueur</th>
                            <th onclick="sortTable(6)">Map</th>
                            <th>Page Brute eBot</th>
                        </tr>
                    </thead>
                    <tbody>
"""

for m in matches:
    mid = str(m["match_id"])
    sa = int(m.get('score_a', 0))
    sb = int(m.get('score_b', 0))
    index_html += f"""<tr>
        <td><strong>#{mid}</strong></td>
        <td style="color:#94a3b8; font-size:0.85rem;">{m.get('date_match')}</td>
        <td style="font-weight:600; text-align:right;">{m.get('equipe_a')}</td>
        <td style="text-align:center; font-weight:800; font-size:1.1rem; min-width:80px;">
            <span style="color:{'#10b981' if sa > sb else ('#ef4444' if sa < sb else 'inherit')}">{sa}</span>
            -
            <span style="color:{'#10b981' if sb > sa else ('#ef4444' if sa > sb else 'inherit')}">{sb}</span>
        </td>
        <td style="font-weight:600;">{m.get('equipe_b')}</td>
        <td style="color:#f59e0b; font-weight:600;">{m.get('vainqueur')}</td>
        <td><strong>{m.get('maps_jouees') or '-'}</strong></td>
        <td><a href="matchs/match_{mid}.html" class="btn-ebot" target="_blank">Ouvrir Match #{mid} ↗</a></td>
    </tr>"""

index_html += """
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        function filterMatches() {
            var input = document.getElementById("searchMatch");
            var filter = input.value.toLowerCase();
            var rows = document.getElementById("matchTable").getElementsByTagName("tbody")[0].getElementsByTagName("tr");
            for (var i = 0; i < rows.length; i++) {
                var text = rows[i].textContent.toLowerCase();
                rows[i].style.display = text.indexOf(filter) > -1 ? "" : "none";
            }
        }

        var sortOrders = {};
        function sortTable(colIndex) {
            var table = document.getElementById("matchTable");
            var tbody = table.querySelector("tbody");
            var rows = Array.from(tbody.querySelectorAll("tr"));
            var isAsc = !sortOrders[colIndex];
            sortOrders[colIndex] = isAsc;

            var ths = table.querySelectorAll("th");
            ths.forEach(function(th) { th.classList.remove("sorted-asc", "sorted-desc"); });
            ths[colIndex].classList.add(isAsc ? "sorted-asc" : "sorted-desc");

            rows.sort(function(a, b) {
                var tA = a.cells[colIndex].innerText.trim();
                var tB = b.cells[colIndex].innerText.trim();
                if (tA.startsWith("#")) tA = tA.substring(1);
                if (tB.startsWith("#")) tB = tB.substring(1);
                var nA = parseFloat(tA);
                var nB = parseFloat(tB);
                if (!isNaN(nA) && !isNaN(nB)) {
                    return isAsc ? (nA - nB) : (nB - nA);
                }
                return isAsc ? tA.localeCompare(tB, 'fr') : tB.localeCompare(tA, 'fr');
            });

            rows.forEach(function(row) { tbody.appendChild(row); });
        }
    </script>
</body>
</html>
"""

with open(os.path.join(ebot_dir, "index.html"), "w", encoding="utf-8") as f:
    f.write(index_html)

print("\n4. Portail index.html généré avec succès !")

# 5. Build ZIP archive of eBot_Pages_Brutes
print("\n5. Compression du pack eBot en archive ZIP...")
zip_out = os.path.join(r"D:\GGLan_Google_Drive_Pack", "GGLan19_Pages_Brutes_eBot.zip")
seven_zip = r"C:\Program Files\7-Zip\7z.exe"
cmd = [seven_zip, "a", "-tzip", "-mx=5", "-mmt=on", zip_out, "*"]
import subprocess
proc = subprocess.run(cmd, cwd=ebot_dir, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
if os.path.exists(zip_out):
    sz_mb = os.path.getsize(zip_out) / (1024 * 1024)
    print(f"-> Archive {zip_out} créée avec succès ({sz_mb:.1f} Mo)")

print("\n=== TOUTES LES PAGES BRUTES EBOT SONT EXPORTEES ET PRETES ! ===")
