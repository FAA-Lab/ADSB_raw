import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as crs
from scipy.stats import linregress

from utils.util_compare import rms


def draw_bias_histogram(merged_df, i, comparison_target, target_year, out_path, time_resolution, thinning_method):
    hist_fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    merged_df[f'ugap{i}'].hist(bins=100, ax=axes[0][0])
    merged_df[f'vgap{i}'].hist(bins=100, ax=axes[0][1])
    merged_df[f'wspdgap{i}'].hist(bins=100, ax=axes[1][0])
    merged_df[f'wdirgap{i}'].hist(bins=100, ax=axes[1][1])
    axes[0][0].set_title('u')
    axes[0][1].set_title('v')
    axes[1][0].set_title('wspd')
    axes[1][1].set_title('wdir')
    hist_fig.suptitle(f'Bias histogram {comparison_target}, {target_year}')
    hist_fig.tight_layout()
    hist_fig.savefig(
        f"{out_path}/c{i}/{target_year}_bias_histogram_t{time_resolution}_{thinning_method}.png")


def draw_box_plot(merged_df, i, comparison_target, target_year, out_path, time_resolution, thinning_method):
    box_fig, axes = plt.subplots(1, 2, figsize=(12, 7), sharey=True)
    box_u = merged_df.groupby('lev')[f'ugap{i}'].apply(np.array).values
    box_u_avg = merged_df.groupby('lev')[f'ugap{i}'].mean().values
    box_v = merged_df.groupby('lev')[f'vgap{i}'].apply(np.array).values
    box_v_avg = merged_df.groupby('lev')[f'vgap{i}'].mean().values
    box_lev = merged_df.groupby('lev')[f'ugap{i}'].apply(np.array).index

    axes[0].plot(box_u_avg, box_lev, '--go')
    axes[0].set_ylim(200, 1050)
    axes[0].boxplot(box_u, widths=0.05, positions=box_lev,
                    vert=False,
                    flierprops=dict(marker='.', markerfacecolor='k', markersize=2, linestyle='none')
                    )
    axes[0].set_ylabel("pressure (hPa)")
    axes[0].set_xlabel("u (m/s)")

    axes[1].plot(box_v_avg, box_lev, '--go')
    axes[1].boxplot(box_v, widths=0.05, positions=box_lev,
                    vert=False,
                    flierprops=dict(marker='.', markerfacecolor='k', markersize=2, linestyle='none')
                    )
    axes[1].set_xlabel("v (m/s)")

    count_ax = axes[1].twinx()
    count_ax.set_ylim(200, 1050)
    count_ax.set_yticks(box_lev)
    count_ax.set_yticklabels([len(x) for x in box_u])
    axes[0].invert_yaxis()
    count_ax.invert_yaxis()

    # If ytick index is too dense for visualizing
    # for ytick_index, label in enumerate(reversed(axes[0].get_yticklabels())):
    #     if ytick_index % 3 == 0:
    #         pass
    #     else:
    #         label.set_visible(False)
    box_fig.suptitle(f'{comparison_target} Bias box plot, {target_year}')
    box_fig.tight_layout()
    box_fig.savefig(
        f"{out_path}/c{i}/{target_year}_uvbox_t{time_resolution}_{thinning_method}.png")


def draw_scatter_plot(merged_df, i, suffix_list, suffix_name_list,
                      comparison_target, target_year, out_path, time_resolution, thinning_method):
    scatter_fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    for j, scatter_target in enumerate(['u', 'v', 'wspd']):
        x = merged_df[f'{scatter_target}{suffix_list[i // 3]}']
        y = merged_df[f'{scatter_target}{suffix_list[i % 3 + (i // 3) * 2]}']
        slope, intercept, r_value, p_value, std_err = linregress(x, y)
        axes[j].scatter(x, y, c='k', s=1)
        axes[j].plot(np.linspace(np.min(x), np.max(x), 3), np.linspace(np.min(x), np.max(x), 3), c='r', lw=0.7)
        axes[j].set_xlim(np.min(x), np.max(x))
        axes[j].set_ylim(np.min(x), np.max(x))
        axes[j].set_xlabel(f'{scatter_target}, {suffix_name_list[i // 3]}')
        axes[j].set_ylabel(f'{scatter_target}, {suffix_name_list[i % 3 + (i // 3) * 2]}')
        axes[j].text(np.min(x), np.max(x),
                     f' slope: {slope},\n R^2: {r_value},\n RMSE: {std_err}',
                     bbox=dict(boxstyle="square",
                               fc=(1., 1., 1.))
                     )
    scatter_fig.suptitle(f'{comparison_target} Scatter plot, {target_year}')
    scatter_fig.savefig(
        f"{out_path}/c{i}/{target_year}_scatter_t{time_resolution}_{thinning_method}.png")


