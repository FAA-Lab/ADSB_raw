import glob
import pandas as pd
import numpy as np
from functools import reduce
import logging
import argparse
import datetime

from utils.util_compare import round_by_step, read_AMDAR_to_df, read_ERA5_to_df, altitude_to_pressure, calc_geo_distance
from utils.util_fig import draw_bias_histogram, draw_box_plot, draw_scatter_plot, draw_bias_rms, draw_map
from utils.wind import calc_wspd, calc_wdir

parser = argparse.ArgumentParser(description='Triple Comparing Work')
parser.add_argument('--year', dest='target_year', default='2020', type=str)
parser.add_argument('--time', dest='time_resolution', default='60min', type=str)
parser.add_argument('--lat', dest='lat_resolution', default=0.25, type=float)
parser.add_argument('--lon', dest='lon_resolution', default=0.25, type=float)
parser.add_argument('--lev', dest='lev_resolution', default=25, type=int)
parser.add_argument('--method', dest='thinning_method', default='mean', type=str)
parser.add_argument('--wind_based_on', dest='wind_based_on', default='BDS60', type=str)

target_year = str(parser.parse_args().target_year)
time_resolution = parser.parse_args().time_resolution
lat_resolution = parser.parse_args().lat_resolution
lon_resolution = parser.parse_args().lon_resolution
lev_resolution = parser.parse_args().lev_resolution
thinning_method = parser.parse_args().thinning_method
wind_based_on = parser.parse_args().wind_based_on
# print(parser.parse_args())

