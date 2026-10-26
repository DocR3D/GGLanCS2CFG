import os
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

# Read both monolith files for global stats (unfiltered and gglan19)
with open("ebot_stats_global_monolith.html", "r", encoding="utf-8") as f:
    global_all_html = f.read()

with open("ebot_stats_global_gglan19_monolith.html", "r", encoding="utf-8") as f:
    global_19_html = f.read()

# Extract span10 from both
def extract_span10(html):
    match = re.search(r'<div class="span10">(.*?)</div>\s*</div>\s*(?:<!-- Please, don\'t remove the brand -->)?\s*<footer', html, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

span10_all = extract_span10(global_all_html)
span10_19 = extract_span10(global_19_html)

# Neutralize form actions
span10_all = re.sub(r'action="http://10\.101\.11\.200/[^"]*"', 'action="#"', span10_all)
span10_19 = re.sub(r'action="http://10\.101\.11\.200/[^"]*"', 'action="#"', span10_19)

# Build the wrapped content: by default, show GGLan 19, or show All
# Both are pure monolith HTML without any redesign!
interactive_span10 = f"""
<div id="wrapper-gglan19" class="season-view">
{span10_19}
</div>
<div id="wrapper-all" class="season-view" style="display:none;">
{span10_all}
</div>

<script>
$(document).ready(function() {{
    // Hook all season filter forms and buttons
    $('form[action="#"], form').on('submit', function(e) {{
        e.preventDefault();
        var selectedVal = $(this).find('select[name*="season_id"]').val();
        applySeasonFilter(selectedVal);
        return false;
    }});

    $('select[name*="season_id"]').on('change', function() {{
        var selectedVal = $(this).val();
        applySeasonFilter(selectedVal);
    }});

    function applySeasonFilter(val) {{
        if (val == "2" || val == "gglan19") {{
            $('#wrapper-all').hide();
            $('#wrapper-gglan19').show();
            $('select[name*="season_id"]').val("2");
        }} else {{
            $('#wrapper-gglan19').hide();
            $('#wrapper-all').show();
            $('select[name*="season_id"]').val("");
        }}
    }}
}});
</script>
"""

# Replace in global_19_html (so GGLan #19 is selected by default!)
final_html = re.sub(
    r'<div class="span10">(.*?)</div>\s*</div>\s*(?:<!-- Please, don\'t remove the brand -->)?\s*<footer',
    f'<div class="span10">{interactive_span10}</div></div><footer',
    global_19_html,
    flags=re.DOTALL
)

out_files = [
    r"C:\Users\yonne\Desktop\GGLan\ebot_stats_global_interactif.html",
    r"C:\Users\yonne\Desktop\GGLan\ebot_site_officiel_complet.html",
    r"D:\GGLan_Google_Drive_Pack\ebot_site_officiel_complet.html",
    r"D:\GGLan_Google_Drive_Pack\ebot_stats_global_interactif.html",
    r"C:\Users\yonne\Desktop\GGLan\GGLan #19\Stats\ebot_site_officiel_complet.html"
]

for p in out_files:
    with open(p, "w", encoding="utf-8") as f:
        f.write(final_html)

sz_mb = len(final_html) / (1024 * 1024)
print(f"=== FICHIER OFFICIEL EBOT INTERACTIF CREE ({sz_mb:.2f} Mo) ===")
print("Le bouton 'Search' filtre désormais instantanément entre GGLan #19 et Toutes les stats !")