def draw_bias_rms(merged_df, target_year, out_path, time_resolution, thinning_method):
    lev_fig, axes = plt.subplots(1, 2, figsize=(12, 7), sharey=True)
    axes[0].plot(merged_df.groupby('lev')['ugap1'].apply(rms).values,
                 merged_df.groupby('lev')['ugap1'].apply(rms).index,
                 'k^--', lw=1.3)
    axes[0].plot(merged_df.groupby('lev')['ugap1'].mean().values,
                 merged_df.groupby('lev')['ugap1'].mean().index,
                 'k^-')
    axes[0].plot(merged_df.groupby('lev')['ugap2'].apply(rms).values,
                 merged_df.groupby('lev')['ugap2'].apply(rms).index,
                 'kx--', lw=1.3)
    axes[0].plot(merged_df.groupby('lev')['ugap2'].mean().values,
                 merged_df.groupby('lev')['ugap2'].mean().index,
                 'kx-')
    axes[0].plot(merged_df.groupby('lev')['ugap3'].apply(rms).values,
                 merged_df.groupby('lev')['ugap3'].apply(rms).index,
                 'ko--', lw=1.3)
    axes[0].plot(merged_df.groupby('lev')['ugap3'].mean().values,
                 merged_df.groupby('lev')['ugap3'].mean().index,
                 'ko-')
    axes[0].set_xlabel('u (m/s)')
    axes[0].set_ylabel('pressure (hPa)')

    axes[1].plot(merged_df.groupby('lev')['vgap1'].apply(rms).values,
                 merged_df.groupby('lev')['vgap1'].apply(rms).index,
                 'k^--', lw=1.3)
    axes[1].plot(merged_df.groupby('lev')['vgap1'].mean().values,
                 merged_df.groupby('lev')['vgap1'].mean().index,
                 'k^-')
    axes[1].plot(merged_df.groupby('lev')['vgap2'].apply(rms).values,
                 merged_df.groupby('lev')['vgap2'].apply(rms).index,
                 'kx--', lw=1.3)
    axes[1].plot(merged_df.groupby('lev')['vgap2'].mean().values,
                 merged_df.groupby('lev')['vgap2'].mean().index,
                 'kx-')
    axes[1].plot(merged_df.groupby('lev')['vgap3'].apply(rms).values,
                 merged_df.groupby('lev')['vgap3'].apply(rms).index,
                 'ko--', lw=1.3)
    axes[1].plot(merged_df.groupby('lev')['vgap3'].mean().values,
                 merged_df.groupby('lev')['vgap3'].mean().index,
                 'ko-')
    axes[1].set_xlabel('v (m/s)')
    axes[0].invert_yaxis()
    lev_fig.suptitle(f'Bias and RMS, {target_year} triple collocations')
    lev_fig.tight_layout()
    lev_fig.savefig(
        f"{out_path}/{target_year}_uvlev_t{time_resolution}_{thinning_method}.png")


def draw_map(merged_df, target_year, out_path, time_resolution, thinning_method):
    x = merged_df["lon"]
    y = merged_df["lat"]

    left, width = 0.1, 0.9
    bottom, height = 0.1, 0.6
    spacing = 0.005

    rect_scatter = [left, bottom, width, height]
    rect_histx = [left, bottom + height + spacing, width, 0.2]
    rect_histy = [left + width + spacing, bottom, 0.2, height]

    fig = plt.figure(figsize=(8, 8))

    ax_scatter = plt.axes(rect_scatter, projection=crs.PlateCarree())
    ax_scatter.tick_params(direction='in', top=True, right=True)
    ax_scatter.coastlines(resolution='110m')
    ax_scatter.gridlines(crs=crs.PlateCarree(), draw_labels=True)
    cm = plt.cm.get_cmap('jet')

    ax_histx = plt.axes(rect_histx)
    ax_histx.tick_params(direction='in', labelbottom=False)
    ax_histy = plt.axes(rect_histy)
    ax_histy.tick_params(direction='in', labelleft=False)

    # the scatter plot:
    ax_scatter.scatter(x,
                       y,
                       c=merged_df['lev'],
                       s=2,
                       cmap=cm,
                       transform=crs.PlateCarree())

    ax_scatter.set_xlim((120, 135))
    ax_scatter.set_ylim((30, 40))
    ax_histx.hist(x, bins=np.arange(120, 135+0.25, 0.25), color='k')
    ax_histy.hist(y, bins=np.arange(30, 40+0.25, 0.25), orientation='horizontal', color='k')
    ax_histx.set_xlim(ax_scatter.get_xlim())
    ax_histy.set_ylim(ax_scatter.get_ylim())

    plt.title(f'{target_year} \n map (triple), \n total point: {len(merged_df)}', loc='right')
    fig.savefig(
        f'{out_path}/{target_year}_map_t{time_resolution}_{thinning_method}.png', bbox_inches='tight')


