import pandas as pd
import glob
import logging

from utils.common import unixtime2utc, df, typecode, icao
from utils.position import oe_flag, altitude05, util_position, altcode
from utils.BDS50 import is50, roll50, trk50, gs50, tas50
from utils.BDS60 import is60, hdg60, vr60ins, mach60, ias60

log_path = "../log"
logging.basicConfig(filename=f"{log_path}/decode.log",
                    filemode='a',
                    format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

file_path = "/data3/storage/ADSB/raw/DF"
out_path = "/data3/sotrage/ADSB/merged"
time_resolution = "0.5S"

logging.info(f"Decode start, all files")
logging.info(f"file_path: {file_path}")
logging.info(f"out_path: {out_path}")
logging.info(f"time_resolution: {time_resolution}")

# Read file
for f in glob.glob(f"{file_path}/**/*.txt"):
    filename = f.split('/')[-1]
    date = f.split('/')[-2]
    logging.info(f"{date}, {filename}")

    try:
        target = pd.read_csv(f, sep="\s+", header=None)
        target.columns = ['time', 'code']
        logging.info(f"Read done")

        # Timestamp
        target['time'] = target['time'].apply(lambda x: unixtime2utc(x))
        target['time'] = pd.to_datetime(target['time'])
        target['time'] = target['time'].dt.round(time_resolution)
        logging.info(f"Raw data: len {len(target)}")
        logging.info(f"Add timestamp done")

        # Filtering length
        target['length'] = target['code'].apply(lambda x: len(x))
        target = target[target['length']==28]
        logging.info(f"Length filtering done")

        # Flags
        target['df'] = target['code'].apply(lambda x: df(x))
        target['tc'] = target['code'].apply(lambda x: typecode(x))
        target['oe'] = target['code'].apply(lambda x: oe_flag(x))
        target['is60'] = target['code'].apply(lambda x: is60(x) if (df(x)==21 or df(x)==20) else None)
        target['is50'] = target['code'].apply(lambda x: is50(x) if (df(x)==21 or df(x)==20) else None)
        logging.info(f"Flag done")

        # Filtering downlink format
        target = target[(target['df']==17) | (target['df']==20) | (target['df']==21)]

        # Split data based on DF
        target_adsb = target[target['df']==17]
        target_commb = target[(target['df']==20) | (target['df']==21)]
        logging.info(f"First split done")

        # Filtering typecode for ADSB data
        target_adsb = target_adsb[(target_adsb['tc'] >= 9) & (target_adsb['tc'] <= 18)]

        # Altitude for ADSB data
        target_adsb['alt'] = target_adsb['code'].apply(lambda x: altitude05(x))
        logging.info(f"ADSB altitude done")

        # Get position information from ADSB data
        unqt = target_adsb['time'].unique()
        adsb_list = list()
        for j, t in enumerate(unqt):
            sample = target_adsb[target_adsb['time'] == t]
            acidlist = sample['acid'].unique()
            for acid in acidlist:
                chunk_pos = pd.DataFrame()
                sample_use = sample[sample['acid'] == acid]
                sample_latlon_list, sample_alt_list = util_position(sample_use)
                if len(sample_latlon_list) > 0:
                    chunk_pos['lat'] = [x[0] for x in sample_latlon_list]
                    chunk_pos['lon'] = [x[1] for x in sample_latlon_list]
                    chunk_pos['alt'] = sample_alt_list
                    chunk_pos['time'] = t
                    chunk_pos['acid'] = acid
                    adsb_list.append(chunk_pos)
        target_pos = pd.concat(adsb_list)
        logging.info(f"Position work done")

        # Filtering for Comm-b data
        target_commb = target_commb[~((target_commb['is50']==False)&(target_commb['is60']==False))]
        target_commb = target_commb[~((target_commb['is50']==True)&(target_commb['is60']==True))]
        target_50 = target_commb[target_commb['is50']==True]
        target_60 = target_commb[target_commb['is60']==True]
        logging.info(f"Total data: len {len(target)}")
        logging.info(f"ADSB data: len {len(target_adsb)}")
        logging.info(f"Comm-B data: len {len(target_commb)}")
        logging.info(f"BDS50 data: len {len(target_50)}")
        logging.info(f"BDS60 data: len {len(target_60)}")

        # Get airborne data from Comm-b data
        target_50['acid'] = target_50['code'].apply(lambda x: icao(x))
        target_50['alt'] = target_50['code'].apply(lambda x: altcode(x))
        target_50['roll'] = target_50['code'].apply(lambda x: roll50(x))
        target_50['tta'] = target_50['code'].apply(lambda x: trk50(x))
        target_50['gspd'] = target_50['code'].apply(lambda x: gs50(x))
        target_50['tas'] = target_50['code'].apply(lambda x: tas50(x))

        target_60['acid'] = target_60['code'].apply(lambda x: icao(x))
        target_60['alt'] = target_60['code'].apply(lambda x: altcode(x))
        target_60['mhed'] = target_60['code'].apply(lambda x: hdg60(x))
        target_60['vr'] = target_60['code'].apply(lambda x: vr60ins(x))
        target_60['mach'] = target_60['code'].apply(lambda x: mach60(x))
        target_60['ias'] = target_60['code'].apply(lambda x: ias60(x))

        # Drop nan values
        target_50 = target_50.dropna(subset=['time', 'acid', 'tta', 'gspd', 'tas'])
        target_50 = target_50[['time', 'acid', 'alt', 'tta', 'gspd', 'tas', 'roll']]
        target_60 = target_60.dropna(subset=['time', 'acid', 'mhed'])
        target_60 = target_60[['time', 'acid', 'alt', 'mhed', 'ias', 'mach', 'vr']]

        # Merge BDS50 and 60
        target_info = pd.merge(target_50, target_60, how='inner',  on=['time', 'acid'])

        # Merge position and airborne data to produce merged data
        target_final = pd.merge(target_pos, target_info, how='inner', on=['time', 'acid'])
        final_cols = ['time', 'acid', 'alt', 'alt_x', 'alt_y', 'tta', 'gspd', 'tas', 'roll', 'ias', 'mach', 'vr']
        target_final = target_final[final_cols]
        logging.info(f"Final data: len {len(target_final)}")

        target_final.to_csv(f"{out_path}/{date}_{filename}")
        logging.info(f"Work done")

    except Exception as e:
        logging.critical(e, exc_info=True)
