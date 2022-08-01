import numpy as np

def calc_gspd_vector(gspd, tta):
    return np.array((gspd*np.sin(np.pi/180.*tta), gspd*np.cos(np.pi/180.*tta)))


def calc_tas_vector(tas, mhed):
    return np.array((tas*np.sin(np.pi/180.*(mhed-8)), tas*np.cos(np.pi/180.*(mhed-8))))


def calc_wspd(u, v):
    return (u**2+v**2)**0.5


def calc_wdir(u, v):
    u[u == 0] += 0.0000001
    v[v == 0] += 0.0000001
    return np.where(u > 0, 270.-np.arctan(v/u)*180./np.pi, 90.-np.arctan(v/u)*180./np.pi)


def calculate(chunk):
    u, v = calc_gspd_vector(chunk['gspd'], chunk['tta']) - calc_tas_vector(chunk['tas'], chunk['mhed'])
    chunk['wspd'] = calc_wspd(u, v)
    chunk['wdir'] = calc_wdir(u, v)
    return chunk
