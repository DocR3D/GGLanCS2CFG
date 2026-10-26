import os
import sys
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

desktop_dir = r"C:\Users\yonne\Desktop\GGLan"
gdrive_dir = r"D:\GGLan_Google_Drive_Pack"
stats_dir = r"C:\Users\yonne\Desktop\GGLan\GGLan #19\Stats"
repo_dir = r"c:\Users\yonne\Documents\antigravity\delightful-bell\GGLanCS2CFG\GGBot"

# Load match scoreboards data for modal display
with open("ebot_full_data.json", "r", encoding="utf-8") as f:
    ebot_data = json.load(f)

scoreboards_json = json.dumps(ebot_data["scoreboards"], ensure_ascii=False)
matches_map = {str(m["id"]): m for m in ebot_data["matches"]}
matches_json = json.dumps(matches_map, ensure_ascii=False)

print("=== FIXATION DES LIENS LOCAUX ET SUPPRESSION DE TOUTES LES URLS DISTANTES ===")

# --- 1. Fix ebot_site_officiel_complet.html ---
master_path = os.path.join(desktop_dir, "ebot_site_officiel_complet.html")
with open(master_path, "r", encoding="utf-8") as f:
    html = f.read()

# Replace socket.io address
html = html.replace('var socketIoAddress = "http://10.100.100.200:12360";', 'var socketIoAddress = "";')

# Neutralize form actions to remote
html = re.sub(r'action="http://10\.101\.11\.200/[^"]*"', 'action="#" onsubmit="return false;"', html)
html = re.sub(r'action="/switch/lang/[^"]*"', 'action="#" onsubmit="return false;"', html)
html = html.replace('href="http://10.101.11.200/matchs/filter/clear"', 'href="#" onclick="$(\'select[name*=\\\'season_id\\\']\').val(\'\').trigger(\\\'change\\\'); return false;"')
html = html.replace('http://10.101.11.200', 'localhost')

# Navigation Menu Links -> showEbotSection
menu_map = {
    'href="http://10.101.11.200/stats/global"': 'href="#global" onclick="showEbotSection(\'global\'); return false;"',
    'href="http://10.101.11.200/stats/maps"': 'href="#maps" onclick="showEbotSection(\'maps\'); return false;"',
    'href="http://10.101.11.200/stats/weapons"': 'href="#weapons" onclick="showEbotSection(\'weapons\'); return false;"',
    'href="http://10.101.11.200/matchs/archived/1"': 'href="#archived" onclick="showEbotSection(\'archived\'); return false;"',
    'href="http://10.101.11.200/matchs/current/1"': 'href="#home" onclick="showEbotSection(\'home\'); return false;"',
    'href="http://10.101.11.200/matchs/current"': 'href="#home" onclick="showEbotSection(\'home\'); return false;"',
    'href="http://10.101.11.200/"': 'href="#home" onclick="showEbotSection(\'home\'); return false;"',
    'href="http://10.101.11.200/stats"': 'href="#global" onclick="showEbotSection(\'global\'); return false;"',
    'href="http://10.101.11.200/seasons"': 'href="#archived" onclick="showEbotSection(\'archived\'); return false;"',
    'href="http://10.101.11.200/credits"': 'href="#home" onclick="showEbotSection(\'home\'); return false;"',
    'href="/stats/global"': 'href="#global" onclick="showEbotSection(\'global\'); return false;"',
    'href="/stats/maps"': 'href="#maps" onclick="showEbotSection(\'maps\'); return false;"',
    'href="/stats/weapons"': 'href="#weapons" onclick="showEbotSection(\'weapons\'); return false;"',
    'href="/matchs/archived/1"': 'href="#archived" onclick="showEbotSection(\'archived\'); return false;"',
    'href="/matchs/current/1"': 'href="#home" onclick="showEbotSection(\'home\'); return false;"',
    'href="/matchs/current"': 'href="#home" onclick="showEbotSection(\'home\'); return false;"',
    'href="/"': 'href="#home" onclick="showEbotSection(\'home\'); return false;"',
    'href="/stats"': 'href="#global" onclick="showEbotSection(\'global\'); return false;"',
    'href="/seasons"': 'href="#archived" onclick="showEbotSection(\'archived\'); return false;"',
    'href="/credits"': 'href="#home" onclick="showEbotSection(\'home\'); return false;"'
}

