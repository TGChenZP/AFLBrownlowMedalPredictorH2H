from collections import defaultdict as dd
import numpy as np


def get_brownlow_accuracy_metric(obs_y, pred_y):

    """ Helper to evaluate Brownlow Accuracy Metrics """

    brownlow_accuracy_metric = 0 # overall metric

    for game_id in set(obs_y['game_id']): # every game

        # initialise tallies
        obs_leaderboard = dd(int)
        pred_leaderboard = dd(int)
        
        # get H2H for one game
        obs_game_data = obs_y[obs_y['game_id'] == game_id]
        pred_game_data = pred_y[pred_y['game_id'] == game_id] 

        # for every head to head, get data
        for row in obs_game_data.iterrows(): # first recover actual Brownlow votes
            if row[1]['Brownlow Votes'] > 0:
                obs_leaderboard[row[1]['player1']] += 1
                obs_leaderboard[row[1]['player2']] -= 1

            elif row[1]['Brownlow Votes'] < 0:
                obs_leaderboard[row[1]['player1']] -= 1
                obs_leaderboard[row[1]['player2']] += 1
        
        for row in pred_game_data.iterrows(): # then get predicted votes
            if row[1]['Predicted Brownlow Votes'] > 0:
                pred_leaderboard[row[1]['player1']] += 1
                pred_leaderboard[row[1]['player2']] -= 1

            elif row[1]['Predicted Brownlow Votes'] < 0:
                pred_leaderboard[row[1]['player1']] -= 1
                pred_leaderboard[row[1]['player2']] += 1
        
        # turn leaderboard into a useable list
        obs_leaderboard = list(obs_leaderboard.items())
        obs_leaderboard.sort(key = lambda x:x[1],  reverse= True)

        pred_leaderboard = list(pred_leaderboard.items())
        pred_leaderboard.sort(key = lambda x:x[1],  reverse= True)

        # finally calculate the statistics of model performance for this game
        for i in range(3):
            if obs_leaderboard[0][0] in pred_leaderboard[i][0]:
                brownlow_accuracy_metric += (3-i) # if 3, add 3; if 2, add 2; if 1, add 1
            
            if obs_leaderboard[1][0] in pred_leaderboard[i][0]:
                brownlow_accuracy_metric += 2-abs(i-2) # if 3, add 1; if 2, add 2; if 1, add 1
        
            if obs_leaderboard[2][0] in pred_leaderboard[i][0]:
                brownlow_accuracy_metric += (i+1)/3 # if 1/3, add 1; if 2/3, add 2; if 1, add 1   
        
    return brownlow_accuracy_metric/(len(set(obs_y['game_id']))*6) # scale it by game, and also by max score each game could have acquired





# 03/07/2023





import pandas as pd
import copy
import time
import numpy as np
import pickle

from sklearn.metrics import r2_score, mean_absolute_percentage_error, mean_squared_error
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, balanced_accuracy_score





