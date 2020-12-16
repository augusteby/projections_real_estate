import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import ppscore as pps

if __name__ == '__main__':
    # load projection report data
    projection_df = pd.read_csv('exemple/projection_report_all.csv')

    # filter out unwanted columns
    cols_to_filter_out = ['cash_flow_annuel_apport_total_inclu']
    projection_df_filtered = projection_df.drop(cols_to_filter_out, axis=1)

    # identify target variable and split data between features and labels
    target_variable = 'cash_flow_annuel'
    labels = projection_df_filtered[target_variable].values
    features = projection_df_filtered.drop([target_variable], axis=1).values

    # Display PPS scores
    pps_score = pps.predictors(projection_df_filtered, target_variable)
    print('######################### PPS SCORES #########################')
    print(pps_score)

    # apply Random Forest and get feature importance scores
    rdmf = RandomForestRegressor()
    rdmf.fit(features, labels)
    feature_importance_score = rdmf.feature_importances_

    # Display feature importance scores
    feature_names = projection_df_filtered.drop(['cash_flow_annuel'], axis=1).columns.values
    zipped = zip(feature_names, feature_importance_score)
    feature_importances = sorted(zipped, key=lambda t: t[1], reverse=True)
    print('')
    print('')
    print('######################### RDMF FEATURE IMPORTANCE SCORES #########################')
    print(feature_importances)
