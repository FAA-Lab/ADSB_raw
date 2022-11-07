import pandas as pd
import glob
import logging

from utils.chunk import chunk_dataframe_by_15min, chunk_dataframe_by_hour, chunk_dataframe_by_acid
from utils.util_edr import calculate_jerk, calculate_edr2

def edr2(f):
    csv_path = "/data3/storage/ADSB/QCdone"
    edr_path = f"/data3/storage/ADSB/EDR/EDR2"

    d = f.split('/')[-1][10:-4]
    logging.info(f"Start Calculating File: {d}")

    try:
        df = pd.read_csv(f"{csv_path}/FAAL_ADSB_{d}.csv", index_col=0)
        df['time'] = pd.to_datetime(df['time'])
        df = df.dropna(subset=['wdir', 'wspd'], how='any')

        sub_df_list = chunk_dataframe_by_hour(df)
        acid_list = chunk_dataframe_by_acid(sub_df_list)

        chunk_list = list()
        for sub_acid_list in acid_list:
            for chunk in sub_acid_list:
                if len(chunk) >= 60:
                    chunk_list.append(chunk)
        logging.info(f"Available chunk: {len(chunk_list)}")

        out_csv_list = list()
        for data_i, data in enumerate(chunk_list):
            edr_data = calculate_edr2(data)
            out_csv_list.append(edr_data)
        logging.info("calc done")

        out_df = pd.concat(out_csv_list)
        out_df.to_csv(f'{edr_path}/EDR2_{d}.csv')
        logging.info("save done")

    except Exception as e:
        logging.critical(e, exc_info=True)


def jerk(f):
    csv_path = "/data3/storage/ADSB/QCdone"
    edr_path = f"/data3/storage/ADSB/EDR/jerk"

    d = f.split('/')[-1][10:-4]
    logging.info(f"Start Calculating File: {d}")

    try:
        df = pd.read_csv(f"{csv_path}/FAAL_ADSB_{d}.csv", index_col=0)
        df['time'] = pd.to_datetime(df['time'])
        df = df.dropna(subset=['vr'], how='any')

        sub_df_list = chunk_dataframe_by_15min(df)
        acid_list = chunk_dataframe_by_acid(sub_df_list)

        jerk_list = list()
        for sub_acid_list in acid_list:
            for data in sub_acid_list:
                jerk_data = calculate_jerk(data)
                jerk_list.append(jerk_data)
        jerk_df = pd.concat(jerk_list)
        jerk_df.to_csv(f'{edr_path}/jerk_{d}.csv')

    except Exception as e:
        logging.critical(e, exc_info=True)