for src_link, dst_link in menu_map.items():
    html = html.replace(src_link, dst_link)

# Match Links -> openLocalMatchModal(mid)
# Matches patterns like href="http://10.101.11.200/matchs/view/176" or href="/matchs/view/176"
html = re.sub(
    r'href="(?:http://10\.101\.11\.200)?/matchs/view/(\d+)(?:#[^"]*)?"',
    r'href="#match-\1" onclick="openLocalMatchModal(\'\1\'); return false;"',
    html
)

# Player Links -> openLocalPlayerModal(pseudo) or filter
# e.g. href="http://10.101.11.200/stats/players/%5BU%3A1%3A182125144%5D">attaboy</a>
html = re.sub(
    r'href="(?:http://10\.101\.11\.200)?/stats/players/[^"]*"',
    r'href="#" onclick="filterTableByPlayer(this.innerText); return false;"',
    html
)

# Replace goToMatch function
old_gotomatch = 'document.location.href = "/matchs/view/"+id;'
new_gotomatch = 'openLocalMatchModal(id);'
html = html.replace(old_gotomatch, new_gotomatch)
html = html.replace('document.location.href = "http://10.101.11.200/matchs/view/"+id;', new_gotomatch)

# Heatmap links
html = re.sub(r'href="(?:http://10\.101\.11\.200)?/stats/heatmap/maps/[^"]*"', r'href="#maps" onclick="showEbotSection(\'maps\'); return false;"', html)

