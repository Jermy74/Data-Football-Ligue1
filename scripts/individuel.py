### Création de différentes fonction pour calculer les stats individuelles des joueurs
import pandas as pd
from pathlib import Path
from utils import load_match

# Fonction pour calculer le temps de jeu du joueur 
def temps_de_jeu(df, player_name):
    stats = {}

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

    stats['Titulaire'] = 1 if titulaire else 0
    stats['Temps de jeu'] = temps

    return stats
    
# Fonction pour calculer les passes du joueur
def passes_indiv(df_player):
    stats = {}
    
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

    if 'pass.goal_assist' in df_player.columns:
        passes_décisives = nbre_passes[nbre_passes['pass.goal_assist'] == True]
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

    return stats

# Fonction pour calculer le nombre de cartons du joueur
def cartons_indiv(df_player):
    stats = {}

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

    return stats

# Fonction pour calculer le nombre de penalty provoqué du joueur
def penalty_provoque_indiv(df_player):
    stats = {}

    penalty_provoque = 0
    if 'foul_won.penalty' in df_player.columns:
        penalty_provoque += len(df_player[df_player['foul_won.penalty'] == True])
    
    stats['Penalty provoqués'] = penalty_provoque

    return stats

# Fonction pour calculer le nombre de centre par joueur
def centres_indiv(df_player):
    stats = {}

    nbre_passes = df_player[df_player['type.name'] == 'Pass']
    centres = nbre_passes[nbre_passes['pass.cross'] == True]
    centres_reussis = centres[centres['pass.outcome.name'].isna()]
    centres_pourcentage = round(len(centres_reussis)/len(centres)*100,1) if len(centres) else 0

    stats['Centres'] = len(centres)
    stats['Centres réussis'] = len(centres_reussis)
    stats['Centres pourcentage'] = centres_pourcentage

    return stats

# Fonction pour calculer le nombre de tirs du joueur
def tirs_indiv(df_player):
    stats = {}

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

    return stats

# Fonction pour calculer le nombre de dribble du joueur
def dribbles_indiv(df_player):
    stats = {}

    dribbles = df_player[df_player['type.name'] == 'Dribble']
    dribbles_reussis = dribbles[dribbles['dribble.outcome.name'] == 'Complete']
    dribbles_reussis_pourcentage = round(len(dribbles_reussis)/len(dribbles)*100,1) if len(dribbles) > 0 else 0

    stats['Dribbles'] = len(dribbles)
    stats['Dribbles réussis'] = len(dribbles_reussis)
    stats['Dribbles pourcentage'] = dribbles_reussis_pourcentage

    return stats

# Fonction pour calculer le nombre d'interception du joueur
def interception_indiv(df_player):
    stats = {}

    interception = df_player[df_player['interception.outcome.name'].isin(['Success', 'Won','Success In Play', 'Success Out'])]
    stats['Interceptions'] = len(interception)

    return stats

# Fonction pour calculer le nombre de récupération du joueur
def recuperation_indiv(df_player):
    stats = {}
    interception = df_player[df_player['interception.outcome.name'].isin(['Success', 'Won','Success In Play', 'Success Out'])]
    recuperations = len(interception) + len(df_player[(df_player['type.name'] == 'Ball Recovery') & (df_player['ball_recovery.recovery_failure'].isna())])
    stats['Récupération'] = recuperations

    return stats

# Fonction pour calculer le nombre de dégagement du joueur
def degagement_indiv(df_player):
    stats = {}

    degagement = df_player[df_player['type.name'] == 'Clearance']
    stats['Dégagements'] = len(degagement)

    return stats

# Fonction pour calculer le nombre de duel du joueur
def duels_indiv(df_player):
    stats = {}

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
    
    return stats

# Fonction pour calculer les nombre de duel aérien du joueur
def duels_aerien_indiv(df_player):
    stats = {}

    duel_aerien_perdu = df_player[df_player['duel.type.name'] == 'Aerial Lost']
    duel_aerien_gagne = len(df_player[df_player['pass.aerial_won'] == True]) + len(df_player[df_player['clearance.aerial_won'] == True])
    duel_aerien_total = duel_aerien_gagne + len(duel_aerien_perdu)

    stats['Duels aériens total'] = duel_aerien_total
    stats['Duels aériens gagnés'] = duel_aerien_gagne
    stats['Duels aériens perdus'] = len(duel_aerien_perdu)

    return stats

