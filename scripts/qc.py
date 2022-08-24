import pandas as pd
import logging
import numpy as np

from utils.util_QC import rangeQC, staticQC, flucQC, additionalQC
from utils.chunk import chunk_dataframe_by_acid, chunk_dataframe_by_15min


def qc(f):
    csv_path = "/data3/storage/ADSB/merged"
    df_out_path = "/data3/storage/ADSB/QCdone"

    d = f.split('/')[-1][:-4]
    logging.info(f"Start Calculating File: {d}")
    try:
        df = pd.read_csv(f"{csv_path}/{d}.txt", index_col=0)
        df['time'] = pd.to_datetime(df['time'])
        df['wspd'] = df['wspd']*0.514444    # kts to m/s
        logging.info('read done')

        # altitude QC
        alt_cutoff = (np.abs(df['alt'] - df['alt_x']) > 25) | (np.abs(df['alt'] - df['alt_y']) > 25)
        df = df[~alt_cutoff]
        df = df.drop(columns=['alt_x', 'alt_y'])

        # Drop nan values
        df = df.dropna(subset=['time', 'lat', 'lon', 'alt', 'wspd', 'wdir', 'tas', 'mhed', 'tta', 'gspd'])

        df = rangeQC(df)
        # logging.info(f"After Range QC length: {len(df)}")

        sub_df_list = chunk_dataframe_by_15min(df)
        # logging.info(f"Chunking by time done, {len(sub_df_list)}/4")
        acid_list = chunk_dataframe_by_acid(sub_df_list)
        # logging.info(f"Chunking by acid done, {[len(cl) for cl in acid_list]}")

        chunk_list = list()
        for sub_acid_list in acid_list:
            for chunk in sub_acid_list:
                if len(chunk) > 1:
                    logging.info(f"init {len(chunk)}")
                    chunk = staticQC(chunk)
                    logging.info(f"after static QC {len(chunk)}")
                    chunk = flucQC(chunk)
                    logging.info(f"after fluc QC {len(chunk)}")
                    chunk = additionalQC(chunk)
                    logging.info(f"after additional QC {len(chunk)}")
                    chunk = chunk.dropna(subset=['wspd', 'wdir'])
                    if len(chunk) > 2:
                        chunk_list.append(chunk[1:])
                logging.info(f"fin {len(chunk)}")
        logging.info("static, fluc QC done, concat start")
        df_out = pd.concat(chunk_list)

        df_out = df_out.drop_duplicates(subset=['time', 'acid', 'lat', 'lon', 'alt'])

        logging.info(f"Concat done. Final length: {len(df_out)}")

        df_out.to_csv(f"{df_out_path}/FAAL_ADSB_{d}.csv")
        logging.info("save done")

    except Exception as e:
        logging.critical(e, exc_info=True)
