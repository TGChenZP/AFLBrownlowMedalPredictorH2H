import os
import json
import pandas as pd




with open('../future data/raw/AFLCA_votes.json', 'r') as f:
    AFLCA_votes_dict = json.load(f)

errors = 0

if not os.path.exists(f'../future data/curated/AFLCAVotes'):
    os.makedirs(f'../future data/curated/AFLCAVotes')

for year in AFLCA_votes_dict:
    for round in AFLCA_votes_dict[year]:
        for game in AFLCA_votes_dict[year][round]:

            teams_list = game.split(' ')
            team1 = teams_list[0]
            team2 = teams_list[1]
            try:
                data = pd.read_csv(f'../future data/curated/OriginalData_AddDerived/{year} Round {round} {team1} v {team2} (O).csv')
            except:
                data = pd.read_csv(f'../future data/curated/OriginalData_AddDerived/{year} Round {round} {team2} v {team1} (O).csv')
                print('Teams reversed')
                print(year, round, game)
                print(votes_data)

            votes_data = AFLCA_votes_dict[year][round][game]

            AFLCA_votes = list()
            for player in data['Player']:
                if player.lower() in votes_data:
                    AFLCA_votes.append(votes_data[player.lower()])
                else:
                    AFLCA_votes.append(0)

            if sum(AFLCA_votes) != 30: # validation
                print('Did not sum up to 30:', sum(AFLCA_votes))
                print(year, round, game)
                print(votes_data, '\n')

                errors += 1

            data['AFLCA_votes'] = AFLCA_votes

            data.to_csv(f'../future data/curated/AFLCAVotes/{year} Round {round} {team1} v {team2} (O).csv', index = False)

print(errors)






import numpy as np
from sklearn.model_selection import train_test_split





filelist = os.listdir(f'../future data/curated/AFLCAVotes')
filelist.sort()
filelist = [file for file in filelist if file[0] != '.' ]





# First make dictionaries which direct the flow of control as to whether a column shoul receive manipulation and whether it should be positive or inversed direction.

# Unchanged
Orig = ['Player']

# compare
compare = ['Winloss','HomeAway', 'AFLCA_votes', 'Kicks', 'Handballs', 'Disposals', 'Marks', 'Goals', 'Behinds', 'Tackles', 'Hitouts', 'Goal Assists', 'Inside 50s', 
               'Clearances', 'Rebound 50s', 'Frees For', 'Contested Possessions', 'Uncontested Possessions', 
               'Effective Disposals', 'Contested Marks', 'Marks Inside 50', 'One Percenters', 'Bounces', 'Centre Clearances', 
               'Stoppage Clearances', 'Score Involvements', 'Metres Gained', 'Intercepts', 'Tackles Inside 50', 'Time On Ground %', 'Uncontested Marks',
               'Marks Outside 50', 'Tackles Outside 50', 'Behind Assists', 'Effective Disposals', 'Ineffective Disposals', 'Brownlow Votes', 'Clangers', 'Turnovers', 'Frees Agains']





if not os.path.exists(f'../future data/curated/Head2Head'):
    os.makedirs(f'../future data/curated/Head2Head')





for file in filelist:

    if file in os.listdir(f'../future data/curated/Head2Head'):
        continue

    df = pd.read_csv(f'../future data/curated/AFLCAVotes/{file}')
    # df = df[df['Time On Ground %'] > 0.55] # below this time on ground no player has won Brownlow Votes (ever)

    df['HomeAway'] = df['HomeAway'].apply(lambda x: 1 if x=='Home' else 0)

    game_head2head_df_list = []

    for player in df['Player']:
        
        one_player_df_list = []

        player_stat = df[df['Player']==player]

        for other_player in df['Player']:
            if other_player == player:
                continue
            
            other_player_stat = df[df['Player']==other_player]

            head_2_head = {'player1': [player], 'player2': [other_player]}

            for stat in compare:
                
                head_2_head[stat] = [player_stat[stat].values[0] - other_player_stat[stat].values[0]]
    
            head_2_head_df = pd.DataFrame(head_2_head)

            one_player_df_list.append(head_2_head_df)

        one_player_df = pd.concat(one_player_df_list)
        game_head2head_df_list.append(one_player_df)  
    
    game_head2head_df = pd.concat(game_head2head_df_list)

    game_head2head_df.to_parquet(f'../future data/curated/Head2Head/{file.split(".")[0]}.parquet')