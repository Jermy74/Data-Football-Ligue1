### Création de différentes fonctions pour calculer les statistiques collectives des équipes
import pandas as pd
from utils import load_match
from pathlib import Path


# Fonction pour calculer les tirs des équipes
def tirs_equipe(df_team):
    shot = df_team[df_team['type.name'] == 'Shot']

    stats = {}
    stats['Buts'] =  len(shot[shot['shot.outcome.name'] == 'Goal'])

    stats['Tirs totaux'] = len(shot)
    stats['Tirs non cadrés'] = len(shot[shot['shot.outcome.name'].isin(['Off T', 'Post', 'Wayward', 'Saved To Post'])])
    stats['Tirs cadrés'] = len(shot[shot['shot.outcome.name'].isin(['Saved', 'Goal'])])
    stats['Tirs contrés'] = len(shot[shot['shot.outcome.name'] == 'Blocked'])

    stats['xG'] = round(shot['shot.statsbomb_xg'].sum(),1)

    return stats

# Fonction pour calculer les passes des équipes
def passes_equipe(df_team):
    nbr_pass = df_team[df_team['type.name'] == 'Pass']

    stats = {}

    stats['Nombre de passes'] = len(nbr_pass)

    stats['Passes réussies'] = len(nbr_pass[nbr_pass['pass.outcome.name'].isna()])
    stats['Taux passe (%)'] = round(len(nbr_pass[nbr_pass['pass.outcome.name'].isna()])/ len(nbr_pass)*100,1)

    stats['Passes longues'] = len(nbr_pass[nbr_pass['pass.length'] >= 27])
    stats['Passes courtes'] = len(nbr_pass[nbr_pass['pass.length'] < 27])


    pass_loc = nbr_pass.dropna(subset=['location'])
    stats['Passes dernier tiers'] = len(pass_loc[pass_loc['location'].apply(lambda loc: loc[0] if isinstance(loc, list) else None)>90])

    stats['Passes clés'] = nbr_pass['pass.shot_assist'].notna().sum()

    return stats

# Fonction pour calculer la possession des équipes
def possession_equipe(df_team, df):
    stats = {}

    stats['Possession (%)'] = round(df_team['duration'].sum()/df['duration'].sum()*100,1)

    return stats

# Fonction pour calculer les centres des équipes
def centres_equipes(df_team):
    stats = {}


    nbr_pass = df_team[df_team['type.name'] == 'Pass']
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

    return stats

# Fonction pour calculer les cpa des équipes
def cpa_equipe(df_team):
    stats = {}

    nbr_pass = df_team[df_team['type.name'] == 'Pass']
    nbr_shot = df_team[df_team['type.name'] == 'Shot']
    nbr_corner = nbr_pass[nbr_pass['pass.type.name'] == 'Corner']
    nbr_coupfranc = nbr_pass[nbr_pass['pass.type.name'] == 'Free Kick']

    stats['Corners'] = len(nbr_corner)
    stats['Coup Franc'] = len(nbr_coupfranc) + len(nbr_shot[nbr_shot['shot.type.name'] == 'Free Kick'])
    
    return stats

# Fonction pour calculer les hors-jeu des équipes
def horsjeu_equipe(df_team):
    stats = {}

    nbr_horsjeu = df_team[df_team['type.name'] == 'Offside']

    stats['Hors-jeu'] = len(nbr_horsjeu)

    return stats

# Fonction pour calculer les fautes des équipes à voir
def fautes_equipe(df_team, df):
    stats = {}

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

    return stats

# Fonction pour calculer les duels des équipes
def duels_equipe(df_team):
    stats = {}

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
    stats['Pourcentage tacle réussi (%)'] = tacle_réussie_ratio

    return stats

# Fonction pour calculer les dribbles des équipes
def dribbles_equipe(df_team):
    stats = {}
    
    nbr_dribble = df_team[df_team['type.name'] == 'Dribble']
    nbr_dribblesucc = nbr_dribble[nbr_dribble['dribble.outcome.name'] == 'Complete']

    stats['Dribbles tentés'] = len(nbr_dribble) 
    stats['Dribbles réussis'] = len(nbr_dribblesucc)
    stats['Dribbles réussis (%)'] = round(len(nbr_dribblesucc)/len(nbr_dribble)*100,1) if len(nbr_dribblesucc) > 0 else 0

    return stats

# Fonction pour calculer les actions défensive des équipes
def actions_def_equipe(df_team):
    stats = {}

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

    return stats

# Fonction pour calculer les arrêts des équipes
def arret_equipe(df_team, df, team_name):
    stats = {}

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

# Fonction pour savoir si le match est à domicile ou l'extérieur
def lieu_equipe(df, team_name):
    stats = {}

    lieu = 'domicile' if df['team.name'].unique()[0] == team_name else 'exterieur'

    stats['Domicile ou exterieur'] = lieu

    return stats

# Fonction qui va appeler les autres fonctions pour tout regrouper
def stats_equipe(df, team_name):
    df_team = df[df['team.name'] == team_name]

    stats = {'Équipe' : team_name}
    stats.update(possession_equipe(df_team,df))
    stats.update(tirs_equipe(df_team))
    stats.update(passes_equipe(df_team))
    stats.update(centres_equipes(df_team))
    stats.update(cpa_equipe(df_team))
    stats.update(horsjeu_equipe(df_team))
    stats.update(fautes_equipe(df_team, df))
    stats.update(duels_equipe(df_team))
    stats.update(dribbles_equipe(df_team))
    stats.update(actions_def_equipe(df_team))
    stats.update(arret_equipe(df_team, df, team_name))
    stats.update(lieu_equipe(df, team_name))

    return stats

# Fonction pour parcourir le fichier contenant les équipes et d'appeler la fonction stats_equipe
def stats_match(filepath):
    df = load_match(filepath)
    equipes = df[df['type.name'] == 'Starting XI']['team.name'].tolist()

    match_id = Path(filepath).stem

    resultat = []
    for equipe in equipes :
        stats = stats_equipe(df, equipe)
        stats['match ID'] = match_id
        resultat.append(stats)

    return resultat

# Fonction pour parcourir tout le dossier contenant les fichiers et appeler la fonction stats_match
def stats_tous_match(dossier_path):
    dossier = Path(dossier_path)
    fichiers = list(dossier.glob('*.json'))

    tous_resultat = []

    for i, fichier in enumerate(fichiers, 1):
        print(f'Match {i}/{len(fichiers)}')
        try:
            resultats = stats_match(fichier)
            tous_resultat.extend(resultats)
        except Exception as e:
            print(f'Erreur sur {fichier.name}: {e}')
    
    return pd.DataFrame(tous_resultat)