# Fonction pour calculer le nombre de ballon perdus du joueur
def ballons_perdus_indiv(df_player):
    stats = {}

    dribbles = df_player[df_player['type.name'] == 'Dribble']
    nbre_passes = df_player[df_player['type.name'] == 'Pass']
    ball_perdus = len(nbre_passes[nbre_passes['pass.outcome.name'].isin(['Incomplete', 'Out', 'Pass Offside'])]) + len(dribbles[dribbles['dribble.outcome.name'] == 'Incomplete']) + len(df_player[df_player['type.name'] == 'Miscontrol']) + len(df_player[df_player['type.name'] == 'Dispossession']) + len(df_player[df_player['type.name'] == 'Error'])
    
    stats['Ballons perdus'] = ball_perdus

    return stats

# Fonction pour calculer le nombre de hors jeu du joueur
def horsjeu_indiv(df, player_name):
    stats = {}

    df_pass = df[df['type.name'] == 'Pass']
    ballon_recu = df_pass[df_pass['pass.recipient.name'] == player_name]
    offside = ballon_recu[ballon_recu['pass.outcome.name'] == 'Pass Offside']

    stats['Hors-jeu'] =  len(offside)

    return stats

# Fonction pour calculer le nombre de fautes du joueur
def fautes_indiv(df_player):
    stats ={}

    fautes_provoques = df_player[df_player['type.name'] == 'Foul Won']
    fautes_commises = df_player[df_player['type.name'] == 'Foul Committed']

    stats['Fautes provoquées'] = len(fautes_provoques)
    stats['Fautes commises'] = len(fautes_commises)

    return stats

# Fonction pour calculer le nombre de ballon joué par le joueur
def ballon_joue_indiv(df, df_player, player_name):
    stats = {}

    interception = df_player[df_player['interception.outcome.name'].isin(['Success', 'Won','Success In Play', 'Success Out'])]
    nbr_ballon_joue = len(interception) + len(df_player[df_player['type.name'] == 'Ball Recovery']) + len(df[df['pass.recipient.name'] == player_name])

    stats['Ballons joués'] = nbr_ballon_joue

    return stats

## Fonction pour les gardiens de but

# Fonction pour calculer le nombre d'arrêts du gardien, les différentes partie du corps utilisé et sa position 
def arrets_indiv(df_player):
    stats = {}

    arrets = df_player[df_player['goalkeeper.type.name'] == 'Shot Saved']    
    
    plongeon = arrets[arrets['goalkeeper.technique.name'] == 'Diving']
    debout = arrets[arrets['goalkeeper.technique.name'] == 'Standing']

    arrets_pieds = arrets[arrets['goalkeeper.body_part.name'].isin(['Left Foot', 'Right Foot'])]
    arrets_mains = arrets[arrets['goalkeeper.body_part.name'].isin(['Left Hand', 'Right Hand', 'Both Hands'])]
    arrets_poitrine = arrets[arrets['goalkeeper.body_part.name'] == 'Chest']
    arrets_tete = arrets[arrets['goalkeeper.body_part.name'] == 'Head']

    stats['Nombre arrêts'] = len(arrets)

    stats['Plongeon'] = len(plongeon)
    stats['Debout'] = len(debout)

    stats['Arrets du pied'] = len(arrets_pieds)
    stats['Arrets des mains'] = len(arrets_mains)
    stats['Arrets poitrine'] = len(arrets_poitrine)
    stats['Arrets tête'] = len(arrets_tete)

    return stats

