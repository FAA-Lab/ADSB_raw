import numpy as np
import netCDF4 as nc4
import pandas as pd


def round_by_step(x, step):
    return np.round(np.round(x/step)*step, str(step)[::-1].find('.')+1)


def read_AMDAR_to_df(f):
    nc = nc4.Dataset(f)
    dtime = nc4.num2date(nc.variables['timeObs'][:],
                         nc.variables['timeObs'].units,
                         only_use_cftime_datetimes=False,
                         only_use_python_datetimes=True)
    time = pd.to_datetime(dtime)
    lat = pd.Series(nc.variables['latitude'][:])
    lon = pd.Series(nc.variables['longitude'][:])
    alt = pd.Series(nc.variables['altitude'][:])
    wdir = pd.Series(nc.variables['windDir'][:])
    wspd = pd.Series(nc.variables['windSpeed'][:])
    head = pd.Series(nc.variables['heading'][:])
    tas = pd.Series(nc.variables['trueAirSpeed'][:])
    tailNo = pd.Series(np.array(nc.variables['tailNumber'][:]).astype(object).sum(axis=1))
    ncdf = pd.DataFrame()
    ncdf['time'] = time
    ncdf['lat'] = lat
    ncdf['lon'] = lon
    ncdf['alt'] = alt * 3.28084  # m to ft
    ncdf['wdir'] = wdir
    ncdf['wspd'] = wspd
    ncdf['head'] = head
    ncdf['tas'] = tas
    ncdf['tailNo'] = tailNo
    return ncdf


def rms(x):
    return np.sqrt(np.sum(x**2)/len(x))


def spatial_filtered_groupby(df):
    df = df.dropna(how='any')
    meangroup = df.groupby(['time', 'lat', 'lon', 'lev']).mean()
    stdgroup = df.groupby(['time', 'lat', 'lon', 'lev']).apply(np.std)
    countgroup = df.groupby(['time', 'lat', 'lon', 'lev']).count()
    series_list = list()
    for vec in ['u', 'v']:
        arraygroup = df.groupby(['time', 'lat', 'lon', 'lev'])[vec].apply(np.array)
        for i, row in enumerate(arraygroup):
            arraygroup.iloc[i] = arraygroup.iloc[i][(arraygroup.iloc[i] > meangroup[vec][i] - stdgroup[vec][i])
                                                    & (arraygroup.iloc[i] < meangroup[vec][i] + stdgroup[vec][i])]
        arraygroup = arraygroup[countgroup[vec] > 10]
        series_list.append(arraygroup.apply(np.mean))
    return pd.concat(series_list, axis=1)


def read_ERA5_to_df(f):
    nc = nc4.Dataset(f)
    dtime = nc4.num2date(nc.variables['time'][:],
                         nc.variables['time'].units,
                         only_use_cftime_datetimes=False,
                         only_use_python_datetimes=True)
    time = pd.to_datetime(dtime)
    lat = pd.Series(nc.variables['latitude'][:])
    lon = pd.Series(nc.variables['longitude'][:])
    lev = pd.Series(nc.variables['level'][:])
    u = nc.variables['u'][:]
    v = nc.variables['v'][:]
    midx = pd.MultiIndex.from_product([time, lev, lat, lon], names=['time', 'lev', 'lat', 'lon'])
    df = pd.DataFrame(np.concatenate((u.reshape(-1, 1), v.reshape(-1, 1)), axis=1), index=midx, columns=['u', 'v'])
    df = df.reset_index()
    return df


def altitude_to_pressure(h):
    # Under the condition of ISA, International Standard Atmosphere
    # All variables follow SI unit (hpa, m, K)
    # meter to hPa
    p0 = 1013.25
    T0 = 288.15
    p11 = 226.32
    h11 = 11000.
    T11 = 216.65
    R = 287.04
    g = 9.80665
    # Below tropopause
    if h < 11000:
        p = p0*(1-0.0065*h/T0)**5.2561
    # Above tropopause
    else:
        p = p11*np.exp(-1*g*(h-h11)/R/T11)
    return p


def calc_geo_distance(in_lat1, in_lon1, in_lat2, in_lon2):
    # approximate radius of earth in km
    R = 6373.0

    lat1 = np.radians(in_lat1)
    lon1 = np.radians(in_lon1)
    lat2 = np.radians(in_lat2)
    lon2 = np.radians(in_lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    return R * c * 1000