# Inject the Local Match Modal and Scoreboards Data into the page right before </body>
modal_and_script = f"""
<!-- MODAL SCOREBOARD MATCH LOCAL & AUTONOME -->
<div id="localModalBackdrop" style="position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.7); z-index:99998; display:none;" onclick="closeLocalMatchModal()"></div>
<div id="localMatchModal" style="position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); width:90%; max-width:950px; max-height:85vh; background:#fff; border-radius:8px; box-shadow:0 10px 30px rgba(0,0,0,0.5); z-index:99999; display:none; flex-direction:column; overflow:hidden;">
    <div style="padding:15px 20px; background:#f8fafc; border-bottom:1px solid #e2e8f0; display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h4 id="localModalTitle" style="margin:0; font-size:17px; color:#1e293b;">Feuille de Match</h4>
            <div id="localModalSubtitle" style="font-size:12px; color:#64748b; margin-top:2px;"></div>
        </div>
        <button type="button" onclick="closeLocalMatchModal()" style="font-size:24px; border:none; background:transparent; cursor:pointer; line-height:1; font-weight:bold; color:#64748b;">&times;</button>
    </div>
    <div style="padding:20px; overflow-y:auto; flex:1;">
        <h5 id="localTeamATitle" style="color:#0088cc; margin-top:0;">Équipe 1</h5>
        <table class="table table-striped table-condensed" style="font-size:12px; margin-bottom:20px;">
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
            <tbody id="localTeamATbody"></tbody>
        </table>

        <h5 id="localTeamBTitle" style="color:#ed2939; margin-top:15px;">Équipe 2</h5>
        <table class="table table-striped table-condensed" style="font-size:12px;">
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
            <tbody id="localTeamBTbody"></tbody>
        </table>
    </div>
    <div style="padding:12px 20px; background:#f8fafc; border-top:1px solid #e2e8f0; text-align:right;">
        <button class="btn btn-inverse" onclick="closeLocalMatchModal()">Fermer</button>
    </div>
</div>

<script>
var LOCAL_SCOREBOARDS = {scoreboards_json};
var LOCAL_MATCHES = {matches_json};

function openLocalMatchModal(mid) {{
    var m = LOCAL_MATCHES[String(mid)];
    var title = m ? ("Match #" + m.id + " : " + m.team_a + " (" + m.score_a + ") vs (" + m.score_b + ") " + m.team_b) : ("Match #" + mid);
    var sub = m ? ("Map : " + m.map_name + " • Saison : " + m.season_name + " • Date : " + m.created_at) : "";
    
    document.getElementById("localModalTitle").textContent = title;
    document.getElementById("localModalSubtitle").textContent = sub;
    
    document.getElementById("localTeamATitle").textContent = m ? ("Équipe 1 : " + m.team_a + " (" + m.score_a + " rounds)") : "Équipe 1";
    document.getElementById("localTeamBTitle").textContent = m ? ("Équipe 2 : " + m.team_b + " (" + m.score_b + " rounds)") : "Équipe 2";
    
    var tA = document.getElementById("localTeamATbody");
    var tB = document.getElementById("localTeamBTbody");
    tA.innerHTML = "";
    tB.innerHTML = "";
    
    var players = LOCAL_SCOREBOARDS[String(mid)] || [];
    if (players.length === 0) {{
        tA.innerHTML = '<tr><td colspan="13" style="text-align:center; color:#94a3b8;">Aucun détail de joueur enregistré pour ce match dans eBot.</td></tr>';
    }} else {{
        players.forEach(function(p) {{
            var kd = parseFloat(p.kd) || 0;
            var kdColor = kd >= 1.0 ? "#468847" : "#b94a48";
            var tr = document.createElement("tr");
            tr.innerHTML = 
                '<td style="font-weight:600;">' + p.pseudo + '</td>' +
                '<td><strong>' + p.k + '</strong></td>' +
                '<td>' + p.d + '</td>' +
                '<td style="font-weight:bold; color:' + kdColor + ';">' + kd.toFixed(2) + '</td>' +
                '<td>' + p.a + '</td>' +
                '<td>' + p.hs + '</td>' +
                '<td>' + p.hs_pct + '%</td>' +
                '<td>' + p.k1 + '</td>' +
                '<td>' + p.k2 + '</td>' +
                '<td>' + p.k3 + '</td>' +
                '<td>' + p.k4 + '</td>' +
                '<td style="color:' + (p.k5 > 0 ? '#d9534f' : 'inherit') + '; font-weight:' + (p.k5 > 0 ? 'bold' : 'normal') + ';">' + p.k5 + '</td>' +
                '<td>' + p.fk + '</td>';
                
            if (m && (p.team_name === m.team_a || p.team_name === 'a')) {{
                tA.appendChild(tr);
            }} else {{
                tB.appendChild(tr);
            }}
        }});
    }}
    
    document.getElementById("localModalBackdrop").style.display = "block";
    document.getElementById("localMatchModal").style.display = "flex";
}}

function closeLocalMatchModal() {{
    document.getElementById("localModalBackdrop").style.display = "none";
    document.getElementById("localMatchModal").style.display = "none";
}}

function filterTableByPlayer(name) {{
    name = name.trim();
    if ($.fn.dataTable && $('#tableScore').length) {{
        $('#tableScore').dataTable().fnFilter(name);
    }}
}}
</script>
"""

html = html.replace("</body>", modal_and_script + "\n</body>")

# Check remaining remote URLs
rem = re.findall(r'http://10\.[^\s"\'<>]+', html)
print(f"Occurrences restantes de 10.x dans ebot_site_officiel_complet.html : {len(rem)}")
if rem:
    print(f"Exemples : {rem[:5]}")

# Write to all outputs
for p in [master_path, os.path.join(gdrive_dir, "ebot_site_officiel_complet.html"), os.path.join(stats_dir, "ebot_site_officiel_complet.html"), os.path.join(repo_dir, "ebot_site_officiel_complet.html")]:
    with open(p, "w", encoding="utf-8") as f:
        f.write(html)
print(f"-> ebot_site_officiel_complet.html mis a jour sur le Bureau et Drive Pack !")

