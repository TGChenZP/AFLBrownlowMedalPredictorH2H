# BrownlowPredictor (2023 Version)
- Author: Lang (Ron) Chen
- Date: Dec 2022 - Feb 2023


**Presentables**
- Flask web application at `./app/Programme.py`
- To run web application, please open terminal at `./app` and input `export FLASK_APP='Programme.py` and `flask run` before heading to the link as described printed in the terminal
- First click **scrape data** (may take a moment), followed by **predict**
- You can view game by game prediction by clicking **Game by Game Prediction**

**Introduction**

This project attempts to predict the Brownlow Medal winner (AFL's highest individual honour) based on statistics of each AFL game.
It predicts following the structure of the actual brownlow medal (i.e. voting game by game)

**Method**
1. Data was crawled and scraped from the afltables, and validated by footywire data; data were then stored by game
2. Additional features were generated
3. Features were normalised (x-mean)/sd within each game
4. Brownlow votes were turned into three labels using one hot encoding (i.e. 1 vote model: player with 1 vote has label 1, every other player 0; 2 vote model: player with 2 votes has label 2, every other player 0 etc); thus three final models were required
5. For each model, features that had abs(correlation with label) higher than 0.1 were selected
6. Many regression models were attempted (tuned to best validation score hyperparameter combination)

-  *models attempted includes: Linear Regression (with regularisation), Binomial Regression, K-Nearest Neighbour Regressor, Random Forest Regressor, AdaBoost Regressor, GradientBoost Regressor, XGB Regressor, LightGBM Regressor, CatBoost Regressor, Explainable Boosting Machine Regressor, Fully Connected Neural Network Regressor* 

Prediction

7. Each game was put through the three models to get predicted outputs. 
- the player with highest predicted score for 3-votes model gets 3 predicted votes
- the player with highest predicted score for 2-votes model gets 2 predicted votes, unless they have already received 3 votes in which case the second ranked player for this model gets 2 votes
- the player with highest predicted score for 1-votes model gets 1 predicted votes, unless they have already received 3 votes or 2 votes in which case the second ranked player for this model gets 1 vote. If the second ranked player also has received a higher vote then the third ranked player receives 1 vote
8. Each game's votes are tallied up and the player with the highest vote for the season is the predicted Brownlow Winner
<br>

**Tuning Results (Validation dataset r<sup>2</sup> score)**
| Model | 1 val  | 1 test  | 
|-------|--------|--------|
| RFR   | 0.5488 | 0.5051 |
| GBR   |  |  |
| XGB   |  |  |
| LGB   | 0.5454 | 0.5093 |
| CBR   |  |  |
| EBR   | 0.5273 | 0.4830 |
| NN    | **0.5687** | 0.5208 |
| EXTRFR| 0.5485 | 0.5160 |
| EBinR | 0.5516 | 0.5085 |
| BinR  | 0.5517 | 0.5103 |
| HBR   | 0.5246 | 0.4928 |
| DNN_c | 0.5672 | **0.5224** |

| Model | 2 val  | 2 test  | 
|-------|--------|--------|
| RFR   | 0.1104 | 0.0536 |
| ADA   | 0.0991 | 0.0613 |
| GBR   |  |  |
| XGB   | 0.1126 | 0.0601 |
| LGB   | 0.5454 |  |
| CBR   |  |  |
| EBR   | 0.1040 | **0.0816** |
| NN    | 0.1160 | 0.0663 |
| EXTRFR| **0.1267** | 0.0782 |
| HBR   | 0.1042 | 0.0778 |
| DNN_c | 0.1190 | 0.0718 |

| Model | 3 val  | 3 test  | 
|-------|--------|--------|
| RFR   | 0.1642 | 0.1470 |
| ADA   | 0.1493 | 0.1490 |
| GBR   |  |  |
| XGB   | 0.1537 | 0.1208 |
| LGB   | **0.1778** | 0.1529 |
| CBR   |  |  |
| EBR   | 0.1692 | 0.1556 |
| NN    | 0.1773 | 0.1678 |
| EXTRFR| 0.1267 | 0.1571 |
| HBR   | 0.1725 | 0.1504 |
| DNN_c | 0.1765 | **0.1720** |


However, due to inability to replicate NN results, the ultimate models used were
- 1 vote: LightGB
- 2 votes: LightGB
- 3 votes: GradientBoost

**Results**

For held out 2022 data, predicted Clayton Oliver with 35 votes and actual winner Patrick Cripps on 28 votes (2nd). 

Emperically, model tends to have each year's actual winner within its top 3


**Bibliography**

Data Source

- AFLTables.com. 2022. Brownlow Votes Round by Round. [online] Available at: <https://afltables.com/afl/brownlow/brownlow_idx.html> [Accessed 26 January 2022].

- Footywire.com. 2022. AFL Fixture. [online] Available at: <https://www.footywire.com/afl/footy/ft_match_list> [Accessed 26 January 2022].