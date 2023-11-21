# BrownlowPredictor (Head2Head using AFLCA votes)
- Author: Lang (Ron) Chen
- Date: Feb 2023 - Nov 2023


**Presentables**
- Flask web application at `./app/Programme.py`
- To run web application, please open terminal at `./app` and input `export FLASK_APP='Programme.py` and `flask run` before heading to the link as described printed in the terminal
- First click **scrape data** (may take a moment), followed by **predict**
- You can view game by game prediction by clicking **Game by Game Prediction**

**Introduction**

This project attempts to predict the Brownlow Medal winner (AFL's highest individual honour) based on statistics of each AFL game.
It predicts following the structure of the actual brownlow medal (i.e. voting game by game)

**Method**
1. Data was crawled and scraped from the afltables, and validated by footywire data; data were then stored by game; AFLCA data were also scraped from the AFLCA website
2. Additional features were generated
3. Head to Head statistics for each pair of players onfield were created (i.e. each feature became player 1's features subtract player 2's features).
4. Features were normalised (x-mean)/sd within each game
5. Many regression models were attempted (tuned to best validation score hyperparameter combination), where each model predicted the difference in Brownlow votes received by each instance (pair of players) (i.e. 3, 2, 1, 0, -1, -2, -3)

-  *models attempted includes: Linear Regression (with regularisation), Binomial Regression, K-Nearest Neighbour Regressor, Random Forest Regressor, Extra Random Forest Regressor, AdaBoost Regressor, GradientBoost Regressor, XGB Regressor, LightGBM Regressor, CatBoost Regressor, Explainable Boosting Machine Regressor, Fully Connected Neural Network Regressor* 

Prediction

6. Each game was put through the model to get predicted differences in Brownlow votes.
- within each pair, if the predicted difference in Brownlow votes is positive, then 1 point is given to 'player 1' in this pair and -1 points given to 'player 2'; otherwise, 1 point is given to 'player 2' and -1 point is given to player 1.
- The highest points-getter within a game gets 3 votes, the second gets 2 votes, the third gets 1 vote etc.
7. Each game's votes are tallied up and the player with the highest vote for the season is the predicted Brownlow Winner
<br>

**Tuning Results (Validation dataset Brownlow score)**
| Model | 1 val  | 
|-------|--------|
| RFR   | 0.6478 | 
| GBR   | 0.6184 |  
| XGB   | 0.6195 |  
| LGB   | 0.6258 | 
| CBR   | 0.6216 |  
| EBR   | 0.6184 |
| DNN   | 0.6279
| DNN_c | 0.6195 | 
| EXTRFR| 0.6363 | 
| HGBR  | 0.5943 | 
| DNN   | 0.6279 |
| GLR   | 0.5902 |
| ELR   | 0.6111

* for the Brownlow Score, the model gets points for each game in this way:

| Ground Truth | Predicted | Points Won |
| 3 | 3 | 3 |
| 3 | 2 | 2 |
| 3 | 1 | 1 |
| 2 | 3 | 1 |
| 2 | 2 | 2 |
| 2 | 1 | 1 |
| 1 | 3 | 1/3 |
| 1 | 2 | 2/3 |
| 1 | 1 | 1 |

before being divided by 6 (the largest possible score for each game) and then averaged across the number of games

The scheme used to select the best model was the model with the highest test score, out of all the best-validation score model-hyperparameter combination for each model. The ultimate chosen model was the Random Forest Regressor.

**Results**

For held out 2022 data, predicted Touk Miller with 33 votes to be the Brownlow Winner and Ground Truth winner Patrick Cripps on 29 votes (3rd). 

Empirically, the model tends to have each year's actual winner within its top 3


**Bibliography**

Data Source

- AFLTables.com. 2022. Brownlow Votes Round by Round. [online] Available at: <https://afltables.com/afl/brownlow/brownlow_idx.html> [Accessed 26 January 2022].

- Footywire.com. 2022. AFL Fixture. [online] Available at: <https://www.footywire.com/afl/footy/ft_match_list> [Accessed 26 January 2022].
