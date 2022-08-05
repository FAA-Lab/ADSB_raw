import numpy as np
import pandas as pd


def chunk_dataframe_by_15min(df):
    if np.issubdtype(df["time"].dtype, np.datetime64):
        pass
    else:
        df["time"] = pd.to_datetime(df["time"], errors='coerce')

    sub_df_list = list()
    for (start_hour, sub_df) in df.groupby(pd.Grouper(key='time', freq='15min')):
        sub_df_list.append(sub_df)

    return sub_df_list


def chunk_dataframe_by_callsign(df_list):
    callsign_list = list()
    for df in df_list:
        temp_list = list()
        for csgn in df["csgn"].unique():
            temp_list.append(df[df["csgn"] == csgn])
        callsign_list.append(temp_list)
    return callsign_list


def chunk_dataframe_by_hour(df):
    if np.issubdtype(df["time"].dtype, np.datetime64):
        pass
    else:
        df["time"] = pd.to_datetime(df["time"], errors='coerce')

    sub_df_list = list()
    for (start_hour, sub_df) in df.groupby(pd.Grouper(key='time', freq='60min')):
        sub_df_list.append(sub_df)

    return sub_df_list

def chunk_dataframe_by_1min(df):
    if np.issubdtype(df["time"].dtype, np.datetime64):
        pass
    else:
        df["time"] = pd.to_datetime(df["time"], errors='coerce')

    sub_df_list = list()
    for (start_hour, sub_df) in df.groupby(pd.Grouper(key='time', freq='1min')):
        sub_df_list.append(sub_df)

    return sub_df_list