# Fonction pour calculer les positions du gardiens lors des frappes et le nombre de tirs
def position_gardien(df, player_name):
    stats = {}

    tirs = df[df['type.name'] == 'Shot']
    position = []
    for tir in tirs['shot.freeze_frame'].dropna():
        for joueur in tir:
            if (joueur['position']['name'] == 'Goalkeeper') & (joueur['player']['name'] == player_name):
                position.append(joueur['location'])

    stats['Position gardien'] = position
    stats['Nombre de tirs subis'] = len(position)

    return stats

# Fonction pour calculer le nombre de dégagement de poing du gardien
def degagement_gardien(df_player):
    stats = {}

    degagement_poing = df_player[df_player['goalkeeper.type.name'] == 'Punch']
    stats['Dégagement poings'] = len(degagement_poing)

    return stats

# Fonction pour calculer le nombre de buts concédés du gardien
def buts_concedes_gardien(df_player):
    stats = {}

    buts_concede = df_player[df_player['goalkeeper.type.name'] == 'Goal Conceded']
    cleansheet = 1 if len(buts_concede) == 0 else 0

    stats['Buts concedes'] = len(buts_concede)
    stats['Clean sheet'] = cleansheet

    return stats

# Fonction pour calculer le nombre de penlaty arrêté et encaissé du gardien
def penalty_gardien(df_player):
    stats = {}

    penalty_encaisse = df_player[df_player['goalkeeper.type.name'] == 'Penalty Conceded']
    penalty_sauve = df_player[df_player['goalkeeper.type.name'] == 'Penalty Saved']

    stats['Penalty encaissé'] = len(penalty_encaisse)
    stats['Penlaty arrêté'] = len(penalty_sauve)

    return stats

# Fonction pour calculer les sorties en dehors de la surface du gardien
def sorti_gardien(df_player):
    stats = {}

    sorti = df_player[df_player['goalkeeper.type.name'] == 'Keeper Sweeper']
    stats['Sorti'] = len(sorti)

    return stats

# Fonction pour calculer la position du ballon lorsqu'il est arrêté ou encaissé du gariden
def position_ballon_gardien(df, team_name):
    stats ={}

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

    return stats

# Fonction qui va nous permettre d'appeler toutes les fonctions pour calculer les statistiques
def stat_player(df, player_name, filepath):
    df_player = df[df['player.name'] == player_name]
    df_team = df_player['team.name'].unique()
    team_name = df_team[0]
    poste = df_player['position.name'].unique()[0]
    player_id = df[df['player.name'] == player_name]['player.id'].values[0]
    match_id = Path(filepath).stem

    stats = {'Joueurs' : player_name, 'Equipe' : team_name, 'Poste': poste, 'Joueur Id': player_id, 'Match id': match_id}
    stats.update(temps_de_jeu(df, player_name))
    stats.update(passes_indiv(df_player))
    stats.update(cartons_indiv(df_player))
    stats.update(penalty_provoque_indiv(df_player))
    if poste == 'Goalkeeper':
        stats.update(arrets_indiv(df_player))
        stats.update(position_gardien(df, player_name))
        stats.update(degagement_gardien(df_player))
        stats.update(buts_concedes_gardien(df_player))
        stats.update(penalty_gardien(df_player))
        stats.update(sorti_gardien(df_player))
        stats.update(position_ballon_gardien(df, team_name))
    else:
        stats.update(centres_indiv(df_player))
        stats.update(tirs_indiv(df_player))
        stats.update(dribbles_indiv(df_player))
        stats.update(interception_indiv(df_player))
        stats.update(recuperation_indiv(df_player))
        stats.update(degagement_indiv(df_player))
        stats.update(duels_indiv(df_player))
        stats.update(duels_aerien_indiv(df_player))
        stats.update(ballons_perdus_indiv(df_player))
        stats.update(horsjeu_indiv(df, player_name))
        stats.update(fautes_indiv(df_player))
        stats.update(ballon_joue_indiv(df, df_player, player_name))

    return stats

# Fonction pour parcourir le fichier et réaliser les stats pours tous les joueurs
def stat_tous_player(dossier_path):
    dossier = Path(dossier_path)
    fichiers = list(dossier.glob('*.json'))

    tous_joueurs = []
    total = len(fichiers)
    for i, fichier in enumerate(fichiers, 1):
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
    