log_path = "../log"
logging.basicConfig(filename=f"{log_path}/{target_year}_triple_compare.log",
                    filemode='a',
                    format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


ADSB_path = f"/data3/storage/ADSB/QCdone"
out_path = f"../results/{target_year}_triple_compare_220805"

AMDAR_path = f"/home/kjmv/MADIS_AMDAR"
ERA5_path = "/data2/share/ADSB_Calculation"

logging.info(f'Start comparing: ')
logging.info(f'method:  {thinning_method}')
logging.info(f'month:   {target_year}')
logging.info(f'time:    {time_resolution}')
logging.info(f'lat:     {lat_resolution}')
logging.info(f'lon:     {lon_resolution}')
logging.info(f'lev:     {lev_resolution}')

try:
    ERA5list = list()
    for f in glob.glob(f"{ERA5_path}/*{target_year}*"):
        Edf = read_ERA5_to_df(f)
        Edf = Edf[(Edf['lat'] < 40) & (Edf['lat'] > 30) & (Edf['lon'] > 120) & (Edf['lon'] < 135)]
        ERA5list.append(Edf)
    ERA5df = pd.concat(ERA5list)
    # ERA5df.to_csv(f'{out_path}/era5_211115.csv')
    logging.info('ERA5 read done')

    ADSBlist = list()
    for f in glob.glob(f"{ADSB_path}/FAAL_ADSB_{target_year}*"):
        sub_df = pd.read_csv(f, index_col=0)
        #        sub_df.rename(columns={'mhed_new':'mhed'}, inplace=True)
        sub_df = sub_df[sub_df['mhed'] != 0.]
        sub_df = sub_df[sub_df['tas'] != 0.]
        sub_df = sub_df.groupby(['time', 'acid', 'alt', 'lat', 'lon']).mean().reset_index()
        ADSBlist.append(sub_df)
    ADSBdf = pd.concat(ADSBlist)

    ADSBdf['time'] = pd.to_datetime(ADSBdf['time'])
    # LST to UTC
    ADSBdf['time'] = ADSBdf['time'] - datetime.timedelta(hours=9)

    ADSBdf = ADSBdf[ADSBdf['mhed']!=0.]
    ADSBdf = ADSBdf[ADSBdf['tas']!=0.]

    ADSBdf.to_csv(f'{out_path}/adsb_{target_year}_220805.csv')
    logging.info('ADS-B read done')

#    aciddf = pd.read_csv('../acid_use.csv', index_col=0)
#    ADSBdf = pd.merge(ADSBdf, aciddf, how='left', on='acid')
#    ADSBdf = ADSBdf.dropna(subset=['actype_big'])

    AMDARlist = list()
    for f in glob.glob(f"{AMDAR_path}/{target_year}*/**/*.nc"):
        ncdf = read_AMDAR_to_df(f)
        #        ncdf = ncdf.dropna(how='any')
        AMDARlist.append(ncdf)
    AMDARdf = pd.concat(AMDARlist)
    AMDARdf = AMDARdf[(AMDARdf['lat'] < 40) & (AMDARdf['lat'] > 30) & (AMDARdf['lon'] > 120) & (AMDARdf['lon'] < 135)]
    AMDARdf.to_csv(f'{out_path}/amdar_{target_year}_220805.csv')
    logging.info('AMDAR read done')

    if thinning_method == 'mean':
        ADSBdf['time'] = ADSBdf['time'].dt.round(time_resolution)
        ADSBdf['lat'] = ADSBdf['lat'].apply(lambda x: round_by_step(x, lat_resolution))
        ADSBdf['lon'] = ADSBdf['lon'].apply(lambda x: round_by_step(x, lon_resolution))
        ADSBdf['lev'] = (ADSBdf['alt'] * 0.3048).apply(altitude_to_pressure)
        ADSBdf['lev'] = ADSBdf['lev'].apply(lambda x: round_by_step(x, lev_resolution))
        ADSBdf['u'] = ADSBdf['wspd'] * np.cos((-90 - ADSBdf['wdir']) / 180 * np.pi)
        ADSBdf['v'] = ADSBdf['wspd'] * np.sin((-90 - ADSBdf['wdir']) / 180 * np.pi)
        ADSBdf = ADSBdf[['time', 'lat', 'lon', 'lev', 'u', 'v']]
        logging.info('ADSB calc done')

        AMDARdf['time'] = AMDARdf['time'].dt.round(time_resolution)
        AMDARdf['lat'] = AMDARdf['lat'].apply(lambda x: round_by_step(x, lat_resolution))
        AMDARdf['lon'] = AMDARdf['lon'].apply(lambda x: round_by_step(x, lon_resolution))
        AMDARdf['lev'] = (AMDARdf['alt'] * 0.3048).apply(altitude_to_pressure)
        AMDARdf['lev'] = AMDARdf['lev'].apply(lambda x: round_by_step(x, lev_resolution))
        AMDARdf['u'] = AMDARdf['wspd'] * np.cos((-90 - AMDARdf['wdir']) / 180 * np.pi)
        AMDARdf['v'] = AMDARdf['wspd'] * np.sin((-90 - AMDARdf['wdir']) / 180 * np.pi)
        AMDARdf = AMDARdf[['time', 'lat', 'lon', 'lev', 'u', 'v']]
        logging.info('AMDAR calc done')

        ADSBdf = ADSBdf.groupby(['time', 'lat', 'lon', 'lev']).mean().reset_index()
        logging.info(f'ADSB length: {len(ADSBdf)}')
        AMDARdf = AMDARdf.groupby(['time', 'lat', 'lon', 'lev']).mean().reset_index()
        logging.info(f'AMDAR length: {len(AMDARdf)}')

    elif thinning_method == 'closest':
        ADSBdf['time_grid'] = ADSBdf['time'].dt.round('10min')
        ADSBdf['lat_grid'] = ADSBdf['lat'].apply(lambda x: round_by_step(x, lat_resolution))
        ADSBdf['lon_grid'] = ADSBdf['lon'].apply(lambda x: round_by_step(x, lon_resolution))
        ADSBdf['lev'] = (ADSBdf['alt'] * 0.3048).apply(altitude_to_pressure)
        ADSBdf['lev'] = ADSBdf['lev'].apply(lambda x: round_by_step(x, lev_resolution))
        ADSBdf['u'] = ADSBdf['wspd'] * np.cos((-90 - ADSBdf['wdir']) / 180 * np.pi)
        ADSBdf['v'] = ADSBdf['wspd'] * np.sin((-90 - ADSBdf['wdir']) / 180 * np.pi)
        ADSBdf = ADSBdf[['time', 'time_grid', 'lat', 'lat_grid', 'lon', 'lon_grid', 'lev', 'u', 'v']]
        logging.info('ADSB calc done')

        AMDARdf['time_grid'] = AMDARdf['time'].dt.round('10min')
        AMDARdf['lat_grid'] = AMDARdf['lat'].apply(lambda x: round_by_step(x, lat_resolution))
        AMDARdf['lon_grid'] = AMDARdf['lon'].apply(lambda x: round_by_step(x, lon_resolution))
        AMDARdf['lev'] = (AMDARdf['alt'] * 0.3048).apply(altitude_to_pressure)
        AMDARdf['lev'] = AMDARdf['lev'].apply(lambda x: round_by_step(x, lev_resolution))
        AMDARdf['u'] = AMDARdf['wspd'] * np.cos((-90 - AMDARdf['wdir']) / 180 * np.pi)
        AMDARdf['v'] = AMDARdf['wspd'] * np.sin((-90 - AMDARdf['wdir']) / 180 * np.pi)
        AMDARdf = AMDARdf[['time', 'time_grid', 'lat', 'lat_grid', 'lon', 'lon_grid', 'lev', 'u', 'v']]
        logging.info('AMDAR calc done')

        ADSBdf['dist'] = calc_geo_distance(ADSBdf['lat'], ADSBdf['lon'], ADSBdf['lat_grid'], ADSBdf['lon_grid'])
        ADSBdf = ADSBdf.groupby(['time_grid', 'lat_grid', 'lon_grid', 'lev']).min('dist')[['u', 'v']]
        ADSBdf = ADSBdf.reset_index().rename(columns={'time_grid': 'time', 'lat_grid': 'lat', 'lon_grid': 'lon'})
        logging.info(f'ADSB length: {len(ADSBdf)}')
        AMDARdf['dist'] = calc_geo_distance(AMDARdf['lat'], AMDARdf['lon'], AMDARdf['lat_grid'], AMDARdf['lon_grid'])
        AMDARdf = AMDARdf.groupby(['time_grid', 'lat_grid', 'lon_grid', 'lev']).min('dist')[['u', 'v']]
        AMDARdf = AMDARdf.reset_index().rename(columns={'time_grid': 'time', 'lat_grid': 'lat', 'lon_grid': 'lon'})
        logging.info(f'AMDAR length: {len(AMDARdf)}')

    merged_df = reduce(lambda left, right:
                       pd.merge(left, right, how='inner', on=['time', 'lat', 'lon', 'lev']),
                       [ADSBdf, AMDARdf, ERA5df])
    merged_df = merged_df.dropna(how='any')
    logging.info(f'merge done')
    logging.info(f'merged length: {len(merged_df)}')
    # suffix: {ADSB: _x, AMDAR: _y, ERA5: none}

    # gap1 : AMDAR - ERA5
    # gap2 : ADSB - ERA5
    # gap3 : ADSB - AMDAR
    merged_df['ugap1'] = merged_df['u_y'] - merged_df['u']
    merged_df['ugap2'] = merged_df['u_x'] - merged_df['u']
    merged_df['ugap3'] = merged_df['u_x'] - merged_df['u_y']

    merged_df['vgap1'] = merged_df['v_y'] - merged_df['v']
    merged_df['vgap2'] = merged_df['v_x'] - merged_df['v']
    merged_df['vgap3'] = merged_df['v_x'] - merged_df['v_y']

    merged_df['wspd_x'] = calc_wspd(merged_df['u_x'], merged_df['v_x'])
    merged_df['wdir_x'] = calc_wdir(merged_df['u_x'], merged_df['v_x'])
    merged_df['wspd_y'] = calc_wspd(merged_df['u_y'], merged_df['v_y'])
    merged_df['wdir_y'] = calc_wdir(merged_df['u_y'], merged_df['v_y'])
    merged_df['wspd'] = calc_wspd(merged_df['u'], merged_df['v'])
    merged_df['wdir'] = calc_wdir(merged_df['u'], merged_df['v'])

    merged_df['wspdgap1'] = merged_df['wspd_y'] - merged_df['wspd']
    merged_df['wspdgap2'] = merged_df['wspd_x'] - merged_df['wspd']
    merged_df['wspdgap3'] = merged_df['wspd_x'] - merged_df['wspd_y']

    merged_df['wdirgap1'] = merged_df['wdir_y'] - merged_df['wdir']
    merged_df['wdirgap2'] = merged_df['wdir_x'] - merged_df['wdir']
    merged_df['wdirgap3'] = merged_df['wdir_x'] - merged_df['wdir_y']

    merged_df['wdirgap1'] = merged_df['wdirgap1'].apply(lambda x: x - 360 if x > 180 else (x if x > -180 else x + 360))
    merged_df['wdirgap2'] = merged_df['wdirgap2'].apply(lambda x: x - 360 if x > 180 else (x if x > -180 else x + 360))
    merged_df['wdirgap3'] = merged_df['wdirgap3'].apply(lambda x: x - 360 if x > 180 else (x if x > -180 else x + 360))

    logging.info(f'final calc done')

    comparison_list = ['(AMDAR - ERA5)', '(ADSB - ERA5)', '(ADSB - AMDAR)']
    suffix_list = ['', '_y', '_x']
    suffix_name_list = ['ERA5', 'AMDAR', 'ADSB']

    for i, comparison_target in enumerate(comparison_list):
        i += 1
        # Fig 1
        # Bias Histogram
        draw_bias_histogram(merged_df, i, comparison_target, target_year, out_path, time_resolution, thinning_method)
        logging.info(f'{comparison_target} draw hist done')

        # Fig 2
        # Altitude Box Plot
        draw_box_plot(merged_df, i, comparison_target, target_year, out_path, time_resolution, thinning_method)
        logging.info(f'{comparison_target} draw box done')

        # Fig 5
        # Scatter plot
        draw_scatter_plot(merged_df, i, suffix_list, suffix_name_list,
                          comparison_target, target_year, out_path, time_resolution, thinning_method)
        logging.info(f'{comparison_target} draw scatter done')

    # Fig 3
    # Altitude Bias and RMS
    draw_bias_rms(merged_df, target_year, out_path, time_resolution, thinning_method)
    logging.info(f'Draw level done')

    # Fig 4
    # map
    draw_map(merged_df, target_year, out_path, time_resolution, thinning_method)
    logging.info(f'draw map done')

    merged_df.to_csv(f'{out_path}/triple_compare_merged_{target_year}_220805.csv')

except Exception as e:
    logging.critical(e, exc_info=True)