def draw_jerk_scatter_plot(merged_df, out_path, time_resolution, thinning_method):
    fig1 = plt.figure(figsize=(8, 8))
    x = merged_df['vsr_jerk'].values
    y = merged_df['grav_jerk'].values
    x = (x - x.min()) / (x.max() - x.min())
    y = (y - y.min()) / (y.max() - y.min())
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    plt.scatter(x, y, c='k', s=1)
    # plt.hist2d(x,y, bins=np.linspace(0,1,50), cmap=plt.cm.Greys)
    plt.plot(np.linspace(0, 1, 3), np.linspace(1, 0, 3), c='r', lw=0.7)
    plt.xlim(np.min(x), np.max(x))
    plt.ylim(np.min(x), np.max(x))
    plt.xlabel('vsr_jerk')
    plt.ylabel('grav_jerk')
    plt.text(np.min(x), np.max(x),
             f' slope: {slope},\n R^2: {r_value},\n RMSE: {std_err}',
             bbox=dict(boxstyle="square",
                       fc=(1., 1., 1.))
             )
    fig1.suptitle(f'Scatter plot')
    fig1.savefig(f"{out_path}/scatter_vsr_grav_t{time_resolution}_{thinning_method}.png")

    fig2 = plt.figure(figsize=(8, 8))
    x = merged_df['vsr_jerk'].values
    y = merged_df['vr_jerk'].values
    x = (x - x.min()) / (x.max() - x.min())
    y = (y - y.min()) / (y.max() - y.min())
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    plt.scatter(x, y, c='k', s=1)
    # plt.hist2d(x,y, bins=np.linspace(0,1,50), cmap=plt.cm.Greys)
    plt.plot(np.linspace(0, 1, 3), np.linspace(0, 1, 3), c='r', lw=0.7)
    plt.xlim(np.min(x), np.max(x))
    plt.ylim(np.min(x), np.max(x))
    plt.xlabel('vsr_jerk')
    plt.ylabel('vr_jerk')
    plt.text(np.min(x), np.max(x),
             f' slope: {slope},\n R^2: {r_value},\n RMSE: {std_err}',
             bbox=dict(boxstyle="square",
                       fc=(1., 1., 1.))
             )
    fig2.suptitle(f'Scatter plot')
    fig2.savefig(f"{out_path}/scatter_vsr_vr_t{time_resolution}_{thinning_method}.png")

    fig3 = plt.figure(figsize=(8, 8))
    x = merged_df['vsr_jerk'].values
    y = merged_df['ivv_jerk'].values
    x = (x - x.min()) / (x.max() - x.min())
    y = (y - y.min()) / (y.max() - y.min())
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    plt.scatter(x, y, c='k', s=1)
    # plt.hist2d(x,y, bins=np.linspace(0,1,50), cmap=plt.cm.Greys)
    plt.plot(np.linspace(0, 1, 3), np.linspace(0, 1, 3), c='r', lw=0.7)
    plt.xlim(np.min(x), np.max(x))
    plt.ylim(np.min(x), np.max(x))
    plt.xlabel('vsr_jerk')
    plt.ylabel('ivv_jerk')
    plt.text(np.min(x), np.max(x),
             f' slope: {slope},\n R^2: {r_value},\n RMSE: {std_err}',
             bbox=dict(boxstyle="square",
                       fc=(1., 1., 1.))
             )
    fig3.suptitle(f'Scatter plot')
    fig3.savefig(f"{out_path}/scatter_vsr_ivv_t{time_resolution}_{thinning_method}.png")

    fig4 = plt.figure(figsize=(8, 8))
    x = merged_df['vr_jerk'].values
    y = merged_df['ivv_jerk'].values
    x = (x - x.min()) / (x.max() - x.min())
    y = (y - y.min()) / (y.max() - y.min())
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    plt.scatter(x, y, c='k', s=1)
    # plt.hist2d(x,y, bins=np.linspace(0,1,50), cmap=plt.cm.Greys)
    plt.plot(np.linspace(0, 1, 3), np.linspace(0, 1, 3), c='r', lw=0.7)
    plt.xlim(np.min(x), np.max(x))
    plt.ylim(np.min(x), np.max(x))
    plt.xlabel('vr_jerk')
    plt.ylabel('ivv_jerk')
    plt.text(np.min(x), np.max(x),
             f' slope: {slope},\n R^2: {r_value},\n RMSE: {std_err}',
             bbox=dict(boxstyle="square",
                       fc=(1., 1., 1.))
             )
    fig4.suptitle(f'Scatter plot')
    fig4.savefig(f"{out_path}/scatter_vr_ivv_t{time_resolution}_{thinning_method}.png")