# --- 2. Fix the individual files (ebot_page_brute_*.html) ---
individual_files = [
    ("ebot_page_brute_stats_global.html", "stats/global"),
    ("ebot_page_brute_stats_weapons.html", "stats/weapons"),
    ("ebot_page_brute_stats_maps.html", "stats/maps"),
    ("ebot_page_brute_matchs_archives.html", "matchs/archived"),
    ("ebot_page_brute_accueil.html", "home")
]

ind_links_map = {
    'http://10.101.11.200/stats/global': 'ebot_page_brute_stats_global.html',
    'http://10.101.11.200/stats/maps': 'ebot_page_brute_stats_maps.html',
    'http://10.101.11.200/stats/weapons': 'ebot_page_brute_stats_weapons.html',
    'http://10.101.11.200/matchs/archived/1': 'ebot_page_brute_matchs_archives.html',
    'http://10.101.11.200/matchs/current/1': 'ebot_page_brute_accueil.html',
    'http://10.101.11.200/matchs/current': 'ebot_page_brute_accueil.html',
    'http://10.101.11.200/': 'ebot_page_brute_accueil.html',
    'http://10.101.11.200/stats': 'ebot_page_brute_stats_global.html',
    'http://10.101.11.200/seasons': 'ebot_page_brute_matchs_archives.html',
    'http://10.101.11.200/credits': 'ebot_page_brute_accueil.html',
    '/stats/global': 'ebot_page_brute_stats_global.html',
    '/stats/maps': 'ebot_page_brute_stats_maps.html',
    '/stats/weapons': 'ebot_page_brute_stats_weapons.html',
    '/matchs/archived/1': 'ebot_page_brute_matchs_archives.html',
    '/matchs/current/1': 'ebot_page_brute_accueil.html',
    '/matchs/current': 'ebot_page_brute_accueil.html',
    '/stats': 'ebot_page_brute_stats_global.html',
    '/seasons': 'ebot_page_brute_matchs_archives.html',
    '/credits': 'ebot_page_brute_accueil.html'
}

for fname, _ in individual_files:
    fpath = os.path.join(desktop_dir, fname)
    if not os.path.exists(fpath):
        continue
    with open(fpath, "r", encoding="utf-8") as f:
        c = f.read()
    
    # Neutralize socket.io & forms
    c = c.replace('var socketIoAddress = "http://10.100.100.200:12360";', 'var socketIoAddress = "";')
    c = re.sub(r'action="http://10\.101\.11\.200/[^"]*"', 'action="#" onsubmit="return false;"', c)
    c = re.sub(r'action="/switch/lang/[^"]*"', 'action="#" onsubmit="return false;"', c)
    
    for k, v in ind_links_map.items():
        c = c.replace(f'href="{k}"', f'href="{v}"')
        
    # Match links
    c = re.sub(r'href="(?:http://10\.101\.11\.200)?/matchs/view/(\d+)(?:#[^"]*)?"', r'href="#match-\1" onclick="openLocalMatchModal(\'\1\'); return false;"', c)
    # Player links
    c = re.sub(r'href="(?:http://10\.101\.11\.200)?/stats/players/[^"]*"', r'href="#" onclick="filterTableByPlayer(this.innerText); return false;"', c)
    # Heatmap links
    c = re.sub(r'href="(?:http://10\.101\.11\.200)?/stats/heatmap/maps/[^"]*"', r'href="ebot_page_brute_stats_maps.html"', c)
    c = c.replace('href="http://10.101.11.200/matchs/filter/clear"', 'href="#" onclick="$(\'select[name*=\\\'season_id\\\']\').val(\'\').trigger(\\\'change\\\'); return false;"')
    c = c.replace('http://10.101.11.200', 'localhost')
    
    # Inject modal if not present
    if "localMatchModal" not in c:
        c = c.replace("</body>", modal_and_script + "\n</body>")
        
    # Save back
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(c)
    with open(os.path.join(gdrive_dir, fname), "w", encoding="utf-8") as f:
        f.write(c)
    print(f"-> {fname} nettoye de tout lien distant !")

print("=== NETTOYAGE COMPLET TERMINE AVEC SUCCES ===")
