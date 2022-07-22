from typing import Optional
from textwrap import wrap
from datetime import datetime


def unixtime2utc(ts):
    ts = int(ts)
    dt = datetime.utcfromtimestamp(ts / 1000)
    return dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]


def hex2bin(hexstr: str) -> str:
    num_of_bits = len(hexstr) * 4
    binstr = bin(int(hexstr, 16))[2:].zfill(int(num_of_bits))
    return binstr


def bin2int(binstr: str) -> int:
    return int(binstr, 2)


def allzeros(msg: str) -> bool:
    d = hex2bin(data(msg))
    if bin2int(d) > 0:
        return False
    else:
        return True


def wrongstatus(data: str, sb: int, msb: int, lsb: int) -> bool:
    """Check if the status bit and field bits are consistency.
    This Function is used for checking BDS code versions.
    """
    # status bit, most significant bit, least significant bit
    status = int(data[sb - 1])
    value = bin2int(data[msb - 1: lsb])

    if not status:
        if value != 0:
            return True

    return False


def df(msg: str) -> int:
    """Decode Downlink Format value, bits 1 to 5."""
    dfbin = hex2bin(msg[:2])
    return min(bin2int(dfbin[0:5]), 24)


def crc(msg: str, encode: bool = False) -> int:
    """Mode-S Cyclic Redundancy Check.
    Detect if bit error occurs in the Mode-S message. When encode option is on,
    the checksum is generated.
    Args:
        msg: 28 bytes hexadecimal message string
        encode: True to encode the date only and return the checksum
    Returns:
        int: message checksum, or partity bits (encoder)
    """
    # the CRC generator
    G = [int("11111111", 2), int("11111010", 2), int("00000100", 2), int("10000000", 2)]

    if encode:
        msg = msg[:-6] + "000000"

    msgbin = hex2bin(msg)
    msgbin_split = wrap(msgbin, 8)
    mbytes = list(map(bin2int, msgbin_split))

    for ibyte in range(len(mbytes) - 3):
        for ibit in range(8):
            mask = 0x80 >> ibit
            bits = mbytes[ibyte] & mask

            if bits > 0:
                mbytes[ibyte] = mbytes[ibyte] ^ (G[0] >> ibit)
                mbytes[ibyte + 1] = mbytes[ibyte + 1] ^ (
                        0xFF & ((G[0] << 8 - ibit) | (G[1] >> ibit))
                )
                mbytes[ibyte + 2] = mbytes[ibyte + 2] ^ (
                        0xFF & ((G[1] << 8 - ibit) | (G[2] >> ibit))
                )
                mbytes[ibyte + 3] = mbytes[ibyte + 3] ^ (
                        0xFF & ((G[2] << 8 - ibit) | (G[3] >> ibit))
                )

    result = (mbytes[-3] << 16) | (mbytes[-2] << 8) | mbytes[-1]

    return result


def icao(msg: str) -> Optional[str]:
    """Calculate the ICAO address from an Mode-S message.
    Applicable only with DF4, DF5, DF20, DF21 messages.
    Args:
        msg (String): 28 bytes hexadecimal message string
    Returns:
        String: ICAO address in 6 bytes hexadecimal string
    """
    addr: Optional[str]
    DF = df(msg)

    if DF in (11, 17, 18):
        addr = msg[2:8]
    elif DF in (0, 4, 5, 16, 20, 21):
        c0 = crc(msg, encode=True)
        c1 = int(msg[-6:], 16)
        addr = "%06X" % (c0 ^ c1)
    else:
        addr = None

    return addr


def is_icao_assigned(icao: str) -> bool:
    """Check whether the ICAO address is assigned (Annex 10, Vol 3)."""
    if (icao is None) or (not isinstance(icao, str)) or (len(icao) != 6):
        return False

    icaoint = int(icao, 16)

    if 0x200000 < icaoint < 0x27FFFF:
        return False  # AFI
    if 0x280000 < icaoint < 0x28FFFF:
        return False  # SAM
    if 0x500000 < icaoint < 0x5FFFFF:
        return False  # EUR, NAT
    if 0x600000 < icaoint < 0x67FFFF:
        return False  # MID
    if 0x680000 < icaoint < 0x6F0000:
        return False  # ASIA
    if 0x900000 < icaoint < 0x9FFFFF:
        return False  # NAM, PAC
    if 0xB00000 < icaoint < 0xBFFFFF:
        return False  # CAR
    if 0xD00000 < icaoint < 0xDFFFFF:
        return False  # future
    if 0xF00000 < icaoint < 0xFFFFFF:
        return False  # future

    return True


def typecode(msg: str) -> Optional[int]:
    """Type code of ADS-B message
    Args:
        msg (string): 28 bytes hexadecimal message string
    Returns:
        int: type code number
    """
    if df(msg) not in (17, 18):
        return None

    tcbin = hex2bin(msg[8:10])
    return bin2int(tcbin[0:5])


def floor(x: float) -> int:
    return int(np.floor(x))


def data(msg: str) -> str:
    """Return the data frame in the message, bytes 9 to 22."""
    return msg[8:-6]


def callsign(msg):
    """Aircraft callsign
    Args:
        msg (str): 28 hexdigits string
    Returns:
        string: callsign
    """

    if typecode(msg) < 1 or typecode(msg) > 4:
        return None
    #        raise RuntimeError("%s: Not a identification message" % msg)

    else:
        chars = "#ABCDEFGHIJKLMNOPQRSTUVWXYZ#####_###############0123456789######"
        msgbin = hex2bin(msg)
        csbin = msgbin[40:96]

        cs = ""
        cs += chars[bin2int(csbin[0:6])]
        cs += chars[bin2int(csbin[6:12])]
        cs += chars[bin2int(csbin[12:18])]
        cs += chars[bin2int(csbin[18:24])]
        cs += chars[bin2int(csbin[24:30])]
        cs += chars[bin2int(csbin[30:36])]
        cs += chars[bin2int(csbin[36:42])]
        cs += chars[bin2int(csbin[42:48])]

        # clean string, remove spaces and marks, if any.
        # cs = cs.replace('_', '')
        cs = cs.replace("#", "")
        return cs


def gray2alt(binstr: str) -> Optional[int]:
    gc500 = binstr[:8]
    n500 = gray2int(gc500)

    # in 100-ft step must be converted first
    gc100 = binstr[8:]
    n100 = gray2int(gc100)

    if n100 in [0, 5, 6]:
        return None

    if n100 == 7:
        n100 = 5

    if n500 % 2:
        n100 = 6 - n100

    alt = (n500 * 500 + n100 * 100) - 1300
    return alt


def gray2int(binstr: str) -> int:
    """Convert greycode to binary."""
    num = bin2int(binstr)
    num ^= num >> 8
    num ^= num >> 4
    num ^= num >> 2
    num ^= num >> 1
    return num
