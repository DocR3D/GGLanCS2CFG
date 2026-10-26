import os
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

# Read monolith files
with open("ebot_stats_global_monolith.html", "r", encoding="utf-8") as f:
    global_html = f.read()

with open("ebot_stats_weapons_monolith.html", "r", encoding="utf-8") as f:
    weapons_html = f.read()

with open("ebot_stats_maps_monolith.html", "r", encoding="utf-8") as f:
    maps_html = f.read()

with open("ebot_matchs_archived_monolith.html", "r", encoding="utf-8") as f:
    archived_html = f.read()

with open("ebot_home_monolith.html", "r", encoding="utf-8") as f:
    home_html = f.read()

def extract_main_content(html):
    match = re.search(r'<div class="span10">(.*?)</div>\s*</div>\s*(?:<!-- Please, don\'t remove the brand -->)?\s*<footer', html, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

content_global = extract_main_content(global_html)
content_weapons = extract_main_content(weapons_html)
content_maps = extract_main_content(maps_html)
content_archived = extract_main_content(archived_html)
content_home = extract_main_content(home_html)

# Clean any form actions that could submit to the remote IP
def neutralize_forms(c):
    c = re.sub(r'action="http://10\.101\.11\.200/[^"]*"', 'action="#" onsubmit="return false;"', c)
    return c

content_global = neutralize_forms(content_global)
content_weapons = neutralize_forms(content_weapons)
content_maps = neutralize_forms(content_maps)
content_archived = neutralize_forms(content_archived)
content_home = neutralize_forms(content_home)

# Now, in global_html, replace the sidebar and the main content area
sidebar_replacement = """
    <div class="well sidebar-nav">
        <script>
            function showEbotSection(sec) {
                $('.ebot-section').hide();
                $('#section-' + sec).show();
                $('.sidebar-nav .nav-list li').removeClass('active');
                $('#menu-' + sec).addClass('active');
                window.location.hash = sec;
            }
            $(document).ready(function() {
                var hash = window.location.hash.replace('#', '');
                if (hash && $('#section-' + hash).length) {
                    showEbotSection(hash);
                }
            });
        </script>
        <ul class="nav nav-list">
            <li class="nav-header">Main Menu</li>
            <li id="menu-home"><a href="#home" onclick="showEbotSection('home'); return false;"><i class="icon-home"></i> Home</a></li>
            <li id="menu-archived"><a href="#archived" onclick="showEbotSection('archived'); return false;"><i class="icon-th-list"></i> Archived Matches</a></li>
            <li class="nav-header">Statistics</li>
            <li id="menu-global" class="active"><a href="#global" onclick="showEbotSection('global'); return false;"><i class="icon-user"></i> Global Statistics</a></li>
            <li id="menu-maps"><a href="#maps" onclick="showEbotSection('maps'); return false;"><i class="icon-map-marker"></i> Statistics by Map</a></li>
            <li id="menu-weapons"><a href="#weapons" onclick="showEbotSection('weapons'); return false;"><i class="icon-fire"></i> Statistics by Weapon</a></li>
        </ul>
    </div>
"""

combined_content = f"""
<div id="section-global" class="ebot-section">
{content_global}
</div>

<div id="section-weapons" class="ebot-section" style="display:none;">
{content_weapons}
</div>

<div id="section-maps" class="ebot-section" style="display:none;">
{content_maps}
</div>

<div id="section-archived" class="ebot-section" style="display:none;">
{content_archived}
</div>

<div id="section-home" class="ebot-section" style="display:none;">
{content_home}
</div>
"""

# Replace in global_html
master_html = re.sub(r'<div class="well sidebar-nav">.*?</div>\s*</div>\s*<div class="span10">', sidebar_replacement + '</div><div class="span10">', global_html, flags=re.DOTALL)
master_html = re.sub(r'<div class="span10">(.*?)</div>\s*</div>\s*(?:<!-- Please, don\'t remove the brand -->)?\s*<footer', f'<div class="span10">{combined_content}</div></div><footer', master_html, flags=re.DOTALL)

# Change title
master_html = master_html.replace("<title>eBot :: Your ingame bot manager for CS:GO</title>", "<title>eBot-CSGO :: Site Officiel et Statistiques Complètes (Fichier Unique)</title>")

# Output file
out_path = r"C:\Users\yonne\Desktop\GGLan\ebot_site_officiel_complet.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(master_html)

# Also copy to Google Drive pack and Desktop
out_gdrive = r"D:\GGLan_Google_Drive_Pack\ebot_site_officiel_complet.html"
with open(out_gdrive, "w", encoding="utf-8") as f:
    f.write(master_html)

out_stats = r"C:\Users\yonne\Desktop\GGLan\GGLan #19\Stats\ebot_site_officiel_complet.html"
with open(out_stats, "w", encoding="utf-8") as f:
    f.write(master_html)

# Copy the individual raw monolith files as well
shutil_targets = [
    ("ebot_stats_global_monolith.html", "ebot_page_brute_stats_global.html"),
    ("ebot_stats_weapons_monolith.html", "ebot_page_brute_stats_weapons.html"),
    ("ebot_stats_maps_monolith.html", "ebot_page_brute_stats_maps.html"),
    ("ebot_matchs_archived_monolith.html", "ebot_page_brute_matchs_archives.html"),
    ("ebot_home_monolith.html", "ebot_page_brute_accueil.html")
]

import shutil
for src, dst_name in shutil_targets:
    shutil.copy2(src, os.path.join(r"C:\Users\yonne\Desktop\GGLan", dst_name))
    shutil.copy2(src, os.path.join(r"D:\GGLan_Google_Drive_Pack", dst_name))

sz_mb = os.path.getsize(out_path) / (1024 * 1024)
print(f"=== MASTER EBOT MONOLITH GENERE : {sz_mb:.2f} Mo ===")
print(f"Fichier : {out_path}")
