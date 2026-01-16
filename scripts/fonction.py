import pandas as pd
import json 
import glob
import os

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
    stats['Fautes commises'] = len(nbr_faute)

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

    stats['Duel totaux'] = len(nbr_duel)
    stats['Duel gagnés (%)'] = round(len(nbr_duel_nettoyé[nbr_duel_nettoyé['duel.outcome.name'].isin(['Won','Success','Success In Play', 'Success Out'])])/len(nbr_duel_nettoyé)*100,1) if len(nbr_duel_nettoyé[nbr_duel_nettoyé['duel.outcome.name'].isin(['Won','Success','Success In Play', 'Success Out'])]) > 0 else 0

    stats['Duel aériens'] = nbr_duelaeriengag + nbr_duelaerienper
    stats['Duel aérien gagnés (%)'] = round(nbr_duelaeriengag/(nbr_duelaeriengag + nbr_duelaerienper)*100,1) if nbr_duelaeriengag > 0 else 0
    
    #Dribbles
    nbr_dribble = df_team[df_team['type.name'] == 'Dribble']
    nbr_dribblesucc = nbr_dribble[nbr_dribble['dribble.outcome.name'] == 'Complete']

    stats['Dribbles tentés'] = len(nbr_dribble) 
    stats['Dribbles réussis'] = len(nbr_dribblesucc)
    stats['Dribbles réussis (%)'] = round(len(nbr_dribblesucc)/len(nbr_dribble)*100,1) if len(nbr_dribblesucc) > 0 else 0

    #Actions défensives
    nbr_interception = df_team[df_team['interception.outcome.name'].isin(['Success', 'Success In Play', 'Success Out', 'Won'])]
    nbr_clear = df_team[df_team['type.name'] == 'Clearance']
   

    stats['Interceptions'] = len(nbr_interception)
    stats['Dégagement'] = len(nbr_clear)

    if 'block.deflection' in df_team.columns:
        nbr_block = df_team[df_team['block.deflection'] == True]
        stats['Bloc'] = len(nbr_block)
    else :
        stats['Bloc'] = 0
        
    #Arrêts
    nbr_save = df_team[df_team['goalkeeper.type.name'] == 'Shot Saved']

    stats['Arrêts'] = len(nbr_save)

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

    df_classment=df_classement.reset_index(drop=True)
    df_classement = df_classement.index + 1 

    return df_classement