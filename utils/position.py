import numpy as np
from typing import Optional

from utils.common import floor, hex2bin, bin2int, typecode, gray2alt, df


def cprNL(lat: float) -> int:
    """NL() function in CPR decoding."""

    if np.isclose(lat, 0):
        return 59
    elif np.isclose(abs(lat), 87):
        return 2
    elif lat > 87 or lat < -87:
        return 1

    nz = 15
    a = 1 - np.cos(np.pi / (2 * nz))
    b = np.cos(np.pi / 180 * abs(lat)) ** 2
    nl = 2 * np.pi / (np.arccos(1 - a / b))
    NL = floor(nl)
    return NL


def oe_flag(msg):
    """Check the odd/even flag. Bit 54, 0 for even, 1 for odd.
    Args:
        msg (str): 28 hexdigits string
    Returns:
        int: 0 or 1, for even or odd frame
    """
    tc = typecode(msg)
    if tc is None:
        return None
    else:
        if tc < 5 or tc > 18:
            return None
        else:
            msgbin = hex2bin(msg)
            return int(msgbin[53])



def airborne_position(msg0, msg1, t0, t1):
    """Decode airborn position from a pair of even and odd position message
    Args:
        msg0 (string): even message (28 hexdigits)
        msg1 (string): odd message (28 hexdigits)
        t0 (int): timestamps for the even message
        t1 (int): timestamps for the odd message
    Returns:
        (float, float): (latitude, longitude) of the aircraft
    """

    mb0 = hex2bin(msg0)[32:]
    mb1 = hex2bin(msg1)[32:]

    oe0 = int(mb0[21])
    oe1 = int(mb1[21])
    if oe0 == 0 and oe1 == 1:
        pass
    elif oe0 == 1 and oe1 == 0:
        mb0, mb1 = mb1, mb0
        t0, t1 = t1, t0
    else:
        raise RuntimeError("Both even and odd CPR frames are required.")

    # 131072 is 2^17, since CPR lat and lon are 17 bits each.
    cprlat_even = bin2int(mb0[22:39]) / 131072
    cprlon_even = bin2int(mb0[39:56]) / 131072
    cprlat_odd = bin2int(mb1[22:39]) / 131072
    cprlon_odd = bin2int(mb1[39:56]) / 131072

    air_d_lat_even = 360 / 60
    air_d_lat_odd = 360 / 59

    # compute latitude index 'j'
    j = floor(59 * cprlat_even - 60 * cprlat_odd + 0.5)

    lat_even = float(air_d_lat_even * (j % 60 + cprlat_even))
    lat_odd = float(air_d_lat_odd * (j % 59 + cprlat_odd))

    if lat_even >= 270:
        lat_even = lat_even - 360

    if lat_odd >= 270:
        lat_odd = lat_odd - 360

    # check if both are in the same latidude zone, exit if not
    if cprNL(lat_even) != cprNL(lat_odd):
        return None

    # compute ni, longitude index m, and longitude
    if t0 > t1:
        lat = lat_even
        nl = cprNL(lat)
        ni = max(cprNL(lat) - 0, 1)
        m = floor(cprlon_even * (nl - 1) - cprlon_odd * nl + 0.5)
        lon = (360 / ni) * (m % ni + cprlon_even)
    else:
        lat = lat_odd
        nl = cprNL(lat)
        ni = max(cprNL(lat) - 1, 1)
        m = floor(cprlon_even * (nl - 1) - cprlon_odd * nl + 0.5)
        lon = (360 / ni) * (m % ni + cprlon_odd)

    if lon > 180:
        lon = lon - 360

    return round(lat, 5), round(lon, 5)


def airborne_position_with_ref(msg, lat_ref, lon_ref):
    """Decode airborne position with only one message,
    knowing reference nearby location, such as previously calculated location,
    ground station, or airport location, etc. The reference position shall
    be within 180NM of the true position.
    Args:
        msg (str): even message (28 hexdigits)
        lat_ref: previous known latitude
        lon_ref: previous known longitude
    Returns:
        (float, float): (latitude, longitude) of the aircraft
    """

    mb = hex2bin(msg)[32:]

    cprlat = bin2int(mb[22:39]) / 131072
    cprlon = bin2int(mb[39:56]) / 131072

    i = int(mb[21])
    d_lat = 360 / 59 if i else 360 / 60

    j = floor(lat_ref / d_lat) + floor(
        0.5 + ((lat_ref % d_lat) / d_lat) - cprlat
    )

    lat = d_lat * (j + cprlat)

    ni = cprNL(lat) - i

    if ni > 0:
        d_lon = 360 / ni
    else:
        d_lon = 360

    m = floor(lon_ref / d_lon) + floor(
        0.5 + ((lon_ref % d_lon) / d_lon) - cprlon
    )

    lon = d_lon * (m + cprlon)

    return round(lat, 5), round(lon, 5)