class JiaoCheng:



    def __init__(self):
        """ Initialise class """
        self._initialise_objects()

        print('JiaoCheng Initialised')



    def _initialise_objects(self):
        """ Helper to initialise objects """

        self.train_x = None
        self.train_y = None
        self.val_x = None
        self.val_y = None
        self.test_x = None
        self.test_y = None
        self.tuning_result = None
        self.model = None
        self.parameter_choices = None
        self.hyperparameters = None
        self.feature_n_ningxiang_score_dict = None
        self.non_tuneable_parameter_choices = list()
        self._feature_combo_n_index_map = None
        self.checked = None
        self.result = None
        self.tuning_result_saving_address = None
        self.object_saving_address = None
        self._up_to = 0
        self._tune_features = False
        self._seed = 19210216
        self.best_score = -np.inf
        self.best_combo = None
        self.best_clf = None
        self.clf_type = None
        self.combos = None
        self.n_items = None
        self.hyperparameter_tuning_order = None
        self._tuning_order_map_hp = None
        self._parameter_value_map_index = None
        self._total_combos = None
        self._tune_features = False
        self.hyperparameter_default_values = None
        self.best_model_saving_address = None

        self.regression_extra_output_columns = ['Train r2', 'Val r2', 'Test r2', 
            'Train RMSE', 'Val RMSE', 'Test RMSE', 'Train MAPE', 'Val MAPE', 'Test MAPE', 'Time']
        self.classification_extra_output_columns = ['Train accu', 'Val accu', 'Test accu', 
            'Train balanced_accu', 'Val balanced_accu', 'Test balanced_accu', 'Train f1', 'Val f1', 'Test f1', 
            'Train precision', 'Val precision', 'Test precision', 'Train recall', 'Val recall', 'Test recall', 'Time']

        

    def read_in_data(self, train_x, train_y, val_x, val_y, test_x, test_y):
        """ Reads in train validate test data for tuning """

        self.train_x = train_x
        print("Read in Train X data")

        self.train_y = train_y
        print("Read in Train y data")

        self.val_x = val_x
        print("Read in Val X data")

        self.val_y = val_y
        print("Read in Val y data")

        self.test_x = test_x
        print("Read in Test X data")

        self.test_y = test_y
        print("Read in Test y data")



    def read_in_model(self, model, type):
        """ Reads in underlying model object for tuning, and also read in what type of model it is """

        assert type == 'Classification' or type == 'Regression' # check

        # record
        self.model = model
        self.clf_type = type 

        print(f'Successfully read in model {self.model}, which is a {self.clf_type} model')



    def set_hyperparameters(self, parameter_choices):
        """ Input hyperparameter choices """

        self.parameter_choices = parameter_choices
        self._sort_hyperparameter_choices()

        self.param_value_reverse_map = {param:{self.parameter_choices[param][j]:j for j in range(len(self.parameter_choices[param]))} for param in self.parameter_choices}

        self.hyperparameters = list(parameter_choices.keys())

        # automatically calculate how many different values in each hyperparameter
        self.n_items = [len(parameter_choices[key]) for key in self.hyperparameters]
        self._total_combos = np.prod(self.n_items)

        # automatically calculate all combinations and setup checked and result arrays and tuning result dataframe
        self._get_combinations()
        self._get_checked_and_result_array()
        self._setup_tuning_result_df()

        print("Successfully recorded hyperparameter choices")



    def _sort_hyperparameter_choices(self):
        """ Helper to ensure all hyperparameter choice values are in order from lowest to highest """

        for key in self.parameter_choices:
            tmp = copy.deepcopy(list(self.parameter_choices[key]))
            tmp.sort()
            self.parameter_choices[key] = tuple(tmp)

    

    def _get_combinations(self):
        """ Helper to calculate all combinations """

        ##ALGORITHM

        # recursively append values to get every combination in ordinal/numerical form
        self.combos = [[]]
        for i in range(len(self.n_items)):

            tmp = copy.deepcopy(self.combos)
            self.combos = list()

            for x in tmp:

                for k in range(self.n_items[i]):
                    y = copy.deepcopy(x)
                    
                    y.append(k)

                    self.combos.append(y)



    def _get_checked_and_result_array(self):
        """ Helper to set up checked and result array """

        self.checked = np.zeros(shape=self.n_items)
        self.result = np.zeros(shape=self.n_items)



    def _setup_tuning_result_df(self):
        """ Helper to set up tuning result dataframe """

        tune_result_columns = copy.deepcopy(self.hyperparameters)

        if self._tune_features == True:
            tune_result_columns.append('feature combo ningxiang score')

        # Different set of metric columns for different types of models
        if self.clf_type == 'Classification':
            tune_result_columns.extend(self.classification_extra_output_columns)
        elif self.clf_type == 'Regression':
            tune_result_columns.extend(self.regression_extra_output_columns)

        self.tuning_result = pd.DataFrame({col:list() for col in tune_result_columns})



    def set_non_tuneable_hyperparameters(self, non_tuneable_hyperparameter_choice):
        """ Input Non tuneable hyperparameter choice """

        if type(non_tuneable_hyperparameter_choice) is not dict:
            raise TypeError('non_tuneable_hyeprparameters_choice must be dict, please try again')
            
        
        for nthp in non_tuneable_hyperparameter_choice:
            if type(non_tuneable_hyperparameter_choice[nthp]) in (set, list, tuple, dict):
                raise TypeError('non_tuneable_hyperparameters_choice must not be of array-like type')
                

        self.non_tuneable_parameter_choices = non_tuneable_hyperparameter_choice

        print("Successfully recorded non_tuneable_hyperparameter choices")



    def set_features(self, ningxiang_output):
        """ Input features """

        if type(ningxiang_output) is not dict:
            raise TypeError("Please ensure NingXiang output is a dict")
            
        
        if not self.hyperparameters:
            raise AttributeError("Missing hyperparameter choices, please run .set_hyperparameters() first")
            
        
        for feature in list(ningxiang_output.keys())[-1]:
            if feature not in list(self.train_x.columns):
                raise ValueError(f'feature {feature} in ningxiang output is not in train_x. Please try again')
                
            if feature not in list(self.val_x.columns):
                raise ValueError(f'feature {feature} in ningxiang output is not in val_x. Please try again')
                
            if feature not in list(self.test_x.columns):
                raise ValueError(f'feature {feature} in ningxiang output is not in test_x. Please try again')
                
        
        # sort ningxiang just for safety, and store up
        ningxiang_output_sorted = self._sort_features(ningxiang_output)
        self.feature_n_ningxiang_score_dict = ningxiang_output_sorted

        # activate this switch
        self._tune_features = True

        # update previous internal structures based on first set of hyperparameter choices
        ##here used numbers instead of tuples as the values in parameter_choices; thus need another mapping to get map back to the features
        self.parameter_choices['features'] = tuple([i for i in range(len(ningxiang_output_sorted))])
        self._feature_combo_n_index_map = {i: list(ningxiang_output_sorted.keys())[i] for i in range(len(ningxiang_output_sorted))}

        self.param_value_reverse_map = {param:{self.parameter_choices[param][j]:j for j in range(len(self.parameter_choices[param]))} for param in self.parameter_choices}
        
        self.hyperparameters = list(self.parameter_choices.keys())

        # automatically calculate how many different values in each hyperparameter
        self.n_items = [len(self.parameter_choices[key]) for key in self.hyperparameters]
        self._total_combos = np.prod(self.n_items)

        # automatically calculate all combinations and setup checked and result arrays and tuning result dataframe
        self._get_combinations()
        self._get_checked_and_result_array()
        self._setup_tuning_result_df()

        print("Successfully recorded tuneable feature combination choices and updated relevant internal structures")


    
    def _sort_features(self, ningxiang_output):
        """ Helper for sorting features based on NingXiang values (input dict output dict) """

        ningxiang_output_list = [(key, ningxiang_output[key]) for key in ningxiang_output]

        ningxiang_output_list.sort(key = lambda x:x[1])

        ningxiang_output_sorted = {x[0]:x[1] for x in ningxiang_output_list}

        return ningxiang_output_sorted


    
    def set_tuning_order(self, order):
        """ Input sorting order """
        
        if type(order) is not list:
            raise TypeError("order must be a list, please try agian")
            
        
        if self.hyperparameters == False:
            raise AttributeError('Please run set_hyperparameters() first')
            
        
        if 'features' in self.hyperparameters:
            if self._tune_features == False:
                raise AttributeError('Please run set_features() first')
                
        
        for hp in order:
            if hp not in self.hyperparameters:
                raise ValueError(f'Feature {hp} is not in self.hyperparameters which was set by set_hyperparameters(); consider reinitiating JiaoCheng or double checking input')
                

        self.hyperparameter_tuning_order = order
        self._tuning_order_map_hp = {self.hyperparameters[i]:i for i in range(len(self.hyperparameters))}
    

    
    def set_hyperparameter_default_values(self, default_values):
        """ Input default values for hyperparameters """

        if type(default_values) is not dict:
            raise TypeError("default_values must be a dict, please try agian")
            
        
        if self.hyperparameters == False:
            raise AttributeError('Please run set_hyperparameters() first')
            
        
        if 'features' in self.hyperparameters:
            if self._tune_features == False:
                raise AttributeError('Please run set_features() first')

        
        for hp in default_values:
            if hp not in self.hyperparameters:
                raise ValueError(f'Feature {hp} is not in self.hyperparameter which was set by set_hyperparameters(); consider reinitiating JiaoCheng or double checking input')
                
            if default_values[hp] not in self.parameter_choices[hp]:
                raise ValueError(f'{default_values[hp]} is not a value to try out in self.hyperparameter which was set by set_hyperparameters(). consider reinitiating JiaoCheng or double checking input')
                

        self.hyperparameter_default_values = default_values


        
    def tune(self, key_stats_only = False): #TODO
        """ Begin tuning """

        if self.train_x is None or self.train_y is None or self.val_x is None or self.val_y is None or self.test_x is None or self.test_y is None:
            raise AttributeError(" Missing one of the datasets, please run .read_in_data() ")
            

        if self.model is None:
            raise AttributeError(" Missing model, please run .read_in_model() ")
            
        
        if self.combos is None:
            raise AttributeError("Missing hyperparameter choices, please run .set_hyperparameters() first")
            

        if self.tuning_result_saving_address is None:
            raise AttributeError("Missing tuning result csv saving address, please run .set_tuning_result_saving_address() first")

        self.key_stats_only = key_stats_only
        
        
        starting_hp_combo = [self.param_value_reverse_map[hp][self.hyperparameter_default_values[hp]] for hp in self.hyperparameters] # setup starting combination
        print('\nDefault combo:', starting_hp_combo, '\n')

        round = 1
        continue_tuning = 1 # continuously loop through features until converge (combo stays same after a full round)
        while continue_tuning:
            print("\nROUND", round)
            round += 1

            # first store previous round's best combo/the starting combo before each round; for comparison at the end
            last_round_starting_hp_combo = copy.deepcopy(starting_hp_combo)

            for hp in self.hyperparameter_tuning_order: # tune each hp in order
                print("\nRound", round, '\nHyperparameter:', hp, f'(index: {self._tuning_order_map_hp[hp]})', '\n')

                last_hyperparameter_best_hp_combo = copy.deepcopy(starting_hp_combo) # store last iteration's best combo

                combo = list(copy.deepcopy(starting_hp_combo)) # tune the root combo
                combo[self._tuning_order_map_hp[hp]] = 0

                for i in range(self.n_items[self._tuning_order_map_hp[hp]]):
                
                    if not self.checked[tuple(combo)]:
                        self._up_to += 1
                        self._train_and_test_combo(combo)
                    else:
                        self._check_already_trained_best_score(combo)
                      
                    combo[self._tuning_order_map_hp[hp]] += 1 
                
                starting_hp_combo = copy.deepcopy(self.best_combo) # take the best combo after this hyperparameter has been tuned
                
                if starting_hp_combo == last_hyperparameter_best_hp_combo:
                    print('\nBest combo after this hyperparameter:', starting_hp_combo, ', NOT UPDATED SINCE LAST HYPERPARAMETER\n')
                else:
                    print('\nBest combo after this hyperparameter:', starting_hp_combo, ', UPDATED SINCE LAST HYPERPARAMETER\n')
            
            if starting_hp_combo == last_round_starting_hp_combo: # if after this full round best combo hasn't moved, then can terminate
                continue_tuning = 0
        

        # Display final information
        self.view_best_combo_and_score()
            
    

    def _eval_combo(self, df_building_dict, train_pred, val_pred, test_pred):

        if self.clf_type == 'Regression':

            train_score = val_score = test_score = train_rmse = val_rmse = test_rmse = train_mape = val_mape = test_mape = 0

            try:
                train_score = r2_score(self.train_y, train_pred)
            except:
                pass
            try:
                val_score = r2_score(self.val_y, val_pred)
            except:
                pass
            try:
                test_score = r2_score(self.test_y, test_pred)
            except:
                pass
            
            try:
                train_rmse = np.sqrt(mean_squared_error(self.train_y, train_pred))
            except:
                pass
            try:
                val_rmse = np.sqrt(mean_squared_error(self.val_y, val_pred))
            except:
                pass
            try:
                test_rmse = np.sqrt(mean_squared_error(self.test_y, test_pred))
            except:
                pass

            if self.key_stats_only == False:
                try:
                    train_mape = mean_absolute_percentage_error(self.train_y, train_pred)
                except:
                    pass
                try:
                    val_mape = mean_absolute_percentage_error(self.val_y, val_pred)
                except:
                    pass
                try:
                    test_mape = mean_absolute_percentage_error(self.test_y, test_pred)
                except:
                    pass
            
            df_building_dict['Train r2'] = [np.round(train_score, 6)]
            df_building_dict['Val r2'] = [np.round(val_score, 6)]
            df_building_dict['Test r2'] = [np.round(test_score, 6)]
            df_building_dict['Train RMSE'] = [np.round(train_rmse, 6)]
            df_building_dict['Val RMSE'] = [np.round(val_rmse, 6)]
            df_building_dict['Test RMSE'] = [np.round(test_rmse, 6)]
            
            if self.key_stats_only == False:
                df_building_dict['Train MAPE'] = [np.round(train_mape, 6)]
                df_building_dict['Val MAPE'] = [np.round(val_mape, 6)]
                df_building_dict['Test MAPE'] = [np.round(test_mape, 6)]

        
        elif self.clf_type == 'Classification':

            train_score = val_score = test_score = train_bal_accu = val_bal_accu = test_bal_accu = train_f1 = val_f1 = test_f1 = \
                train_precision = val_precision = test_precision = train_recall = val_recall = test_recall = 0

            try:    
                train_score = accuracy_score(self.train_y, train_pred)
            except:
                pass
            try:
                val_score = accuracy_score(self.val_y, val_pred)
            except:
                pass
            try:
                test_score = accuracy_score(self.test_y, test_pred)
            except:
                pass

            try:
                train_bal_accu = balanced_accuracy_score(self.train_y, train_pred)
            except:
                pass
            try:
                val_bal_accu = balanced_accuracy_score(self.val_y, val_pred)
            except:
                pass
            try:
                test_bal_accu = balanced_accuracy_score(self.test_y, test_pred)
            except:
                pass
            
            try:
                train_f1 = f1_score(self.train_y, train_pred, average='weighted')
            except:
                pass
            try:
                val_f1 = f1_score(self.val_y, val_pred, average='weighted')
            except:
                pass
            try:
                test_f1 = f1_score(self.test_y, test_pred, average='weighted')
            except:
                pass
            
            try:
                train_precision = precision_score(self.train_y, train_pred, average='weighted')
            except:
                pass
            try:
                val_precision = precision_score(self.val_y, val_pred, average='weighted')
            except:
                pass
            try:
                test_precision = precision_score(self.test_y, test_pred, average='weighted')
            except:
                pass

            try:
                train_recall = recall_score(self.train_y, train_pred, average='weighted')
            except:
                pass
            try:
                val_recall = recall_score(self.val_y, val_pred, average='weighted')
            except:
                pass
            try:
                test_recall = recall_score(self.test_y, test_pred, average='weighted')
            except:
                pass

            df_building_dict['Train accu'] = [np.round(train_score, 6)]
            df_building_dict['Val accu'] = [np.round(val_score, 6)]
            df_building_dict['Test accu'] = [np.round(test_score, 6)]
            df_building_dict['Train balanced_accuracy'] = [np.round(train_bal_accu, 6)]
            df_building_dict['Val balanced_accuracy'] = [np.round(val_bal_accu, 6)]
            df_building_dict['Test balanced_accuracy'] = [np.round(test_bal_accu, 6)]
            df_building_dict['Train f1'] = [np.round(train_f1, 6)]
            df_building_dict['Val f1'] = [np.round(val_f1, 6)]
            df_building_dict['Test f1'] = [np.round(test_f1, 6)]
            df_building_dict['Train precision'] = [np.round(train_precision, 6)]
            df_building_dict['Val precision'] = [np.round(val_precision, 6)]
            df_building_dict['Test precision'] = [np.round(test_precision, 6)]
            df_building_dict['Train recall'] = [np.round(train_recall, 6)]
            df_building_dict['Val recall'] = [np.round(val_recall, 6)]
            df_building_dict['Test recall'] = [np.round(test_recall, 6)]

        return df_building_dict, val_score, test_score
    


    def _train_and_test_combo(self, combo):
        """ Helper to train and test each combination as part of tune() """

        combo = tuple(combo)
        
        params = {self.hyperparameters[i]:self.parameter_choices[self.hyperparameters[i]][combo[i]] for i in range(len(self.hyperparameters))}
        
        
        if self._tune_features == True:
            del params['features']
            tmp_train_x = self.train_x[list(self._feature_combo_n_index_map[combo[-1]])] 
            tmp_val_x = self.val_x[list(self._feature_combo_n_index_map[combo[-1]])]
            tmp_test_x = self.test_x[list(self._feature_combo_n_index_map[combo[-1]])]

            # add non tuneable parameters
            for nthp in self.non_tuneable_parameter_choices:
                params[nthp] = self.non_tuneable_parameter_choices[nthp]

            # initialise object
            clf = self.model(**params)

            params['features'] = [list(self._feature_combo_n_index_map[combo[-1]])] 
            params['feature combo ningxiang score'] = self.feature_n_ningxiang_score_dict[self._feature_combo_n_index_map[combo[-1]]]

        else:
            tmp_train_x = self.train_x
            tmp_val_x = self.val_x
            tmp_test_x = self.test_x

            # add non tuneable parameters
            for nthp in self.non_tuneable_parameter_choices:
                params[nthp] = self.non_tuneable_parameter_choices[nthp]

            # initialise object
            clf = self.model(**params)

        # get time and fit
        start = time.time()
        clf.fit(tmp_train_x, self.train_y)
        end = time.time()

        # get predicted labels/values for three datasets
        train_pred = clf.predict(tmp_train_x)
        val_pred = clf.predict(tmp_val_x)
        test_pred = clf.predict(tmp_test_x)

        train_obs_df = copy.deepcopy(self.train_other_info)
        val_obs_df = copy.deepcopy(self.val_other_info)
        test_obs_df = copy.deepcopy(self.test_other_info)

        train_obs_df['Brownlow Votes'] = list(self.train_y)
        val_obs_df['Brownlow Votes'] = list(self.val_y)
        test_obs_df['Brownlow Votes'] = list(self.test_y)

        train_pred_df = copy.deepcopy(self.train_other_info)
        val_pred_df = copy.deepcopy(self.val_other_info)
        test_pred_df = copy.deepcopy(self.test_other_info)

        train_pred_df['Predicted Brownlow Votes'] = list(train_pred)
        val_pred_df['Predicted Brownlow Votes'] = list(val_pred)
        test_pred_df['Predicted Brownlow Votes'] = list(test_pred)

        try:
            train_brownlow_score = get_brownlow_accuracy_metric(train_obs_df, train_pred_df)
        except:
            train_brownlow_score = 0
        try:
            val_brownlow_score = get_brownlow_accuracy_metric(val_obs_df, val_pred_df)
        except:
            val_brownlow_score = 0
        try:
            test_brownlow_score = get_brownlow_accuracy_metric(test_obs_df, test_pred_df)
        except:
            test_brownlow_score = 0

        # get scores and time used
        time_used = end-start

        # build output dictionary and save result
        df_building_dict = params
        
        df_building_dict['Train Brownlow Metric'] = [np.round(train_brownlow_score, 6)]
        df_building_dict['Val Brownlow Metric'] = [np.round(val_brownlow_score, 6)]
        df_building_dict['Test Brownlow Metric'] = [np.round(test_brownlow_score, 6)]

        # get evaluation statistics
        df_building_dict, val_score, test_score = self._eval_combo(df_building_dict, train_pred, val_pred, test_pred)

        df_building_dict['Time'] = [np.round(time_used, 2)]

        tmp = pd.DataFrame(df_building_dict)


        self.tuning_result = pd.concat([self.tuning_result, tmp])
        self._save_tuning_result()

        # update best score stats
        if val_brownlow_score > self.best_score: 
            self.best_score = val_brownlow_score
            self.best_clf = clf
            self.best_combo = combo
            
            if self.object_saving_address:
                self._save_best_model()

        # update internal governing DataFrames
        self.checked[combo] = 1
        self.result[combo] = val_brownlow_score

        print(f'''Trained and Tested combination {self._up_to} of {self._total_combos}: {combo}, taking {np.round(time_used,2)} seconds to get val score of {np.round(val_brownlow_score,4)}
        Current best combo: {self.best_combo} with val score {np.round(self.best_score, 4)}''')



    def _check_already_trained_best_score(self, combo):
        """ Helper for checking whether an already trained combo is best score """
        
        combo = tuple(combo)
        
        # update best score stats
        if self.result[combo] > self.best_score: 
            self.best_score = self.result[combo]
            self.best_clf = None
            print(f"As new Best Combo {combo} was read in, best_clf is set to None")
            self.best_combo = combo

        print(f'''Already Trained and Tested combination {combo}, which had val score of {np.round(self.result[combo],4)}
        Current best combo: {self.best_combo} with val score {np.round(self.best_score, 4)}. 
        Has trained {self._up_to} of {self._total_combos} combinations so far''')



    def _save_tuning_result(self):
        """ Helper to export tuning result csv """

        tuning_result_saving_address_strip = self.tuning_result_saving_address.split('.csv')[0]

        self.tuning_result.to_csv(f'{tuning_result_saving_address_strip}.csv', index=False)


    
    def view_best_combo_and_score(self):
        """ View best combination and its validation score """
        
        print('Max Score: \n', self.best_score)

        if self.clf_type == 'Classification':
            max_val_id = self.tuning_result['Val accu'].idxmax()
            print('Max Test Score: \n', self.tuning_result.iloc[max_val_id]['Test accu'])
            
        elif self.clf_type == 'Regression':
            max_val_id = self.tuning_result['Val Brownlow Metric'].idxmax()
            print('Max Test Score: \n', self.tuning_result.iloc[max_val_id]['Test Brownlow Metric'])

        print('Max Combo Index: \n', self.best_combo, 'out of', self.n_items, '(note best combo is 0-indexed)')

        final_combo = {self.hyperparameters[i]:self.parameter_choices[self.hyperparameters[i]][self.best_combo[i]] for i in range(len(self.hyperparameters))}
        print('Max Combo Hyperparamer Combination: \n', final_combo)

        if self._tune_features:
            print('Max Combo Features: \n', self._feature_combo_n_index_map[self.best_combo[-1]])

        print('% Combos Checked:', int(sum(self.checked.reshape((np.prod(self.n_items))))), 'out of', np.prod(self.n_items), 'which is', f'{np.mean(self.checked).round(8)*100}%')

    

    def read_in_tuning_result_df(self, address): 
        """ Read in tuning result csv and read data into checked and result arrays """

        if self.parameter_choices is None:
            raise AttributeError("Missing parameter_choices to build _parameter_value_map_index, please run set_hyperparameters() first")

        if self.clf_type is None:
            raise AttributeError('Missing clf_type. Please run .read_in_model() first.')

        self.tuning_result = pd.read_csv(address)

        self._up_to = 0

        self._create__parameter_value_map_index()

        # read DataFrame data into internal governing DataFrames of JiaoCheng
        for row in self.tuning_result.iterrows():

            try:
                self._up_to += 1
        
                combo = list()
                for hyperparam in self.hyperparameters:
                    if hyperparam == 'features':
                        
                        # reverse two dicts
                        index_n_feature_combo_map = {self._feature_combo_n_index_map[key]:key for key in self._feature_combo_n_index_map}
                        # special input
                        combo.append(index_n_feature_combo_map[tuple(self._str_to_list(row[1]['features']))])
                        
                    else:
                        if type(self.parameter_choices[hyperparam][0]) is bool:
                            combo.append(self._parameter_value_map_index[hyperparam][bool(row[1][hyperparam])])
                        else:
                            combo.append(self._parameter_value_map_index[hyperparam][row[1][hyperparam]])

                combo = tuple(combo)
                
                self.checked[combo] = 1
                
                if self.clf_type == 'Regression':
                    self.result[combo] = row[1]['Val Brownlow Metric']
                elif self.clf_type == 'Classification':
                    self.result[combo] = row[1]['Val accu']

            except Exception as e:
                print(f"Error message: {str(e)}")
                print('Error Importing this Row:', row)

        print(f"Successfully read in tuning result of {len(self.tuning_result)} rows")



    def _str_to_list(self, string):
        """ Helper to convert string to list"""

        out = list()
        for feature in string.split(', '):
            out.append(feature.strip('[').strip(']').strip("'"))
        
        return out


    
    def _create__parameter_value_map_index(self):
        """ Helper to create parameter-value index map """

        self._parameter_value_map_index = dict()
        for key in self.parameter_choices.keys():
            tmp = dict()
            for i in range(len(self.parameter_choices[key])):
                tmp[self.parameter_choices[key][i]] = i
            self._parameter_value_map_index[key] = tmp
    


    def set_tuning_result_saving_address(self, address):
        """ Read in where to save tuning object """

        self.tuning_result_saving_address = address
        print('Successfully set tuning output address')


    
    def set_best_model_saving_address(self, address):
        """ Read in where to save best model  """

        self.best_model_saving_address = address
        print('Successfully set best model output address')

    

    def _save_best_model(self):
        """ Helper to save best model as a pickle """

        best_model_saving_address_split = self.best_model_saving_address.split('.pickle')[0]

        with open(f'{best_model_saving_address_split}.pickle', 'wb') as f:
            pickle.dump(self.best_clf, f)