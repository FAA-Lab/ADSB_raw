# QC applied by new_csv (calculated wind) and plot

import pandas as pd
import glob
import logging
import matplotlib.pyplot as plt
import numpy as np

from utils.util_QC import rangeQC, staticQC, flucQC, additionalQC
from utils.chunk import chunk_dataframe_by_acid, chunk_dataframe_by_15min


target_year = "2020"

log_path = "../log"
logging.basicConfig(filename=f"{log_path}/{target_year}_calculated_wind_QC.log",
                    filemode='a',
                    format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

csv_path = "/data3/storage/ADSB/merged"
df_out_path = "/data3/storgage/ADSB/QCdone"

fig_out_path = "../results/wind_QC_fig"
logging.info(f'Start QC for calculated wind')

csv_list = glob.glob(f"{csv_path}/{target_year}*.txt")
filname = [x.split('/')[-1][:-4] for x in glob.glob(f"{csv_path}/*.txt")]

length_before_QC = np.zeros(len(filname))
length_after_QC = np.zeros(len(filname))

for i, d in enumerate(filname):
    try:
        logging.info(f"Start Calculating File: {d}")
        df = pd.read_csv(f"{csv_path}/{d}.txt", index_col=0)
        df['time'] = pd.to_datetime(df['time'])
        df['wspd'] = df['wspd']*0.514444    # kts to m/s
        logging.info('read done')
        length_before_QC[i] = len(df)

        # altitude QC
        alt_cutoff = (np.abs(df['alt'] - df['alt_x']) > 25) | (np.abs(df['alt'] - df['alt_y']) > 25)
        df = df[~alt_cutoff]
        df = df.drop(columns=['alt_x', 'alt_y'])

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
        length_after_QC[i] = len(df_out)

        df_out.to_csv(f"{df_out_path}/FAAL_ADSB_{d}.csv")
        logging.info("save done")

    except Exception as e:
        logging.critical(e, exc_info=True)

fig, axes = plt.subplots(2, 1, figsize=(16, 6), gridspec_kw={'height_ratios': [3, 1]})
axes[0].plot(np.arange(len(filname)), length_after_QC/length_before_QC)
axes[1].plot(np.arange(len(filname)), length_before_QC)
fig.savefig(f'{fig_out_path}/{target_year}_QCdone_ratio.png')
logging.info("draw done")
