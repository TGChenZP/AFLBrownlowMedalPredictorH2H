import pandas as pd
import pickle
import json
import os
from collections import defaultdict as dd
import sys



with open(f'../models/final_models/model.pickle', 'rb') as f:
    model = pickle.load(f)

    
# TODO: add in columns



manip_type = 'Head2Head'

csv_list = os.listdir(f'../data/curated/{manip_type}')
csv_list.sort()

csv_list = os.listdir(f'../future data/curated/{manip_type}')
csv_list.sort()

tuning_df = pd.read_csv('../models/tuning/' +'guanganb_BrownlowH2H_RFR.csv')
col = eval(tuning_df.loc[tuning_df['Val Brownlow Metric'].argmax()]['features'])

def predict_brownlow(csv_list):
    json_dict = dict()

    tally = dd(int)

    data = pd.DataFrame()
    for file in csv_list:
        if file[-4:] != '.csv':
            continue

        game_dict = dict()
        if str(sys.argv[1]) in file:
            
            round = file.split()[2]
            team1 = file.split()[3]
            team2 = file.split()[5]
            game = team1 + ' v ' + team2

            data = pd.read_csv(f'../data/curated/{manip_type}/{file}')

            player1 = data['Player1']
            player2 = data['Player2']
            pred = model.predict(data[col])
            pred = pd.DataFrame({'player1': player1, 'player2': player2, 'pred': pred})

            # initialise tallies
            pred_leaderboard = dd(int)
            

            for row in pred.iterrows(): # then get predicted votes
                if row[1]['Predicted Brownlow Votes'] > 0:
                    pred_leaderboard[row[1]['player1']] += 1
                    pred_leaderboard[row[1]['player2']] -= 1

                elif row[1]['Predicted Brownlow Votes'] < 0:
                    pred_leaderboard[row[1]['player1']] -= 1
                    pred_leaderboard[row[1]['player2']] += 1
            
            # turn leaderboard into a useable list
            pred_leaderboard = list(pred_leaderboard.items())
            pred_leaderboard.sort(key = lambda x:x[1],  reverse= True)

            three_votes = pred_leaderboard[0][0]
            
            two_votes = pred_leaderboard[1][0]

            one_vote = pred_leaderboard[2][0]
            
            game_dict[3] = three_votes
            game_dict[2] = two_votes
            game_dict[1] = one_vote

            if f'Round {round}' in json_dict:
                json_dict[f'Round {round}'][game] = game_dict
            else:
                json_dict[f'Round {round}'] = dict()
                json_dict[f'Round {round}'][game] = game_dict

            tally[three_votes] += 3
            tally[two_votes] += 2
            tally[one_vote] += 1
    
    return json_dict, tally


json_dict, tally = predict_brownlow(csv_list) 


with open('../presentables/game_by_game_prediction.json', 'w') as f:
    json.dump(json_dict, f, indent=2)


tally_list = list(tally.items())
tally_list.sort(key = lambda x:x[1], reverse=True)
tally_df = pd.DataFrame(tally_list, columns = ['Player', 'Votes'], index = [i+1 for i in range(len(tally_list))])
tally_df['Ranking'] = tally_df.index
tally_df = tally_df[['Ranking', 'Player', 'Votes']]
tally_df.to_csv('../presentables/leaderboard.csv', index = False)