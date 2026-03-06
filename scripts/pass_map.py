### Création des fonctions qui vont permettre la création d'un tableau avec les coordonnées des passes
### de chaque joueur
import padnas as pd
from utils import load_match
from pathlib import Path

# Fonction pour obtenir les coordonnées des passes
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

# Fonction pour parcourir les fichiers dans le dossier et lancé la fonction
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


#Réseaux de passe

#HeatMap de chaque joueur

#Rajouter fonctions pour emplacement des tirs 

#Pressing des joueurs

