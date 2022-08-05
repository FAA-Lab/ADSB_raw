import numpy as np
import pandas as pd


def rangeQC(df):
    if np.issubdtype(df["time"].dtype, np.datetime64):
        pass
    else:
        df["time"] = pd.to_datetime(df["time"], errors='coerce')

    range_dict = {
        "alt": (-1000., 50000.),  # altitude (ft)
        "wdir": (0., 360.),  # wind direction (deg)
        "wspd": (0., 400.),  # wind speed (m/s)
        "lat": (-90., 90.),  # latitude (deg)
        "lon": (-180., 180.),  # longitude (deg)
    }
    for k, v in range_dict.items():
        if k in df.columns:
            df[k] = df[k].apply(lambda x: x if (v[0] <= x <= v[1]) else None)

    df = df.dropna(axis=0, how='any', subset=["lat", "lon"])

    return df


def staticQC(df):
    ths = 5
    static_list = ["time", "tc", "wdir", "wspd"]
    for k in static_list:
        if k in df.columns:
            df[f"flag_{k}"] = (df[k].groupby([df[k].diff().ne(0).cumsum()]).transform('size').ge(ths).astype(int))
            df[k] = df[k][df[f"flag_{k}"]==0]
            df = df.drop(columns=[f"flag_{k}"])

    df = df.dropna(axis=0, how='any', subset=["time"])

    return df


def flucQC(df):
    df["timegap"] = df["time"].diff(1) / pd.Timedelta(minutes=1)  # interval by minute

    fluc_dict = {
        "alt": 5000,  # altitude (ft)
        "wdir": 180,  # wind direction (deg)
        "wspd": 25,  # wind speed (m/s)
        "lat": 0.5,  # latitude (deg)
        "lon": 5,  # longitude (deg)
    }

    for k, v in fluc_dict.items():
        if k in df.columns:
            if k != "wdir":
                df[f"fluc_{k}"] = df[k].diff(1) * df["timegap"]
                df[k] = df[k][abs(df[f"fluc_{k}"]) < v]
                df = df.drop(columns=[f"fluc_{k}"])
            else:
                df[f"fluc_{k}"] = df[k].diff(1).apply(lambda x: (x + 180) % 360 - 180 ) * df["timegap"]
                df[k] = df[k][abs(df[f"fluc_{k}"]) < v]
                df = df.drop(columns=[f"fluc_{k}"])

    df = df.drop(columns=["timegap"])
    df = df.dropna(axis=0, how='any', subset=["lat", "lon"])

    return df

def additionalQC(df):
    df["timegap"] = df["time"].diff(1)
    fluc_dict = {
        "tas":50,
        "mhed":5,
        "tta":5,
        "gspd":50
    }
    for k, v in fluc_dict.items():
        if k in df.columns:
            if (k != "mhed") | (k != "tta"):
                df[f"fluc_{k}"] = df[k].diff(1)
                df[k] = df[k][~((df["timegap"] == 0) & (abs(df[f"fluc_{k}"]) > v))]
                df = df.drop(columns=[f"fluc_{k}"])
            else:
                df[f"fluc_{k}"] = df[k].diff(1).apply(lambda x: (x + 180) % 360 - 180 ) * df["timegap"]
                df[k] = df[k][~((df["timegap"] == 0) & abs(df[f"fluc_{k}"]) > v)]
                df = df.drop(columns=[f"fluc_{k}"])

    df = df.drop(columns=["timegap"])
    df = df.dropna(axis=0, how='any', subset=["lat", "lon"])
    return df

def judge_phase(vr):
    # assume that vertical rate is in the unit of ft/min
    if vr > 600:
        # ascending
        return 0
    elif vr < -600:
        # descending
        return 1
    else:
        # level flight
        return 2


def linear_interpolation(df, col):
    df['phase_flag'] = df['vr'].apply(judge_phase)

    flag0, flag1, flag2 = 0, 0, 0
    flag0_list, flag1_list, flag2_list = list(), list(), list()
    for i, row in df.iterrows():
        if row['phase_flag'] == 0:
            flag0 += 1
            flag1 = 0
            flag2 = 0
            if flag0 == 3:
                flag0 = 0
                flag0_list.append(i)
        elif row['phase_flag'] == 1:
            flag1 += 1
            flag0 = 0
            flag2 = 0
            if flag1 == 3:
                flag1 = 0
                flag1_list.append(i)
        elif row['phase_flag'] == 2:
            flag2 += 1
            flag0 = 0
            flag1 = 0
            if flag2 == 12:
                flag2 = 0
                flag2_list.append(i)

    for i0 in flag0_list:
        df[col].iloc[i0 - 2:i0 + 1] = np.linspace(df[col].iloc[i0 - 2], df[col].iloc[i0], 3)
    for i1 in flag1_list:
        df[col].iloc[i1 - 2:i1 + 1] = np.linspace(df[col].iloc[i1 - 2], df[col].iloc[i1], 3)
    for i2 in flag2_list:
        df[col].iloc[i2 - 11:i2 + 1] = np.linspace(df[col].iloc[i2 - 12], df[col].iloc[i2], 12)

    return df
