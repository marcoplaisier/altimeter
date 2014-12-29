#!/usr/bin/python
# -*- coding: utf-8 -*-


def calculate_compensation(TEMP, SENS, OFF, dT):
    if TEMP >= 2000:
        return TEMP, OFF, SENS

    if TEMP < 2000:
        T2 = dT**2 / 2**31
        OFF2 = 61 * (TEMP - 2000)**2 / 2**4
        SENS2 = 2 * (TEMP - 2000)**2

    if TEMP <= -1500:
        OFF2 += 15 * (TEMP + 1500)**2
        SENS2 += 8 * (TEMP + 1500)**2

    TEMP -= T2
    OFF -= OFF2
    SENS -= SENS2

    return TEMP, OFF, SENS


def calculate_values(data, compensate=True):
    # dT = D2 - TREF = D2 - C5 * 2^8
    dT = data['D2'] - (data['C5'] * 2**8)

    # TEMP = 20°C + dT * TEMPSENS = 2000 + dT * C6/2^23
    TEMP = 2000 + (dT * data['C6'] / 2**23)

    # OFF = OFFT1 + TCO * dT = C2 * 2^17 + (C4 * dT) / 2^6
    OFF = data['C2'] * 2**17 + (data['C4'] * dT) / 2**6

    # SENS = SENST1 + TCS * dT = C1*2^16 + (C3*dT)/2^7
    SENS = data['C1'] * 2**16 + (data['C3'] * dT) / 2**7

    if compensate:
        TEMP, OFF, SENS = calculate_compensation(TEMP, SENS, OFF, dT)

    # P = D1 * SENS - OFF = (D1 * SENS / 2^21 - OFF) / 2^15
    P = (data['D1'] * SENS / 2**21 - OFF) / 2**15
    return TEMP, P

if __name__ == '__main__':
    from gpio import GPIO

    g = GPIO()
    g.send_data([1])