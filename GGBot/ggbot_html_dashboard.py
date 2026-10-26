import os
import sys
import json
import csv

sys.stdout.reconfigure(encoding='utf-8')

stats_dir = r"C:\Users\yonne\Desktop\GGLan\GGLan #19\Stats"
json_path = os.path.join(stats_dir, "json", "stats_gglan19_ggrating.json")
matches_json_path = os.path.join(stats_dir, "json", "stats_gglan19_complete.json")

with open(json_path, "r", encoding="utf-8") as f:
    ggrating_data = json.load(f)

with open(matches_json_path, "r", encoding="utf-8") as f:
    complete_data = json.load(f)

players = ggrating_data["players"]
teams = complete_data["teams"]
matches = complete_data["matches"]
baselines = ggrating_data["baselines"]

total_kills = sum(p["kills"] for p in players)
total_aces = sum(p["k5"] for p in players)
total_matches = len(matches)

top_ggrating = sorted(players, key=lambda x: x["ggrating"], reverse=True)[:10]

html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>GGLan #19 - Rapport Officiel GGRating 3.0 (HLTV 3.0 CS2)</title>
    <style>
        :root {{
            --bg: #0b0f19;
            --card-bg: #151d30;
            --border: #222f4c;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --primary: #38bdf8;
            --accent: #f59e0b;
            --success: #10b981;
            --danger: #ef4444;
            --purple: #a855f7;
            --cyan: #06b6d4;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
        body {{ background-color: var(--bg); color: var(--text); padding: 2rem; line-height: 1.5; }}
        .container {{ max-width: 1540px; margin: 0 auto; }}
        header {{ text-align: center; margin-bottom: 2.5rem; border-bottom: 1px solid var(--border); padding-bottom: 1.5rem; }}
        header h1 {{ font-size: 2.6rem; font-weight: 800; color: var(--primary); margin-bottom: 0.5rem; letter-spacing: -0.04em; }}
        header p {{ color: var(--text-muted); font-size: 1.15rem; }}
        
        .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1.25rem; margin-bottom: 2rem; }}
        .kpi-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3); }}
        .kpi-val {{ font-size: 2.1rem; font-weight: 800; color: var(--text); }}
        .kpi-label {{ color: var(--text-muted); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.25rem; }}
        
        .banner-filter {{ background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 12px; padding: 1.2rem 1.6rem; margin-bottom: 2rem; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 1rem; font-size: 0.95rem; }}
        .banner-filter strong {{ color: var(--primary); }}

        .section-title {{ font-size: 1.45rem; font-weight: 700; margin-bottom: 1rem; color: var(--text); display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; }}
        .hint-sort {{ font-size: 0.85rem; font-weight: 400; color: var(--text-muted); }}
        
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 2rem; }}
        @media(max-width: 1050px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
        
        .card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.91rem; text-align: left; }}
        th {{ background: #0e1526; color: var(--primary); padding: 0.8rem 0.85rem; border-bottom: 2px solid var(--border); position: sticky; top: 0; white-space: nowrap; }}
        th.sortable {{ cursor: pointer; user-select: none; transition: background 0.15s, color 0.15s; }}
        th.sortable:hover {{ background: #1b2640; color: #fff; }}
        th.sortable::after {{ content: ' ⇅'; font-size: 0.8rem; opacity: 0.35; margin-left: 5px; }}
        th.sorted-asc {{ color: var(--accent); background: #162035; }}
        th.sorted-asc::after {{ content: ' ▲'; opacity: 1; color: var(--accent); }}
        th.sorted-desc {{ color: var(--accent); background: #162035; }}
        th.sorted-desc::after {{ content: ' ▼'; opacity: 1; color: var(--accent); }}
        
        td {{ padding: 0.65rem 0.85rem; border-bottom: 1px solid var(--border); }}
        tr:hover td {{ background: rgba(56, 189, 248, 0.04); }}
        
        .rating-badge {{ display: inline-block; padding: 0.2rem 0.55rem; border-radius: 6px; font-weight: 800; font-size: 0.92rem; }}
        .rating-elite {{ background: rgba(168, 85, 247, 0.25); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.4); }}
        .rating-high {{ background: rgba(16, 185, 129, 0.2); color: var(--success); }}
        .rating-mid {{ background: rgba(56, 189, 248, 0.2); color: var(--primary); }}
        .rating-low {{ background: rgba(239, 68, 68, 0.2); color: var(--danger); }}

        .swing-pos {{ color: var(--success); font-weight: 700; }}
        .swing-neg {{ color: var(--danger); font-weight: 600; }}

        .search-box {{ width: 100%; max-width: 380px; padding: 0.65rem 1.1rem; border-radius: 8px; border: 1px solid var(--border); background: #0b0f19; color: var(--text); margin-bottom: 1rem; }}
        .search-box:focus {{ outline: none; border-color: var(--primary); }}
        .table-container {{ max-height: 560px; overflow-y: auto; border: 1px solid var(--border); border-radius: 8px; }}

        .methodo-box {{ background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 12px; padding: 1.25rem 1.5rem; margin-bottom: 2rem; font-size: 0.92rem; line-height: 1.6; }}
        .methodo-box h3 {{ color: var(--success); margin-bottom: 0.5rem; font-size: 1.1rem; }}
        .methodo-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-top: 0.75rem; }}
        .methodo-pill {{ background: #0e1526; border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem; }}
        .methodo-pill strong {{ color: var(--primary); display: block; margin-bottom: 0.2rem; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⚡ GGLan #19 - Classement Officiel GGRating 3.0</h1>
            <p>Moteur HLTV 3.0 CS2 complet • Analyse tick-par-tick de 100% des 70 démos officielles</p>
        </header>

        <!-- Méthodologie GGRating 3.0 -->
        <div class="methodo-box">
            <h3>🔬 Architecture du Moteur GGRating 3.0 (HLTV 3.0 CS2)</h3>
            <p>Contrairement au Rating 1.0 qui ne comptait que les frags bruts, <strong>GGRating 3.0</strong> évalue chaque duel dans son contexte économique et tactique à travers 6 piliers majeurs :</p>
            <div class="methodo-grid">
                <div class="methodo-pill">
                    <strong>1. eKPR (25%)</strong>
                    Pondération économique : frags éco au pistolet valorisés (+25%), anti-éco au fusil dégonflés (-25%).
                </div>
                <div class="methodo-pill">
                    <strong>2. eADR (25%)</strong>
                    Dégâts réels infligés par round (plafonnés à 100 max par victime, hors overkills & friendly fire).
                </div>
                <div class="methodo-pill">
                    <strong>3. eKAST (20%)</strong>
                    % de rounds avec Kill, Assist (≥40 dmg réels), Survie ou Traded (&lt;5,0 secondes).
                </div>
                <div class="methodo-pill">
                    <strong>4. Round Swing (12%)</strong>
                    Delta réel de probabilité de victoire généré par chaque action (remplace l'ancien Impact).
                </div>
                <div class="methodo-pill">
                    <strong>5. Survie Utile (10%)</strong>
                    Taux de survie en round actif, pénalisant les saves passives dans les rounds déjà perdus.
                </div>
                <div class="methodo-pill">
                    <strong>6. Multi-Kills (8%)</strong>
                    Fréquence des 2k, 3k, 4k et Aces, rééquilibrée pour éviter les doublons avec le Swing.
                </div>
            </div>
        </div>

        <div class="banner-filter">
            <div>
                <strong>🎯 Baselines du Tournoi :</strong> eADR Moyenne = <strong>{baselines['mean_eadr']}</strong> • KAST Moyen = <strong>{baselines['mean_kast']}%</strong> • eKPR Moyen = <strong>{baselines['mean_ekpr']}</strong>
            </div>
            <div>
                <strong>⚖️ Calibration :</strong> GGRating calibré à <strong>1.00</strong> de moyenne pour un joueur standard
            </div>
            <div>
                <strong>💾 Données :</strong> 70 démos GOTV complètes analysées (100% du tournoi)
            </div>
        </div>
        
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-val" style="color: var(--primary);">{total_matches}</div>
                <div class="kpi-label">Matchs GOTV Analysés</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-val" style="color: var(--success);">{len(players)}</div>
                <div class="kpi-label">Joueurs Qualifiés</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-val" style="color: var(--accent);">{len(teams)}</div>
                <div class="kpi-label">Équipes Engagées</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-val">{total_kills}</div>
                <div class="kpi-label">Frags Reconnus</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-val" style="color: #ec4899;">{total_aces}</div>
                <div class="kpi-label">Aces Confirmés</div>
            </div>
        </div>

        <div class="grid-2">
            <!-- Top 10 GGRating -->
            <div class="card" style="margin-bottom:0;">
                <div class="section-title">
                    <span>⭐ Top 10 GGRating 3.0</span>
                    <span class="hint-sort">Cliquez sur un en-tête pour trier</span>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th class="sortable">#</th>
                            <th class="sortable">Pseudo</th>
                            <th class="sortable">Équipe</th>
                            <th class="sortable">GGRating</th>
                            <th class="sortable">ADR</th>
                            <th class="sortable">KAST%</th>
                            <th class="sortable">Swing/R</th>
                            <th class="sortable">K/D</th>
                        </tr>
                    </thead>
                    <tbody>
    """

for i, p in enumerate(top_ggrating, 1):
    r_val = p["ggrating"]
    sw_val = p["swing_per_round"] * 100.0
    sw_cls = "swing-pos" if sw_val >= 0 else "swing-neg"
    badge_cls = 'rating-elite' if r_val >= 1.30 else ('rating-high' if r_val >= 1.20 else ('rating-mid' if r_val >= 1.00 else 'rating-low'))
    html += f"""<tr>
        <td>{i}</td>
        <td style="font-weight:600; color:var(--primary);">{p['pseudo']}</td>
        <td>{p['team_name']}</td>
        <td><span class="rating-badge {badge_cls}">{r_val:.2f}</span></td>
        <td><strong>{p['adr']:.1f}</strong></td>
        <td>{p['kast_pct']:.1f}%</td>
        <td class="{sw_cls}">{sw_val:+.1f}%</td>
        <td>{p['kd_ratio']:.2f}</td>
    </tr>"""

html += """
                    </tbody>
                </table>
            </div>

            <!-- Classement Equipes -->
            <div class="card" style="margin-bottom:0;">
                <div class="section-title">
                    <span>🥇 Classement des Équipes</span>
                    <span class="hint-sort">Cliquez sur un en-tête pour trier</span>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th class="sortable">#</th>
                            <th class="sortable">Équipe</th>
                            <th class="sortable">MJ</th>
                            <th class="sortable">V</th>
                            <th class="sortable">D</th>
                            <th class="sortable">N</th>
                            <th class="sortable">Win %</th>
                            <th class="sortable">Diff</th>
                        </tr>
                    </thead>
                    <tbody>
"""

for i, t in enumerate(teams, 1):
    diff = int(t.get('diff_rounds', 0))
    diff_str = f"+{diff}" if diff > 0 else str(diff)
    html += f"""<tr>
        <td>{i}</td>
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

        <!-- Tableau complet de tous les joueurs avec Comparatif 3.0 vs 1.0 -->
        <div class="card">
            <div class="section-title">
                <span>👥 Statistiques Complètes des Joueurs (GGRating 3.0 vs HLTV 1.0)</span>
                <span class="hint-sort">💡 Cliquez sur n'importe quel en-tête de colonne pour trier par catégorie (ADR, KAST, Swing, Frags...)</span>
            </div>
            <input type="text" id="playerSearch" class="search-box" placeholder="🔍 Rechercher un joueur ou une équipe..." onkeyup="filterPlayers()">
            <div class="table-container">
                <table id="playersTable">
                    <thead>
                        <tr>
                            <th class="sortable">#</th>
                            <th class="sortable">Pseudo</th>
                            <th class="sortable">Équipe</th>
                            <th class="sortable">MJ</th>
                            <th class="sortable" style="color: #c084fc;">GGRating 3.0</th>
                            <th class="sortable" style="color: var(--text-muted);">HLTV 1.0</th>
                            <th class="sortable">ADR</th>
                            <th class="sortable">KAST %</th>
                            <th class="sortable">Swing/R</th>
                            <th class="sortable">Duels (FK/FD)</th>
                            <th class="sortable">K/D</th>
                            <th class="sortable">Kills</th>
                            <th class="sortable">Morts</th>
                            <th class="sortable">Assists</th>
                            <th class="sortable">HS %</th>
                            <th class="sortable">1k</th>
                            <th class="sortable">2k</th>
                            <th class="sortable">3k</th>
                            <th class="sortable">4k</th>
                            <th class="sortable">Aces</th>
                        </tr>
                    </thead>
                    <tbody>
"""

for i, p in enumerate(players, 1):
    r3 = p["ggrating"]
    r1 = p["hltv1"]
    sw = p["swing_per_round"] * 100.0
    sw_cls = "swing-pos" if sw >= 0 else "swing-neg"
    badge_cls = 'rating-elite' if r3 >= 1.30 else ('rating-high' if r3 >= 1.20 else ('rating-mid' if r3 >= 1.00 else 'rating-low'))
    
    html += f"""<tr>
        <td>{i}</td>
        <td style="font-weight:600; color:var(--primary);">{p['pseudo']}</td>
        <td>{p['team_name']}</td>
        <td>{p['matches_played']}</td>
        <td><span class="rating-badge {badge_cls}">{r3:.2f}</span></td>
        <td style="color:var(--text-muted); font-weight:600;">{r1:.2f}</td>
        <td><strong>{p['adr']:.1f}</strong></td>
        <td>{p['kast_pct']:.1f}%</td>
        <td class="{sw_cls}">{sw:+.1f}%</td>
        <td>{p['first_kills']}/{p['first_deaths']}</td>
        <td style="font-weight:600; color:{'var(--success)' if p['kd_ratio'] >= 1.0 else 'var(--danger)'};">{p['kd_ratio']:.2f}</td>
        <td><strong>{p['kills']}</strong></td>
        <td>{p['deaths']}</td>
        <td>{p['assists']}</td>
        <td>{p['hs_pct']:.1f}%</td>
        <td>{p['k1']}</td>
        <td>{p['k2']}</td>
        <td>{p['k3']}</td>
        <td>{p['k4']}</td>
        <td style="color:{'#ec4899' if p['k5'] > 0 else 'inherit'}; font-weight:{'bold' if p['k5'] > 0 else 'normal'};">{p['k5']}</td>
    </tr>"""

html += """
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Tous les Matchs Validés -->
        <div class="card">
            <div class="section-title">
                <span>⚔️ Tous les Matchs Joués du Tournoi (70 Matchs)</span>
                <span class="hint-sort">Cliquez sur un en-tête pour trier</span>
            </div>
            <div class="table-container">
                <table id="matchesTable">
                    <thead>
                        <tr>
                            <th class="sortable">ID</th>
                            <th class="sortable">Date</th>
                            <th class="sortable">Équipe A</th>
                            <th class="sortable">Score</th>
                            <th class="sortable">Équipe B</th>
                            <th class="sortable">Vainqueur</th>
                            <th class="sortable">Map</th>
                        </tr>
                    </thead>
                    <tbody>
"""

for m in matches:
    score_a = int(m.get('score_a', 0))
    score_b = int(m.get('score_b', 0))
    html += f"""<tr>
        <td>#{m.get('match_id')}</td>
        <td style="color:var(--text-muted); font-size:0.85rem;">{m.get('date_match')}</td>
        <td style="font-weight:600; text-align:right;">{m.get('equipe_a')}</td>
        <td style="text-align:center; font-weight:800; font-size:1.1rem; min-width:80px;">
            <span style="color:{'var(--success)' if score_a > score_b else ('var(--danger)' if score_a < score_b else 'inherit')}">{score_a}</span>
            -
            <span style="color:{'var(--success)' if score_b > score_a else ('var(--danger)' if score_a > score_b else 'inherit')}">{score_b}</span>
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
        // Recherche en direct
        function filterPlayers() {
            var input = document.getElementById("playerSearch");
            var filter = input.value.toLowerCase();
            var rows = document.getElementById("playersTable").getElementsByTagName("tbody")[0].getElementsByTagName("tr");
            for (var i = 0; i < rows.length; i++) {
                var pseudo = rows[i].cells[1].textContent.toLowerCase();
                var team = rows[i].cells[2].textContent.toLowerCase();
                if (pseudo.indexOf(filter) > -1 || team.indexOf(filter) > -1) {
                    rows[i].style.display = "";
                } else {
                    rows[i].style.display = "none";
                }
            }
        }

        // Système de tri dynamique par colonnes (Catégories)
        document.addEventListener("DOMContentLoaded", function() {
            var tables = document.querySelectorAll("table");
            tables.forEach(function(table) {
                var headers = table.querySelectorAll("th.sortable");
                headers.forEach(function(header, colIndex) {
                    header.addEventListener("click", function() {
                        sortTable(table, colIndex, header);
                    });
                });
            });
        });

        function parseCellValue(text) {
            text = text.trim();
            // Supprimer le '#' pour les IDs
            if (text.startsWith("#")) {
                var num = parseFloat(text.substring(1));
                if (!isNaN(num)) return num;
            }
            // Pourcentage (ex: 84.5%, +7.2%, -3.1%)
            if (text.endsWith("%")) {
                var clean = text.replace("%", "").replace("+", "");
                var num = parseFloat(clean);
                if (!isNaN(num)) return num;
            }
            // Ratio FK/FD (ex: 14/8)
            if (text.indexOf("/") > -1 && text.split("/").length === 2) {
                var parts = text.split("/");
                var p0 = parseFloat(parts[0]);
                var p1 = parseFloat(parts[1]);
                if (!isNaN(p0) && !isNaN(p1)) {
                    return (p0 * 100) - p1; // Pondération valorisant les FK positifs
                }
            }
            // Score match (ex: 13 - 10)
            if (text.indexOf("-") > -1 && text.split("-").length === 2) {
                var parts = text.split("-");
                var s0 = parseFloat(parts[0].trim());
                var s1 = parseFloat(parts[1].trim());
                if (!isNaN(s0) && !isNaN(s1)) {
                    return s0 - s1;
                }
            }
            // Nombre flottant / entier (ex: 1.35, +50, -22)
            var cleanNum = text.replace("+", "");
            var num = parseFloat(cleanNum);
            if (!isNaN(num) && (String(num) === cleanNum || String(num) === cleanNum.replace(/^0+/, "") || !isNaN(Number(cleanNum)))) {
                return num;
            }
            // Texte alphabétique standard
            return text.toLowerCase();
        }

        function sortTable(table, colIndex, clickedHeader) {
            var tbody = table.querySelector("tbody");
            var rows = Array.from(tbody.querySelectorAll("tr"));
            var isAsc = clickedHeader.classList.contains("sorted-desc");

            // Réinitialiser les indicateurs de tous les en-têtes du tableau
            table.querySelectorAll("th.sortable").forEach(function(th) {
                th.classList.remove("sorted-asc", "sorted-desc");
            });

            // Appliquer la nouvelle direction
            if (isAsc) {
                clickedHeader.classList.add("sorted-asc");
            } else {
                clickedHeader.classList.add("sorted-desc");
            }

            rows.sort(function(rowA, rowB) {
                var cellA = rowA.cells[colIndex].innerText;
                var cellB = rowB.cells[colIndex].innerText;
                var valA = parseCellValue(cellA);
                var valB = parseCellValue(cellB);

                if (typeof valA === "number" && typeof valB === "number") {
                    return isAsc ? (valA - valB) : (valB - valA);
                } else {
                    var strA = String(valA);
                    var strB = String(valB);
                    return isAsc ? strA.localeCompare(strB, 'fr') : strB.localeCompare(strA, 'fr');
                }
            });

            // Réinsérer les lignes triées
            rows.forEach(function(row) {
                tbody.appendChild(row);
            });
        }
    </script>
</body>
</html>
"""

report_path = os.path.join(stats_dir, "rapport_stats_gglan19_ggrating.html")
with open(report_path, "w", encoding="utf-8") as f:
    f.write(html)

default_report_path = os.path.join(stats_dir, "rapport_stats_gglan19.html")
with open(default_report_path, "w", encoding="utf-8") as f:
    f.write(html)

print("Rapports HTML mis à jour avec le système de tri interactif par catégorie !")
