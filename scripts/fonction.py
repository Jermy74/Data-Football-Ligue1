import pandas as pd
import json 
import glob
import os
from pathlib import Path

def load_match(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return pd.json_normalize(data)

def stat_team(df, team_name):
    df_team = df[df['team.name'] == team_name]

    stats = {'Équipe': team_name}
    # Score équipe
    shot = df_team[df_team['type.name'] == 'Shot']

    stats['Buts'] = len(shot[shot['shot.outcome.name'] == 'Goal'])

    # Possession des équipes
    stats['Possession (%)'] = round(df_team['duration'].sum()/df['duration'].sum()*100,1)

    # Nombre de tir

    stats['Tirs totaux'] = len(shot)
    stats['Tirs cadrés'] = len(shot[shot['shot.outcome.name'].isin(['Goal', 'Saved'])])
    stats['Tirs non cadrés'] = len(shot[shot['shot.outcome.name'].isin(['Off T', 'Post', 'Wayward', 'Saved To Post'])])
    stats['Tirs contrés'] = len(shot[shot['shot.outcome.name'].isin(['Blocked'])])
    stats['xG'] = round(shot['shot.statsbomb_xg'].sum(),1)

    #Passes
    nbr_pass = df_team[df_team['type.name'] == 'Pass']

    stats['Nombre de passes'] = len(nbr_pass)

    stats['Passes réussies'] = len(nbr_pass[nbr_pass['pass.outcome.name'].isna()])
    stats['Taux passe (%)'] = round(len(nbr_pass[nbr_pass['pass.outcome.name'].isna()])/ len(nbr_pass)*100,1)

    stats['Passes longues'] = len(nbr_pass[nbr_pass['pass.length'] >= 27])
    stats['Passes courtes'] = len(nbr_pass[nbr_pass['pass.length'] < 27])


    pass_loc = nbr_pass.dropna(subset=['location'])
    stats['Passes dernier tiers'] = len(pass_loc[pass_loc['location'].apply(lambda loc: loc[0] if isinstance(loc, list) else None)>90])

    stats['Passes clés'] = nbr_pass['pass.shot_assist'].notna().sum()

    #Centres
    nbr_centre = nbr_pass[nbr_pass['pass.cross'] == True]
    centre_reussi = nbr_centre[nbr_centre['pass.outcome.name'].isna()]

    stats['Centres'] = len(nbr_centre)
    stats['Centres réussis (%)'] = round(len(centre_reussi)/len(nbr_centre)*100,1) if len(nbr_centre) > 0 else 0    

    centre_loc = nbr_centre.dropna(subset=['location'])
    centre_reu_loc = centre_reussi.dropna(subset=['location'])

    stats['Centres droite'] = len(centre_loc[centre_loc['location'].apply(lambda loc: loc[1] if isinstance(loc, list) else None)>40])
    stats['Centres gauche'] = len(centre_loc[centre_loc['location'].apply(lambda loc: loc[1] if isinstance(loc, list) else None)<40])
    stats['Centres réussis droite (%)'] = round(len(centre_reu_loc[centre_reu_loc['location'].apply(lambda loc: loc[1] if isinstance(loc, list) else None)>40])/len(centre_loc[centre_loc['location'].apply(lambda loc: loc[1] if isinstance(loc, list) else None)>40])*100,1) if len(centre_reu_loc[centre_reu_loc['location'].apply(lambda loc: loc[1] if isinstance(loc, list) else None)>40])> 0 else 0
    stats['Centres réussis gauche (%)'] = round(len(centre_reu_loc[centre_reu_loc['location'].apply(lambda loc: loc[1] if isinstance(loc, list) else None)<40])/len(centre_loc[centre_loc['location'].apply(lambda loc: loc[1] if isinstance(loc, list) else None)<40])*100,1) if len(centre_reu_loc[centre_reu_loc['location'].apply(lambda loc: loc[1] if isinstance(loc, list) else None)<40]) > 0 else 0

    # Coup de pied arrêté
    nbr_corner = nbr_pass[nbr_pass['pass.type.name'] == 'Corner']
    nbr_coupfranc = nbr_pass[nbr_pass['pass.type.name'] == 'Free Kick']

    stats['Corners'] = len(nbr_corner)
    stats['Coup Franc'] = len(nbr_coupfranc) + len(shot[shot['shot.type.name'] == 'Free Kick'])

    #Hors jeu

    nbr_horsjeu = df_team[df_team['type.name'] == 'Offside']

    stats['Hors-jeu'] = len(nbr_horsjeu)

    #Fautes
    nbr_faute = df_team[df_team['type.name'] == 'Foul Committed']
    foul_won = df[df['type.name'] == 'Foul Won']

    stats['Fautes commises'] = len(nbr_faute)
    if 'foul_committed.card.name' in df_team.columns:
        stats['Cartons jaunes'] = len(df_team[df_team['foul_committed.card.name'] == 'Yellow Card'])
        stats['Cartons rouges'] = len(df_team[df_team['foul_committed.card.name'].isin(['Red Card', 'Second Yellow'])])
    else:
        stats['Cartons jaunes'] = 0
        stats['Cartons rouges'] = 0
    stats['Fautes subies'] = len(foul_won)

    if 'foul_won.penalty' in df_team.columns:
        nbr_penalty = df_team[df_team['foul_won.penalty'] == True]
        stats['Penalty'] = len(nbr_penalty)
    else:
        stats['Penalty'] = 0

    #Duels
    nbr_duel = df_team[df_team['type.name'] == 'Duel']
    nbr_duel_nettoyé = nbr_duel[nbr_duel['duel.outcome.name'].notna()]
    nbr_duelaerienper = len(nbr_duel[nbr_duel['duel.type.name'] == 'Aerial Lost'])
    nbr_duelaeriengag = len(df_team[(df_team.get('pass.aerial_won', pd.Series([False]*len(df_team))) == True) | (df_team.get('clearance.aerial_won', pd.Series([False]*len(df_team))) == True) | (df_team.get('shot.aerial_won', pd.Series([False]*len(df_team))) == True)])
    tacle = nbr_duel[nbr_duel['duel.type.name'] == 'Tackle']
    tacle_réussis = tacle[tacle['duel.outcome.name'].isin(['Success In Play', 'Won', 'Success Out'])]
    tacle_réussie_ratio = round(len(tacle_réussis)/len(tacle)*100,1) if len(tacle) > 0 else 0

    stats['Duel totaux'] = len(nbr_duel)
    stats['Duel gagnés (%)'] = round(len(nbr_duel_nettoyé[nbr_duel_nettoyé['duel.outcome.name'].isin(['Won','Success','Success In Play', 'Success Out'])])/len(nbr_duel_nettoyé)*100,1) if len(nbr_duel_nettoyé[nbr_duel_nettoyé['duel.outcome.name'].isin(['Won','Success','Success In Play', 'Success Out'])]) > 0 else 0

    stats['Duel aériens'] = nbr_duelaeriengag + nbr_duelaerienper
    stats['Duel aérien gagnés (%)'] = round(nbr_duelaeriengag/(nbr_duelaeriengag + nbr_duelaerienper)*100,1) if nbr_duelaeriengag > 0 else 0
    
    stats['Nombre de tacle'] = len(tacle)
    stats['Nombre de tacle réussi'] = len(tacle_réussis)
    stats['Pourcentage passe réussi (%)'] = tacle_réussie_ratio

    #Dribbles
    nbr_dribble = df_team[df_team['type.name'] == 'Dribble']
    nbr_dribblesucc = nbr_dribble[nbr_dribble['dribble.outcome.name'] == 'Complete']

    stats['Dribbles tentés'] = len(nbr_dribble) 
    stats['Dribbles réussis'] = len(nbr_dribblesucc)
    stats['Dribbles réussis (%)'] = round(len(nbr_dribblesucc)/len(nbr_dribble)*100,1) if len(nbr_dribblesucc) > 0 else 0

    #Actions défensives
    nbr_interception = df_team[df_team['interception.outcome.name'].isin(['Success', 'Success In Play', 'Success Out', 'Won'])]
    nbr_clear = df_team[df_team['type.name'] == 'Clearance']
    recuperation_total = df_team[df_team['type.name'] == 'Ball Recovery']
    recuperation_reussi = recuperation_total[recuperation_total['ball_recovery.recovery_failure'].isna()]
   
    stats['Interceptions'] = len(nbr_interception)
    stats['Dégagement'] = len(nbr_clear)

    if 'block.deflection' in df_team.columns:
        nbr_block = df_team[df_team['block.deflection'] == True]
        stats['Bloc'] = len(nbr_block)
    else :
        stats['Bloc'] = 0
    
    stats['Récupération'] = len(recuperation_reussi)
    
    #Arrêts
    nbr_save = df_team[df_team['goalkeeper.type.name'] == 'Shot Saved']
    df_team_adv = df[df['team.name'] != team_name]
    tirs_encaisse = df_team_adv[df_team_adv['type.name'] == 'Shot']
    tirs_cadre_encaisse = tirs_encaisse[tirs_encaisse['shot.outcome.name'].isin(['Goal', 'Saved'])]
    buts_encaisse = tirs_encaisse[tirs_encaisse['shot.outcome.name'] == 'Goal']
    clean_sheet = 0 if len(buts_encaisse) > 0 else 1
    
    stats['Arrêts'] = len(nbr_save)
    stats['Tirs subis'] = len(tirs_encaisse)
    stats['Tirs cadrés subis'] = len(tirs_cadre_encaisse)
    stats['Buts encaissés'] = len(buts_encaisse)
    stats['Clean sheet'] = clean_sheet

    return stats

def stat_match(filepath):
    df = load_match(filepath)
    equipes = df[df['type.name'] == 'Starting XI']['team.name'].tolist()

    match_id = Path(filepath).stem
    
    resultat =[]
    for equipe in equipes :
        stats = stat_team(df, equipe)
        stats['match_ID'] = match_id
        resultat.append(stats)

    return resultat

def stat_tous_matchs(dossier_path):
    dossier = Path(dossier_path)
    fichiers = list(dossier.glob('*.json'))

    tous_resultat = []

    for i, fichier in enumerate(fichiers, 1):
        print(f'Match {i}/{len(fichiers)}')
        try:
            resultats = stat_match(fichier)
            tous_resultat.extend(resultats)
        except Exception as e:
            print (f'Erreur sur {fichier.name}: {e}')

    return pd.DataFrame(tous_resultat)

def stat_player(df, player_name, filepath):
    df_pass = df[df['type.name'] == 'Pass']
    df_player = df[df['player.name'] == player_name]
    df_team = df_player['team.name'].unique()
    team_name = df_team[0]
    poste = df_player['position.name'].unique()[0]
    info_temps = temps_de_jeu(df, player_name)

    player_id = df[df['player.name'] == player_name]['player.id'].values[0]
    match_id = Path(filepath).stem

    stats = {'Joueurs' : player_name, 'Equipe' : team_name, 'Poste': poste, 'Joueur Id': player_id, 'Match id': match_id}
    #Temps de jeu
    stats['Titulaire'] = 1 if info_temps['Titulaire'] else 0
    stats['Temps de jeu'] = info_temps['Temps de jeu'] 

    #Passes
    nbre_passes = df_player[df_player['type.name'] == 'Pass']
    passes_reussies = nbre_passes[nbre_passes['pass.outcome.name'].isna()]
    passes_pourcentage = round(len(passes_reussies)/len(nbre_passes)*100,1) if len(nbre_passes) > 0 else 0
    
    stats['Passes'] = len(nbre_passes)
    stats['Passes réussies'] = len(passes_reussies)
    stats['Passes réussies (%)'] = passes_pourcentage

    right_foot_pass = nbre_passes[nbre_passes['pass.body_part.name'] == 'Right Foot']
    left_foot_pass = nbre_passes[nbre_passes['pass.body_part.name'] == 'Left Foot']
    head_pass = nbre_passes[nbre_passes['pass.body_part.name'] == 'Head']
    right_foot_pass_success = right_foot_pass[right_foot_pass['pass.outcome.name'].isna()]
    left_foot_pass_success = left_foot_pass[left_foot_pass['pass.outcome.name'].isna()]
    head_pass_success = head_pass[head_pass['pass.outcome.name'].isna()]

    stats['Passes pied droit'] = len(right_foot_pass)
    stats['Passes réussies pied droit'] = len(right_foot_pass_success)
    stats['Passes pied gauche'] = len(left_foot_pass)
    stats['Passes réussies pied gauche'] = len(left_foot_pass_success)
    stats['Passes tête'] = len(head_pass)
    stats['Passes réussies tête'] = len(head_pass_success)

    if 'pass.goal-assist' in df_player.columns:
        passes_décisives = nbre_passes[nbre_passes['pass.goal-assist'] == True]
        stats['Passes décisives'] = len(passes_décisives)
    else: 
        stats['Passes décisives'] = 0

    passes_courte = nbre_passes[nbre_passes['pass.length']< 40]
    passes_longues = nbre_passes[nbre_passes['pass.length'] >= 40]
    passes_courtes_réussies = passes_courte[passes_courte['pass.outcome.name'].isna()]
    passes_longues_réussies = passes_longues[passes_longues['pass.outcome.name'].isna()]

    stats['Passes courtes'] = len(passes_courte)
    stats['Passes longues'] = len(passes_longues)
    stats['Passes courtes réussies'] = len(passes_courtes_réussies)
    stats['Passes longues réussies'] = len(passes_longues_réussies)

    passe_courte_pied_droit = passes_courte[passes_courte['pass.body_part.name'] == 'Right Foot']
    passe_courte_pied_gauche = passes_courte[passes_courte['pass.body_part.name'] == 'Left Foot']
    passe_longue_pied_droit = passes_longues[passes_longues['pass.body_part.name'] == 'Right Foot']
    passe_longue_pied_gauche = passes_longues[passes_longues['pass.body_part.name'] == 'Left Foot']

    stats['Passes courtes pied droit'] = len(passe_courte_pied_droit)
    stats['Passes courtes pied gauche'] = len(passe_courte_pied_gauche)
    stats['Passes longues pied droit'] = len(passe_longue_pied_droit)
    stats['Passes longues pied gauche'] = len(passe_longue_pied_gauche)

    passe_courte_reussi_d = passe_courte_pied_droit[passe_courte_pied_droit['pass.outcome.name'].isna()]
    passe_courte_reussi_g = passe_courte_pied_gauche[passe_courte_pied_gauche['pass.outcome.name'].isna()]
    passe_longue_reussi_d = passe_longue_pied_droit[passe_longue_pied_droit['pass.outcome.name'].isna()]
    passe_longue_reussi_g = passe_longue_pied_gauche[passe_longue_pied_gauche['pass.outcome.name'].isna()]

    stats['Passes courtes réussies pied droit'] = len(passe_courte_reussi_d)
    stats['Passes courtes réussies pied gauche'] = len(passe_courte_reussi_g)
    stats['Passes longues réussies pied droit'] = len(passe_longue_reussi_d)
    stats['Passes longues réussies pied gauche'] = len(passe_longue_reussi_g)

    pct_passe_courte_droit = round(len(passe_courte_reussi_d)/len(passe_courte_pied_droit)*100,1) if len(passe_courte_pied_droit) else 0
    pct_passe_courte_gauche = round(len(passe_courte_reussi_g)/len(passe_courte_pied_gauche)*100,1) if len(passe_courte_pied_gauche) else 0
    pct_passe_longue_droit = round(len(passe_longue_reussi_d)/len(passe_longue_pied_droit)*100,1) if len(passe_longue_pied_droit) else 0
    pct_passe_longue_gauche = round(len(passe_longue_reussi_g)/len(passe_longue_pied_gauche)*100,1) if len(passe_longue_pied_gauche) else 0 

    stats['Passe courte pied droit pourcentage'] = pct_passe_courte_droit
    stats['Passe courte pied gauche pourcentage'] = pct_passe_courte_gauche
    stats['Passe longue pied droit pourcentage'] = pct_passe_longue_droit
    stats['Passe longue pied gauche pourcentage'] = pct_passe_longue_gauche

    passe_cle = nbre_passes[nbre_passes['pass.shot_assist'] == True]

    stats['Passe clé'] = len(passe_cle) 

    #Cartons
    cartons_jaunes = 0 
    if 'foul_committed.card.name' in df_player.columns:
        cartons_jaunes += len(df_player[df_player['foul_committed.card.name'] == 'Yellow Card'])
    if 'bad_behaviour.card.name' in df_player.columns:
        cartons_jaunes += len(df_player[df_player['bad_behaviour.card.name'] == 'Yellow Card'])

    cartons_rouges = 0
    if 'foul_committed.card.name' in df_player.columns:
        cartons_rouges += len(df_player[df_player['foul_committed.card.name'].isin(['Second Yellow', 'Red Card'])])
    if 'bad_behaviour.card.name' in df_player.columns:
        cartons_rouges += len(df_player[df_player['bad_behaviour.card.name'].isin(['Second Yellow', 'Red Card'])])

    stats['Cartons jaunes'] = cartons_jaunes
    stats['Cartons rouges'] = cartons_rouges

    #Penalty provoqués
    penalty_provoque = 0
    if 'foul_won.penalty' in df_player.columns:
        penalty_provoque += len(df_player[df_player['foul_won.penalty'] == True])
    
    stats['Penalty provoqués'] = penalty_provoque

    if poste == 'Goalkeeper':
        
        #Nombre d'arrêts
        arrets = df_player[df_player['goalkeeper.type.name'] == 'Shot Saved']
        stats['Nombre arrêts'] = len(arrets)

        #Position gardien lors des frappes

        tirs = df[df['type.name'] == 'Shot']
        position = []
        for tir in tirs['shot.freeze_frame'].dropna():
            for joueur in tir:
                if (joueur['position']['name'] == 'Goalkeeper') & (joueur['player']['name'] == player_name):
                    position.append(joueur['location'])
        stats['Position gardien'] = position

        #Nombre de tirs subis
        stats['Nombre de tirs subis'] = len(position)

        #Position arrêt
        plongeon = arrets[arrets['goalkeeper.technique.name'] == 'Diving']
        debout = arrets[arrets['goalkeeper.technique.name'] == 'Standing']

        stats['Plongeon'] = len(plongeon)
        stats['Debout'] = len(debout)

        #Partie du corps
        arrets_pieds = arrets[arrets['goalkeeper.body_part.name'].isin(['Left Foot', 'Right Foot'])]
        arrets_mains = arrets[arrets['goalkeeper.body_part.name'].isin(['Left Hand', 'Right Hand', 'Both Hands'])]
        arrets_poitrine = arrets[arrets['goalkeeper.body_part.name'] == 'Chest']
        arrets_tete = arrets[arrets['goalkeeper.body_part.name'] == 'Head']
    
        stats['Arrets du pied'] = len(arrets_pieds)
        stats['Arrets des mains'] = len(arrets_mains)
        stats['Arrets poitrine'] = len(arrets_poitrine)
        stats['Arrets tête'] = len(arrets_tete)

        #Dégagement des poings
        degagement_poing = df_player[df_player['goalkeeper.type.name'] == 'Punch']

        stats['Dégagement poings'] = len(degagement_poing)

        #Buts concédés
        buts_concede = df_player[df_player['goalkeeper.type.name'] == 'Goal Conceded']
        cleansheet = 1 if len(buts_concede) == 0 else 0

        stats['Buts concedes'] = len(buts_concede)
        stats['Clean sheet'] = cleansheet

        #Penalty
        penalty_encaisse = df_player[df_player['goalkeeper.type.name'] == 'Penalty Conceded']
        penalty_sauve = df_player[df_player['goalkeeper.type.name'] == 'Penalty Saved']

        stats['Penalty encaissé'] = len(penalty_encaisse)
        stats['Penlaty arrêté'] = len(penalty_sauve)

        #Sorti en-dehors de surface
        sorti = df_player[df_player['goalkeeper.type.name'] == 'Keeper Sweeper']

        stats['Sorti'] = len(sorti)

        #Position du ballon lorsqu'il est arrêté ou il franchit la ligne

        tirs_equipe_adverse = df[df['team.name'] != team_name]
        tirs_arretes = tirs_equipe_adverse[tirs_equipe_adverse['shot.outcome.name'].isin(['Saved', 'Saved To Post'])]
        tirs_encaisses = tirs_equipe_adverse[tirs_equipe_adverse['shot.outcome.name'] == 'Goal']

            #Transformer les coordonnées en list
        coordonne_tirs_arrete = tirs_arretes['shot.end_location'].tolist()
        coordonne_tirs_encaisses = tirs_encaisses['shot.end_location'].tolist()

            #Calcul des dimensions pour couper le but en 3 dans la longueur et 2 dans la hauteur
        gauche_but = 36.0
        droite_but = 44.0
        hauteur_but = 2.67
        hauteur_sol = 0

        centre_gauche_but = gauche_but + ((droite_but - gauche_but) / 3)
        centre_droit_but = droite_but - ((droite_but - gauche_but) / 3)
        mi_hauteur = hauteur_but / 2    

            #Position en zone des tirs arrêtés
        position_tirs_arretes_gauchebas = 0
        position_tirs_arretes_gauchehaut = 0

        position_tirs_arretes_droitehaut = 0
        position_tirs_arretes_droitebas = 0

        position_tirs_arretes_centrehaut = 0
        position_tirs_arretes_centrebas = 0

        for tir in coordonne_tirs_arrete :
            z = tir[2] if len(tir) > 2 else 0   
            if tir[1] < centre_gauche_but:
                if z > mi_hauteur:
                    position_tirs_arretes_gauchehaut += 1
                else:
                    position_tirs_arretes_gauchebas += 1
            elif tir[1] > centre_droit_but:
                if z > mi_hauteur:
                    position_tirs_arretes_droitehaut += 1
                else:
                    position_tirs_arretes_droitebas += 1
            else:
                if z > mi_hauteur:
                    position_tirs_arretes_centrehaut += 1
                else:
                    position_tirs_arretes_centrebas += 1

        stats['Arrêts zone gauche haute'] = position_tirs_arretes_gauchehaut
        stats['Arrêts zone gauche basse'] = position_tirs_arretes_gauchebas
        stats['Arrêts zone droite haute'] = position_tirs_arretes_droitehaut
        stats['Arrêts zone droite basse'] = position_tirs_arretes_droitebas
        stats['Arrêts zone centre haute'] = position_tirs_arretes_centrehaut
        stats['Arrêts zone centre basse'] = position_tirs_arretes_centrebas

            #Position en zone des tirs encaissés
        position_tirs_encaisse_gauchehaut = 0
        position_tirs_encaisse_gauchebas= 0

        position_tirs_encaisse_droitehaut = 0
        position_tirs_encaisse_droitebas= 0

        position_tirs_encaisse_centrehaut = 0
        position_tirs_encaisse_centrebas = 0

        for tir in coordonne_tirs_encaisses :
            z = tir[2] if len(tir) > 2 else 0 
            if tir[1] < centre_gauche_but:
                if z > mi_hauteur:
                    position_tirs_encaisse_gauchehaut += 1
                else:
                    position_tirs_encaisse_gauchebas += 1
            elif tir[1] > centre_droit_but:
                if z > mi_hauteur:
                    position_tirs_encaisse_droitehaut += 1
                else:
                    position_tirs_encaisse_droitebas += 1
            else:
                if z > mi_hauteur:
                    position_tirs_encaisse_centrehaut += 1
                else:
                    position_tirs_encaisse_centrebas += 1

        stats['Buts zone gauche haute'] = position_tirs_encaisse_gauchehaut
        stats['Buts zone gauche basse'] = position_tirs_encaisse_gauchebas
        stats['Buts zone droite haute'] = position_tirs_encaisse_droitehaut
        stats['Buts zone droite basse'] = position_tirs_encaisse_droitebas
        stats['Buts zone centre haute'] = position_tirs_encaisse_centrehaut
        stats['Buts zone centre basse'] = position_tirs_encaisse_centrebas

    else:

        #Centres
        centres = nbre_passes[nbre_passes['pass.cross'] == True]
        centres_reussis = centres[centres['pass.outcome.name'].isna()]
        centres_pourcentage = round(len(centres_reussis)/len(centres)*100,1) if len(centres) else 0

        stats['Centres'] = len(centres)
        stats['Centres réussis'] = len(centres_reussis)
        stats['Centres pourcentage'] = centres_pourcentage

        #Tirs
        tirs = df_player[df_player['type.name'] == 'Shot']
        tirs_pied_droit = tirs[tirs['shot.body_part.name'] == 'Right Foot']
        tirs_pied_gauche = tirs[tirs['shot.body_part.name'] == 'Left Foot']
        tirs_tete = tirs[tirs['shot.body_part.name'] == 'Head']
        tirs_autre = tirs[tirs['shot.body_part.name'] == 'Other']

        stats['Tirs'] = len(tirs)
        stats['Tirs pied droit'] = len(tirs_pied_droit)
        stats['Tirs pied gauche'] = len(tirs_pied_gauche)
        stats['Tirs tête'] = len(tirs_tete)
        stats['Tirs autre'] = len(tirs_autre)

        tirs_cadrés = tirs[tirs['shot.outcome.name'].isin(['Goal', 'Saved', 'Saved To Post'])]
        tirs_pied_droit_cadrés = tirs_pied_droit[tirs_pied_droit['shot.outcome.name'].isin(['Goal', 'Saved', 'Saved To Post'])]
        tirs_pied_gauche_cadrés = tirs_pied_gauche[tirs_pied_gauche['shot.outcome.name'].isin(['Goal', 'Saved', 'Saved To Post'])]
        tirs_tete_cadrés = tirs_tete[tirs_tete['shot.outcome.name'].isin(['Goal', 'Saved', 'Saved To Post'])]
        tirs_autre_cadrés = tirs_autre[tirs_autre['shot.outcome.name'].isin(['Goal', 'Saved', 'Saved To Post'])]
        stats['Tirs cadrés'] = len(tirs_cadrés)
        stats['Tirs cadrés pied droit'] = len(tirs_pied_droit_cadrés)
        stats['Tirs cadrés pied gauche'] = len(tirs_pied_gauche_cadrés)
        stats['Tirs cadrés tête'] = len(tirs_tete_cadrés)
        stats['Tirs cadrés autre'] = len(tirs_autre_cadrés)

        buts = tirs[tirs['shot.outcome.name'] == 'Goal']
        buts_pied_droit = buts[buts['shot.body_part.name'] == 'Right Foot']
        buts_pied_gauche = buts[buts['shot.body_part.name'] == 'Left Foot']
        buts_tete = buts[buts['shot.body_part.name'] == 'Head']
        buts_autre = buts[buts['shot.body_part.name'] == 'Other']
        stats['Buts'] = len(buts)
        stats['Buts pied droit'] = len(buts_pied_droit)
        stats['Buts pied gauche'] = len(buts_pied_gauche)
        stats['Buts tête'] = len(buts_tete)
        stats['Buts autre'] = len(buts_autre)

        xG = tirs['shot.statsbomb_xg']
        xG_total = round(xG.sum(),2)
        stats['xG'] = xG_total

        #Dribbles
        dribbles = df_player[df_player['type.name'] == 'Dribble']
        dribbles_reussis = dribbles[dribbles['dribble.outcome.name'] == 'Complete']
        dribbles_reussis_pourcentage = round(len(dribbles_reussis)/len(dribbles)*100,1) if len(dribbles) > 0 else 0
        stats['Dribbles'] = len(dribbles)
        stats['Dribbles réussis'] = len(dribbles_reussis)
        stats['Dribbles pourcentage'] = dribbles_reussis_pourcentage

        #Interception
        interception = df_player[df_player['interception.outcome.name'].isin(['Success', 'Won','Success In Play', 'Success Out'])]
        stats['Interceptions'] = len(interception)

        #Récupération
        recuperations = len(interception) + len(df_player[(df_player['type.name'] == 'Ball Recovery') & (df_player['ball_recovery.recovery_failure'].isna())])

        stats['Récupération'] = recuperations

        #Dégagements
        degagement = df_player[df_player['type.name'] == 'Clearance']

        stats['Dégagements'] = len(degagement)

        #Duels
        duels = df_player[df_player['type.name'] == 'Duel']
        duels_gagnes = duels[duels['duel.outcome.name'].isin(['Won', 'Success', 'Success In Play', 'Success Out'])]
        duels_pourcentage = round(len(duels_gagnes)/len(duels)*100,1) if len(duels) else 0

        stats['Duels'] = len(duels)
        stats['Duels gagnés'] = len(duels_gagnes)
        stats['Duels pourcentage'] = duels_pourcentage

        tacles = duels[duels['duel.type.name'] == 'Tackle']
        tacles_reussis = tacles[tacles['duel.outcome.name'].isin(['Success In Play', 'Won', 'Success Out'])]
        tacles_pourcentage = round(len(tacles_reussis)/len(tacles)*100,1) if len(tacles) else 0

        stats['Tacles'] = len(tacles)
        stats['Tacles réussis'] = len(tacles_reussis)
        stats['Tacles pourcentage'] = tacles_pourcentage

        #Duel aérien
        duel_aerien_perdu = df_player[df_player['duel.type.name'] == 'Aerial Lost']
        duel_aerien_gagne = len(df_player[df_player['pass.aerial_won'] == True]) + len(df_player[df_player['clearance.aerial_won'] == True])
        duel_aerien_total = duel_aerien_gagne + len(duel_aerien_perdu)
        duel_aerien_pourcentage = round(duel_aerien_gagne/duel_aerien_total*100,1) if len(duel_aerien_perdu) else 0

        stats['Duels aériens total'] = duel_aerien_total
        stats['Duels aériens gagnés'] = duel_aerien_gagne
        stats['Duels aériens perdus'] = len(duel_aerien_perdu)

        #Ballon perdus
        ball_perdus = len(nbre_passes[nbre_passes['pass.outcome.name'].isin(['Incomplete', 'Out', 'Pass Offside'])]) + len(dribbles[dribbles['dribble.outcome.name'] == 'Incomplete']) + len(df_player[df_player['type.name'] == 'Miscontrol']) + len(df_player[df_player['type.name'] == 'Dispossession']) + len(df_player[df_player['type.name'] == 'Error'])

        stats['Ballons perdus'] = ball_perdus

        #Hors-jeu
        ballon_recu = df_pass[df_pass['pass.recipient.name'] == player_name]
        offside = ballon_recu[ballon_recu['pass.outcome.name'] == 'Pass Offside']
    
        stats['Hors-jeu'] = len(offside)

        #Fautes
        fautes_provoques = df_player[df_player['type.name'] == 'Foul Won']
        fautes_commises = df_player[df_player['type.name'] == 'Foul Committed']

        stats['Fautes provoquées'] = len(fautes_provoques)
        stats['Fautes commises'] = len(fautes_commises)

        #Nombre de ballon joué
        nbr_ballon_joue = len(interception) + len(df_player[df_player['type.name'] == 'Ball Recovery']) + len(df[df['pass.recipient.name'] == player_name])

        stats['Ballons joués'] = nbr_ballon_joue

    return stats

def stat_tous_player (dossier_path):
    dossier = Path(dossier_path)
    fichiers = list(dossier.glob('*.json'))

    tous_joueurs = []
    total = len(fichiers)
    for i, fichier in enumerate(fichiers, 1) :
        print(f'Match {i}/{total}')
        try:
            df = load_match(fichier)
            joueurs = df['player.name'].dropna().unique().tolist() 
            for joueur in joueurs:
                try:
                    joueur_stat = stat_player(df, joueur, fichier)
                    tous_joueurs.append(joueur_stat)
                except Exception as e:
                    print(f'Erreur sur le joueur {joueur}: {e}')
        except Exception as e:
            print(f'Erreur sur le fichier {fichier.name}: {e}')
    return pd.DataFrame(tous_joueurs)

def resultat_match(fichier_path):
    with open(fichier_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.json_normalize(data)

    match_id = Path(fichier_path).stem

    equipes = df[df['type.name'] == 'Starting XI']['team.name'].tolist()

    equipe_domicile = equipes[0]
    equipe_exterieur = equipes[1]

    tirs = df[df['type.name'] == 'Shot']
    buts = tirs[tirs['shot.outcome.name'] == 'Goal']

    buts_domicile = len(buts[buts['team.name'] == equipe_domicile])
    buts_exterieur = len(buts[buts['team.name'] == equipe_exterieur])

    return {'match ID' : match_id, 'equipe_domicile': equipe_domicile, 'equipe_exterieur': equipe_exterieur, 'buts_domicile': buts_domicile, 'buts_exterieur': buts_exterieur}

def charger_tous_les_matchs(dossier_path):
    dossier = Path(dossier_path)
    fichiers = list(dossier.glob('*.json'))
    
    resultats = []
    erreurs = []

    for i, fichier in enumerate(fichiers):
        if 'checkpoint' in str(fichier):
            continue
        try:
            resultat = resultat_match(fichier)
            resultats.append(resultat)
        except Exception as e:
            erreurs.append({'fichier': fichier.name, 'erreur': str(e)})

    print(f'{len(resultats)} matchs chargés, {len(erreurs)} erreurs')

    if erreurs:
        print(f"Fichiers avec erreurs : {[e['fichier'] for e in erreurs]}")

    return pd.DataFrame(resultats)

def calcul_classement(df_matchs):
    stats = {}

    for i, match in df_matchs.iterrows():
        equipe_dom = match['equipe_domicile']
        equipe_ext = match['equipe_exterieur']
        buts_dom = match['buts_domicile']
        buts_ext = match['buts_exterieur']

        for equipe in [equipe_dom, equipe_ext]:
            if equipe not in stats:
                stats[equipe] = {
                    'Equipe': equipe,
                    'Pts' : 0,
                    'J': 0,
                    'V': 0,
                    'N': 0,
                    'D': 0,
                    'BP': 0,
                    'BC': 0
                }
        stats[equipe_dom]['J'] += 1
        stats[equipe_ext]['J'] += 1

        stats[equipe_dom]['BP'] += buts_dom
        stats[equipe_dom]['BC'] += buts_ext
        stats[equipe_ext]['BP'] += buts_ext
        stats[equipe_ext]['BC'] += buts_dom

        if buts_dom > buts_ext:
            stats[equipe_dom]['Pts'] += 3
            stats[equipe_dom]['V'] += 1
            stats[equipe_ext]['D'] += 1
        elif buts_dom < buts_ext:
            stats[equipe_ext]['Pts'] += 3
            stats[equipe_ext]['V'] += 1
            stats[equipe_dom]['D'] += 1
        else:
            stats[equipe_dom]['Pts'] += 1
            stats[equipe_ext]['Pts'] += 1
            stats[equipe_dom]['N'] += 1
            stats[equipe_ext]['N'] += 1

    df_classement = pd.DataFrame(stats.values())

    df_classement['Diff'] = df_classement['BP'] - df_classement['BC']
    
    df_classement = df_classement.sort_values(by=['Pts', 'Diff', 'BP'], ascending = False)

    df_classement = df_classement.reset_index(drop=True)
    df_classement.index = df_classement.index + 1 

    return df_classement

def temps_de_jeu(df, player_name):
    formations =df[df['type.name'] == 'Starting XI']
    titulaires = formations['tactics.lineup']
    remplacement = df[df['type.name'] == 'Substitution']
    entree = remplacement[remplacement['substitution.replacement.name'] == player_name]

    temps = 0
    titulaire = False
    for equipes in titulaires:
        for joueur in equipes:
        
            #Vérifier si le joueur est titulaire ou non
            if joueur['player']['name'] == player_name:
                titulaire = True
                sorti = remplacement[remplacement['player.name'] == player_name]

                #Vérifier si le joueur titulaire sort
                if len(sorti)>0 :
                    temps = sorti['minute'].values[0]     
                else : 
                    temps = df['minute'].max()
                break
        if titulaire:
            break
            
    #Si pas titulaire vérifier si il rentre en jeu
    if not titulaire and len(entree)>0:
        sorti = remplacement[remplacement['player.name'] == player_name]

        #Vérifier s'il sort
        if len(sorti)>0:
            temps = sorti['minute'].values[0] - entree['minute'].values[0]
        else:
            temps = df['minute'].max() - entree['minute'].values[0]
        
    return {'Titulaire': titulaire, 'Temps de jeu': temps}

def passes_matchs(filepath):
    df = load_match(filepath)
    match_id = Path(filepath).stem

    passes = df[df['type.name'] == 'Pass'].copy()

    passes['x depart'] = passes['location'].apply(lambda loc: loc[0])
    passes['y depart'] = passes['location'].apply(lambda loc: loc[1])
    passes['x arrive'] = passes['pass.end_location'].apply(lambda loc: loc[0])
    passes['y arrive'] = passes['pass.end_location'].apply(lambda loc: loc[1])
    passes['reussie'] = passes['pass.outcome.name'].isna()
    passes['match id'] = match_id

    return passes[['match id', 'player.name', 'player.id', 'team.name', 'minute', 'x depart', 'x arrive', 'y depart', 'y arrive', 'reussie', 'pass.length', 'pass.body_part.name']]

def passes_tous_matchs(dossier_path):
    dossier = Path(dossier_path)
    fichiers = list(dossier.glob('*.json'))

    toutes_passes = []
    for i, fichier in enumerate(fichiers, 1):
        print(f'Match {i}/{len(fichiers)}')
        try:
            passes = passes_matchs(fichier)
            toutes_passes.append(passes)
        except Exception as e:
            print(f'Erreur sur le fichier {fichier.name}: {e}')
    return pd.concat(toutes_passes, ignore_index=True)

#Rajouter fonctions pour emplacement des tirs 

#HeatMap de chaque joueur

#Réseaux de passe

#Pressing des joueurs
