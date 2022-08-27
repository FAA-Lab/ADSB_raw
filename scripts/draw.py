import pandas as pd
import numpy as np
import logging

from utils.util_fig import draw_bias_histogram, draw_box_plot, draw_scatter_plot, draw_bias_rms, draw_map

time_resolution = '60min'
lat_resolution = 0.25
lon_resolution = 0.25
lev_resolution = 25
thinning_method = 'mean'

comparison_list = ['(AMDAR - ERA5)', '(ADSB - ERA5)', '(ADSB - AMDAR)']
suffix_list = ['', '_y', '_x']
suffix_name_list = ['ERA5', 'AMDAR', 'ADSB']

for target_year in [2020, 2021, 2022]:
    merged_df = pd.read_csv(f'../results/triple_compare_merged_{target_year}_220805.csv', index_col=0)
    merged_df['time'] = pd.to_datetime(merged_df['time'])
    out_path = f"../results/{target_year}_triple_compare_220805"

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
