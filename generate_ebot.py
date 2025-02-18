def generate_ebot_restore_file(
    filename, map_name, first_half_score, second_half_score, overtime_score,
    consecutive_wins, losing_team, current_round, team1_players, team2_players
):
    with open(filename, "w", encoding="utf-8") as file:
        file.write('"SaveFile"\n{\n')
        file.write(f'\t"timestamp"\t"2025-02-17 12:42:08"\n')
        file.write(f'\t"map"\t"{map_name}"\n')
        file.write(f'\t"round"\t"{current_round}"\n')  # Ajout du numéro du round en cours

        # Score de la mi-temps
        file.write(f'\t"FirstHalfScore"\n\t{{\n')
        file.write(f'\t\t"team1"\t"{first_half_score[0]}"\n')
        file.write(f'\t\t"team2"\t"{first_half_score[1]}"\n')
        file.write(f'\t}}\n')

        # Score après la seconde mi-temps
        file.write(f'\t"SecondHalfScore"\n\t{{\n')
        file.write(f'\t\t"team1"\t"{second_half_score[0]}"\n')
        file.write(f'\t\t"team2"\t"{second_half_score[1]}"\n')
        file.write(f'\t}}\n')

        # Score en prolongations
        file.write(f'\t"OvertimeScore"\n\t{{\n')
        file.write(f'\t\t"team1"\t"{overtime_score[0]}"\n')
        file.write(f'\t\t"team2"\t"{overtime_score[1]}"\n')
        file.write(f'\t\t"OvertimeID"\t"1"\n')
        file.write(f'\t}}\n')

        # Historique des rounds
        file.write(f'\t"History"\n\t{{\n')
        if losing_team.lower() == "terrorist":
            file.write(f'\t\t"NumConsecutiveTerroristLoses"\t"{consecutive_wins}"\n')
        else:
            file.write(f'\t\t"NumConsecutiveCTLoses"\t"{consecutive_wins}"\n')

        file.write(f'\t\t"LoserMostRecentTeam"\t"{losing_team}"\n')
        file.write(f'\t}}\n')

        # Infos des joueurs de l'équipe 1
        file.write(f'\t"PlayersOnTeam1"\n\t{{\n')
        for player_id, player_data in team1_players.items():
            file.write(f'\t\t"{player_id}"\n\t\t{{\n')
            file.write(f'\t\t\t"cash"\t"{player_data["cash"]}"\n')

            # Ajout des équipements (au moins 1 item obligatoire)
            file.write(f'\t\t\t"Items"\n\t\t\t{{\n')
            if player_data["items"]:
                for item in player_data["items"]:
                    file.write(f'\t\t\t\t"item"\t"{item}"\n')
            else:
                file.write(f'\t\t\t\t"item"\t"weapon_knife"\n')  # Ajout d'un couteau si vide
            file.write(f'\t\t\t}}\n')

            file.write(f'\t\t}}\n')
        file.write(f'\t}}\n')  # Fermeture de PlayersOnTeam1

        # Infos des joueurs de l'équipe 2
        file.write(f'\t"PlayersOnTeam2"\n\t{{\n')
        for player_id, player_data in team2_players.items():
            file.write(f'\t\t"{player_id}"\n\t\t{{\n')
            file.write(f'\t\t\t"cash"\t"{player_data["cash"]}"\n')

            # Ajout des équipements (au moins 1 item obligatoire)
            file.write(f'\t\t\t"Items"\n\t\t\t{{\n')
            if player_data["items"]:
                for item in player_data["items"]:
                    file.write(f'\t\t\t\t"item"\t"{item}"\n')
            else:
                file.write(f'\t\t\t\t"item"\t"weapon_knife"\n')  # Ajout d'un couteau si vide
            file.write(f'\t\t\t}}\n')

            file.write(f'\t\t}}\n')
        file.write(f'\t}}\n')  # Fermeture de PlayersOnTeam2

        file.write(f'}}\n')  # Fermeture du fichier

    print(f"✅ Fichier '{filename}' généré avec succès !")

# Exemple d'utilisation
generate_ebot_restore_file(
    filename="ebot_restore_match.txt",
    map_name="de_ancient",
    first_half_score=(8, 4),
    second_half_score=(3, 6), #Supprimer dans le fichier final si premiere half
    overtime_score=(0, 0), #Supprimer dans le fichier final si pas d'overtime
    consecutive_wins=2,
    losing_team="CT",  # Choisir "Terrorist" ou "CT"
    current_round=22,  # Numéro du round en cours (8+4+3+6 = 22 ême)
    team1_players={
        "XXXXXXXX": {
            "cash": 5000,
            "items": ["weapon_knife_tactical", "weapon_m4a1_silencer", "weapon_smokegrenade"]
        },
        "XXXXXXXX": {
            "cash": 6500,
            "items": ["weapon_knife", "weapon_usp_silencer", "weapon_m4a1"]
        },
        "XXXXXXXX": {
            "cash": 7000,
            "items": ["weapon_knife", "weapon_p250", "weapon_flashbang"]
        },
        "XXXXXXXX": {
            "cash": 3200,
            "items": ["weapon_knife", "weapon_famas", "weapon_hegrenade"]
        },
        "XXXXXXXX": {
            "cash": 11000,
            "items": ["weapon_knife", "weapon_awp", "weapon_flashbang", "weapon_smokegrenade"]
        }
    },
    team2_players={
        "XXXXXXXX": {
            "cash": 4000,
            "items": ["weapon_knife", "weapon_mac10", "weapon_smokegrenade"]
        },
        "XXXXXXXX": {
            "cash": 3000,
            "items": ["weapon_knife", "weapon_galilar", "weapon_hegrenade"]
        },
        "XXXXXXXX": {
            "cash": 10000,
            "items": ["weapon_knife", "weapon_ak47", "weapon_flashbang", "weapon_molotov"]
        },
        "XXXXXXXX": {
            "cash": 7500,
            "items": ["weapon_knife", "weapon_mp9", "weapon_smokegrenade"]
        },
        "XXXXXXXX": {
            "cash": 2000,
            "items": ["weapon_knife", "weapon_deagle", "weapon_flashbang"]
        }
    }
)
