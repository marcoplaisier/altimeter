#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import struct

CALIBRATION_ADDRESSES = {'C1': 0xA2, 'C2': 0xA4, 'C3': 0xA6, 'C4': 0xA8, 'C5': 0xAA, 'C6': 0xAC}


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


def init_chip(chip):
    chip.pin_mode(6, chip.OUTPUT)
    chip.write_pin(6, 1)
    time.sleep(0.5)
    chip.handle.digitalWrite(6, 0)
    time.sleep(0.005)
    print(chip.send_data([0x1E]))
    time.sleep(0.005)
    chip.handle.digitalWrite(6, 1)
    time.sleep(0.05)
    return chip


def get_calibration_value(chip, address):
    chip.write_pin(6, 0)
    time.sleep(0.005)
    chip.send_data([address, 0])
    data = struct.unpack('H', chip.get_data())
    chip.write_pin(6, 1)
    return data


def get_temperature(chip):
    chip.write_pin(6, 0)
    time.sleep(0.005)
    chip.send_data([0x58])
    time.sleep(0.01)
    chip.write_pin(6, 1)

    chip.write_pin(6, 0)
    time.sleep(0.005)
    chip.send_data([0x00, 0, 0])
    data = struct.unpack('H', chip.get_data())
    time.sleep(0.01)
    chip.write_pin(6, 1)
    return data


def get_pressure(chip):
    chip.write_pin(6, 0)
    time.sleep(0.005)
    chip.send_data([0x48])
    time.sleep(0.01)
    chip.write_pin(6, 1)

    chip.write_pin(6, 0)
    time.sleep(0.005)
    chip.send_data([0x00, 0, 0])
    data = struct.unpack('H', chip.get_data())
    time.sleep(0.01)
    chip.write_pin(6, 1)
    return data


def get_calibration_values(chip):
    return {variable: get_calibration_value(chip, address) for (variable, address) in CALIBRATION_ADDRESSES.items()}


if __name__ == '__main__':
    from gpio import GPIO

    g = GPIO()
    g = init_chip(g)
    values = get_calibration_values(g)
    values['D1'] = get_temperature(g)
    values['D2'] = get_pressure(g)
    print(calculate_values(values))









