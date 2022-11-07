import numpy as np
import pandas as pd
from scipy import signal
import matplotlib.pyplot as plt

def calculate_edr2(data, window_size=30):
    data["U"] = (-1) * (np.cos((np.pi / 180) * (90 - data["wdir"]))) * data["wspd"]
    data["V"] = (-1) * (np.sin((np.pi / 180) * (90 - data["wdir"]))) * data["wspd"]

    # Calculate PSD with periodogram
    # Window = 60-seconds, symetrically (i.e. -30 seconds < calc_time < +30 seconds)
    # with Hanning function applied. No overlap and no subwindow was used.
    uwnd = data["U"]  # U-wind data [m/s]
    vwnd = data["V"]  # V-wind data [m/s]
    TAS = data["tas"]  # True airspeed [m/s]

    tlen = window_size  # Window size
    psdlen = tlen // 2 + 1  # Length of PSD, i.e the number of frequencies
    # (below Nyquist frequency)
    ti = len(data) - tlen  # Number of times to calculate EDR2
    f_b = 0.1  # Bound frequency for inertial subrange(fixed with 0.1Hz)
    f_b_ind = -1

    # Kolmogorov constant (from Strauss et al. 2015)
    alpha_u = 0.53
    alpha_v = 0.707

    freq_u = np.zeros((ti, psdlen), np.float64)
    freq_v = np.zeros((ti, psdlen), np.float64)
    fi_u = np.zeros((ti, psdlen), np.float64)
    fi_v = np.zeros((ti, psdlen), np.float64)

    kolmogorov_line_u = np.zeros(ti, np.float64)
    kolmogorov_line_v = np.zeros(ti, np.float64)
    EDR2_u = np.zeros(ti, np.float64)
    EDR2_v = np.zeros(ti, np.float64)

    delta_t = int(tlen / 2)  # Symmetric main window

    psd_start_ind = 0 + delta_t
    psd_end_ind = len(data) - delta_t

    t_start = psd_start_ind
    t_calc = np.arange(psd_start_ind, psd_end_ind, 1)

    assert (t_calc.size == ti)

    for i in range(ti):
        t_now = t_calc[i]
        freq_u[i, :], fi_u[i, :] = signal.periodogram(uwnd[t_now - delta_t:t_now + delta_t], fs=1.0)
        freq_v[i, :], fi_v[i, :] = signal.periodogram(vwnd[t_now - delta_t:t_now + delta_t], fs=1.0)

        # Find the bound frequency index, which is the most closest number to 0.1Hz
        f_b_ind = np.abs(freq_u[i, :] - f_b).argmin()
        # Prepare V for Taylor's frozen hypothesis
        V = np.mean(TAS[t_now - delta_t:t_now + delta_t])
        # Use Equation 3 in Munoz-Esparza et al. 2018 to calculate EDR2
        kolmogorov_line_u[i] = np.mean((np.power(freq_u[i, f_b_ind:], 5 / 3)) * fi_u[i, f_b_ind:])
        kolmogorov_line_v[i] = np.mean((np.power(freq_v[i, f_b_ind:], 5 / 3)) * fi_u[i, f_b_ind:])
        EDR2_u[i] = ((2 * np.pi) / V) ** (1 / 3) * (kolmogorov_line_u[i] / alpha_u) ** (1 / 2)
        EDR2_v[i] = ((2 * np.pi) / V) ** (1 / 3) * (kolmogorov_line_v[i] / alpha_v) ** (1 / 2)

    exp10 = np.vectorize(lambda x: 10 ** x)  # Define vectorized 10^(x) function, for NumPy array

    kolmogorov_line_u += 1e-20  # Prevent trying to calculate log(0)
    kolmogorov_line_v += 1e-20  # Prevent trying to calculate log(0)
    EDR2_u = EDR2_u + 1e-20  # Prevent trying to calculate log(0)
    EDR2_v = EDR2_v + 1e-20  # Prevent trying to calculate log(0)
    EDR2_mean = exp10((np.log10(EDR2_u) + np.log10(EDR2_v)) / 2)  # Calculate log-mean of EDR2 of each wind component

    data['dU'] = data['U'] - data['U'].rolling(10, center=True, min_periods=1).mean()
    data['dV'] = data['V'] - data['V'].rolling(10, center=True, min_periods=1).mean()
    data['TKE'] = 0.5 * (data['dU'] ** 2 + data['dV'] ** 2) ** 0.5
    data['EDR1'] = ((0.84 / np.mean(data['tas'])) * (data['TKE'] ** 1.5)) ** 0.33

    data2 = data[psd_start_ind:psd_end_ind].copy()
    data2['EDR2_u'] = EDR2_u
    data2['EDR2_v'] = EDR2_v
    data2['EDR2_mean'] = EDR2_mean
    return data2


def draw_edr2(data_i, fig_out_path):
    # Draw PSD_u.
    fig = plt.figure(dpi=100)
    plt.ylabel("S$_u$ [$\mathrm{{m^2}{s^{-1}}}$]")
    plt.xlabel("Frequency [$\mathrm{s^{-1}}$]")
    plt.xlim(left=freq_u[0, 1], right=freq_u[0, -1])
    plt.ylim(0.001, 100)
    plt.xscale("log")
    plt.yscale("log")
    for i in range(ti):
        plt.plot(freq_u[i, :], fi_u[i, :])
    fig.savefig(f'{fig_out_path}/PSD_u_{data_i}.png')


def calculate_jerk(data):
    data['dt'] = data['time'].diff(1)
    data['dt'] = data['dt'].dt.total_seconds()
    data['dvr'] = data['vr'].diff(1)
    data['vr_acc'] = data['dvr'] / data['dt']
    data['vr_jerk'] = data['vr_acc'].diff(1) / data['dt']
    data = data[data['dt'] != 0.]
    return data