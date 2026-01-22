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

    for fichier in fichiers:
        try:
            resultats = stat_match(fichier)
            tous_resultat.extend(resultats)
        except Exception as e:
            print (f'Erreur sur {fichier.name}: {e}')

    return pd.DataFrame(tous_resultat)

def stat_player(df, player_name):
    df_player = df[df['player.name'] == player_name]
    df_team = df_player['team.name'].unique()
    team_name = df_team[0]

    stats = {'Joueurs' : player_name, 'Equipe' : team_name}

    #Passes
    nbre_passes = df_player[df_player['type.name'] == 'Pass']
    passes_reussies = nbre_passes[nbre_passes['pass.outcome.name'].isna()]
    passes_pourcentage = round(len(passes_reussies)/len(nbre_passes)*100,1) if len(nbre_passes) > 0 else 0
    
    stats['Passes'] = len(nbre_passes)
    stats['Passes réussies'] = len(passes_reussies)
    stats['Passes réussies (%)'] = len(passes_pourcentage)

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
        print(0)

    passes_courte = nbre_passes[nbre_passes['pass.length']< 40]
    passes_longues = nbre_passes[nbre_passes['pass.length'] >= 40]
    passes_courtes_réussies = passes_courte[passes_courte['pass.outcome.name'].isna()]
    passes_longues_réussies = passes_longues[passes_longues['pass.outcome.name'].isna()]

    stats['Passes courtes'] = len(passes_courte)
    stats['Passes longues'] = len(passes_longues)
    stats['Passes courtes réussies'] = len(passes_courtes_réussies)
    stats['Passes longues réussies'] = len(passes_longues_réussies)

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

    #Duels
    
    return stats
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
