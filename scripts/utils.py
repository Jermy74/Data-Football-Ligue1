import pandas as pd
import json 
import glob
import os
from pathlib import Path

def load_match(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return pd.json_normalize(data)

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