def altitude05(msg):
    """Decode aircraft altitude
    Args:
        msg (str): 28 hexdigits string
    Returns:
        int: altitude in feet
    """
    tc = typecode(msg)

    if tc < 9 or tc == 19 or tc > 22:
        #        raise RuntimeError("%s: Not a airborn position message" % msg)
        return None

    mb = hex2bin(msg)[32:]
    altbin = mb[8:20]

    if tc < 19:
        altcode = altbin[0:6] + "0" + altbin[6:]
        alt = altitude(altcode)
    else:
        alt = bin2int(altbin) * 3.28084

    return alt


def altitude(binstr: str) -> Optional[int]:
    """Decode 13 bits altitude code.
    Args:
        binstr (String): 13 bits binary string
    Returns:
        int: altitude in ft
    """
    alt: Optional[int]

    if len(binstr) != 13 or not set(binstr).issubset(set("01")):
        raise RuntimeError("Input must be 13 bits binary string")

    Mbit = binstr[6]
    Qbit = binstr[8]

    if bin2int(binstr) == 0:
        # altitude unknown or invalid
        alt = None

    elif Mbit == "0":  # unit in ft
        if Qbit == "1":  # 25ft interval
            vbin = binstr[:6] + binstr[7] + binstr[9:]
            alt = bin2int(vbin) * 25 - 1000
        if Qbit == "0":  # 100ft interval, above 50187.5ft
            C1 = binstr[0]
            A1 = binstr[1]
            C2 = binstr[2]
            A2 = binstr[3]
            C4 = binstr[4]
            A4 = binstr[5]
            # M = binstr[6]
            B1 = binstr[7]
            # Q = binstr[8]
            B2 = binstr[9]
            D2 = binstr[10]
            B4 = binstr[11]
            D4 = binstr[12]

            graystr = D2 + D4 + A1 + A2 + A4 + B1 + B2 + B4 + C1 + C2 + C4
            alt = gray2alt(graystr)

    if Mbit == "1":  # unit in meter
        vbin = binstr[:6] + binstr[7:]
        alt = int(bin2int(vbin) * 3.28084)  # convert to ft

    return alt


def altcode(msg: str) -> Optional[int]:
    """Compute altitude encoded in DF4 or DF20 message.
    Args:
        msg (String): 28 bytes hexadecimal message string
    Returns:
        int: altitude in ft
    """
    alt: Optional[int]
    if df(msg) not in [0, 4, 16, 20]:
        return None
    #        raise RuntimeError("Message must be Downlink Format 0, 4, 16, or 20.")

    # Altitude code, bit 20-32
    mbin = hex2bin(msg)
    altitude_code = mbin[19:32]
    alt = altitude(altitude_code)

    return alt


def find_pair_loc(oe_list):
    i = oe_list[0]
    loc_list = list()
    for j, v in enumerate(oe_list):
        if v != i:
            loc_list.append(j-1)
            i = v
    return loc_list

def util_position(chunk):
    latlon = None
    alt = None
    latlon_list = list()
    alt_list = list()
    oe_list = chunk['oe'].tolist()
    pair_loc = find_pair_loc(oe_list)
    if len(pair_loc) > 0:
        pair_c = 0
        for loc in range(len(chunk)):
            if loc == pair_loc[pair_c]:
                alt0 = altitude05(chunk.iloc[loc]['code'])
                alt1 = altitude05(chunk.iloc[loc+1]['code'])
                if abs(alt0 - alt1) < 50:
                    latlon = airborne_position(chunk.iloc[loc]['code'], chunk.iloc[loc+1]['code'],
                                               chunk.iloc[loc]['time'], chunk.iloc[loc+1]['time'])
                    if latlon is not None:
                        latlon_list.append(latlon)
                        lat = latlon[0]
                        lon = latlon[1]

                        alt = (alt0 + alt1)/2.
                        alt_list.append(alt)

                if len(pair_loc)-1 > pair_c:
                    pair_c += 1
            else:
                if latlon is not None:
                    latlon = airborne_position_with_ref(chunk.iloc[loc]['code'], lat, lon)
                    alt = altitude05(chunk.iloc[loc]['code'])
                    latlon_list.append(latlon)
                    alt_list.append(alt)
    return latlon_list, alt_list