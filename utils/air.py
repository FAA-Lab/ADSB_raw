import numpy as np

from utils.constants import *


def atmos(H):
    # H in metres
    T = np.maximum(288.15 - 0.0065 * H, 216.65)
    rhotrop = 1.225 * (T / 288.15) ** 4.256848030018761
    dhstrat = np.maximum(0.0, H - 11000.0)
    rho = rhotrop * np.exp(-dhstrat / 6341.552161)
    p = rho * R * T
    return p, rho, T


def temperature(H):
    p, r, T = atmos(H)
    return T


def pressure(H):
    p, r, T = atmos(H)
    return p


def density(H):
    p, r, T = atmos(H)
    return r


def vsound(H):
    """Speed of sound"""
    T = temperature(H)
    a = np.sqrt(gamma * R * T)
    return a


def distance(lat1, lon1, lat2, lon2, H=0):
    """
    Compute spherical distance from spherical coordinates.
    For two locations in spherical coordinates
    (1, theta, phi) and (1, theta', phi')
    cosine( arc length ) =
       sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    distance = rho * arc length
    """

    # phi = 90 - latitude
    phi1 = np.radians(90 - lat1)
    phi2 = np.radians(90 - lat2)

    # theta = longitude
    theta1 = np.radians(lon1)
    theta2 = np.radians(lon2)

    cos = np.sin(phi1) * np.sin(phi2) * np.cos(theta1 - theta2) + np.cos(phi1) * np.cos(
        phi2
    )
    cos = np.where(cos > 1, 1, cos)

    arc = np.arccos(cos)
    dist = arc * (r_earth + H)  # meters, radius of earth
    return dist


def bearing(lat1, lon1, lat2, lon2):
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)
    x = np.sin(lon2 - lon1) * np.cos(lat2)
    y = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(lon2 - lon1)
    initial_bearing = np.arctan2(x, y)
    initial_bearing = np.degrees(initial_bearing)
    bearing = (initial_bearing + 360) % 360
    return bearing


# -----------------------------------------------------
# Speed conversions, altitude H all in meters
# -----------------------------------------------------
def tas2mach(Vtas, H):
    """True Airspeed to Mach number"""
    a = vsound(H)
    Mach = Vtas / a
    return Mach


def mach2tas(Mach, H):
    """Mach number to True Airspeed"""
    a = vsound(H)
    Vtas = Mach * a
    return Vtas


def eas2tas(Veas, H):
    """Equivalent Airspeed to True Airspeed"""
    rho = density(H)
    Vtas = Veas * np.sqrt(rho0 / rho)
    return Vtas


def tas2eas(Vtas, H):
    """True Airspeed to Equivalent Airspeed"""
    rho = density(H)
    Veas = Vtas * np.sqrt(rho / rho0)
    return Veas


def cas2tas(Vcas, H):
    """Calibrated Airspeed to True Airspeed"""
    p, rho, T = atmos(H)
    qdyn = p0 * ((1 + rho0 * Vcas * Vcas / (7 * p0)) ** 3.5 - 1.0)
    Vtas = np.sqrt(7 * p / rho * ((1 + qdyn / p) ** (2 / 7.0) - 1.0))
    return Vtas


def tas2cas(Vtas, H):
    """True Airspeed to Calibrated Airspeed"""
    p, rho, T = atmos(H)
    qdyn = p * ((1 + rho * Vtas * Vtas / (7 * p)) ** 3.5 - 1.0)
    Vcas = np.sqrt(7 * p0 / rho0 * ((qdyn / p0 + 1.0) ** (2 / 7.0) - 1.0))
    return Vcas


def mach2cas(Mach, H):
    """Mach number to Calibrated Airspeed"""
    Vtas = mach2tas(Mach, H)
    Vcas = tas2cas(Vtas, H)
    return Vcas


def cas2mach(Vcas, H):
    """Calibrated Airspeed to Mach number"""
    Vtas = cas2tas(Vcas, H)
    Mach = tas2mach(Vtas, H)
    return Mach
