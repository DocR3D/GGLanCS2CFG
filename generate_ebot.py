def generate_ebot_file(filename, first_half_team1, first_half_team2, total_team1, total_team2, player_cash, consecutive_wins, player_items):
    with open(filename, "w", encoding="utf-8") as file:
        file.write('"SaveFile"\n{\n')
        file.write(f'\t"timestamp"\t"2025-02-17 12:42:08"\n')
        file.write(f'\t"team1"\t"a"\n')
        file.write(f'\t"team2"\t"b"\n')
        file.write(f'\t"map"\t"de_dust2"\n')
        file.write(f'\t"round"\t"{total_team1 + total_team2}"\n')

        # Score de la mi-temps
        file.write(f'\t"FirstHalfScore"\n\t{{\n')
        file.write(f'\t\t"team1"\t"{first_half_team1}"\n')
        file.write(f'\t\t"team2"\t"{first_half_team2}"\n')
        file.write(f'\t}}\n')

        # Score total actuel
        file.write(f'\t"SecondHalfScore"\n\t{{\n')
        file.write(f'\t\t"team1"\t"{total_team1 - first_half_team1}"\n')
        file.write(f'\t\t"team2"\t"{total_team2 - first_half_team2}"\n')
        file.write(f'\t}}\n')

        # Historique des rounds
        file.write(f'\t"History"\n\t{{\n')
        file.write(f'\t\t"NumConsecutiveCTLoses"\t"{consecutive_wins}"\n')
        file.write(f'\t\t"LoserMostRecentTeam"\t"CT"\n')
        file.write(f'\t\t"SpawnPointsCfg"\t"-791323894"\n')
        file.write(f'\t}}\n')

        # Résultats des rounds (tous à 0 par défaut)
        file.write(f'\t"RoundResults"\n\t{{\n')
        for i in range(1, 31):
            file.write(f'\t\t"round{i}"\t"0"\n')
        file.write(f'\t}}\n')

        # Infos sur un joueur
        file.write(f'\t"PlayersOnTeam1"\n\t{{\n')
        file.write(f'\t\t"32976386"\n\t\t{{\n')
        file.write(f'\t\t\t"name"\t"DocR3D"\n')
        file.write(f'\t\t\t"kills"\t"0"\n')
        file.write(f'\t\t\t"assists"\t"0"\n')
        file.write(f'\t\t\t"deaths"\t"0"\n')
        file.write(f'\t\t\t"mvps"\t"0"\n')
        file.write(f'\t\t\t"score"\t"0"\n')
        file.write(f'\t\t\t"cash"\t"{player_cash}"\n')
        file.write(f'\t\t\t"roundsWon"\t"{total_team1}"\n')
        file.write(f'\t\t\t"enemyKs"\t"0"\n')
        file.write(f'\t\t\t"enemyHSs"\t"0"\n')
        file.write(f'\t\t\t"enemy2Ks"\t"0"\n')
        file.write(f'\t\t\t"enemy3Ks"\t"0"\n')
        file.write(f'\t\t\t"enemy4Ks"\t"0"\n')
        file.write(f'\t\t\t"enemy5Ks"\t"0"\n')
        file.write(f'\t\t\t"enemyKAg"\t"0"\n')
        file.write(f'\t\t\t"firstKs"\t"0"\n')
        file.write(f'\t\t\t"clutchKs"\t"0"\n')
        file.write(f'\t\t\t"kills_weapon_pistol"\t"0"\n')
        file.write(f'\t\t\t"kills_weapon_sniper"\t"0"\n')
        file.write(f'\t\t\t"kills_knife"\t"0"\n')
        file.write(f'\t\t\t"kills_taser"\t"0"\n')
        file.write(f'\t\t\t"enemyDamageDealt"\t"0"\n')
        file.write(f'\t\t\t"helmet"\t"0"\n')
        file.write(f'\t\t\t"armor"\t"100"\n')

        # Ajout des items
        file.write(f'\t\t\t"Items"\n\t\t\t{{\n')
        for item in player_items:
            file.write(f'\t\t\t\t"item"\t"{item}"\n')
        file.write(f'\t\t\t}}\n')

        # MatchStats
        file.write(f'\t\t\t"MatchStats"\n\t\t\t{{\n')
        file.write(f'\t\t\t\t"EquipmentValue"\n\t\t\t\t{{\n')
        for i in range(1, 31):
            file.write(f'\t\t\t\t\t"round{i}"\t"0"\n')
        file.write(f'\t\t\t\t}}\n')

        file.write(f'\t\t\t\t"MoneySaved"\n\t\t\t\t{{\n')
        for i in range(1, 31):
            file.write(f'\t\t\t\t\t"round{i}"\t"0"\n')
        file.write(f'\t\t\t\t}}\n')

        file.write(f'\t\t\t\t"CashEarned"\n\t\t\t\t{{\n')
        for i in range(1, 31):
            file.write(f'\t\t\t\t\t"round{i}"\t"0"\n')
        file.write(f'\t\t\t\t}}\n')

        file.write(f'\t\t\t}}\n')  # Fermeture de MatchStats
        file.write(f'\t\t}}\n')  # Fermeture du joueur
        file.write(f'\t}}\n')  # Fermeture de PlayersOnTeam1

        file.write(f'}}\n')  # Fermeture du fichier

    print(f"✅ Fichier '{filename}' généré avec succès !")

# Exemple d'utilisation
generate_ebot_file(
    filename="ebot_custom_kv_items.txt",
    first_half_team1=8,
    first_half_team2=4,
    total_team1=10,
    total_team2=10,
    player_cash=5000,
    consecutive_wins=2,
    player_items=[
        "weapon_knife",
        "weapon_awp",
        "weapon_hegrenade",
        "weapon_smokegrenade",
        "weapon_flashbang",
        "weapon_fiveseven"
    ]
)
