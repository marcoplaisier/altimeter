#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division, print_function
from contextlib import contextmanager
import time
import struct
import sys

from gpio import GPIO

LONG_WAIT = 0.5
SHORT_WAIT = 0.005
CHIP_SELECT = 6
PRESSURE_ADDRESS = 0x48
TEMPERATURE_ADDRESS = 0x58
RESET_COMMAND = 0x1E
CALIBRATION_ADDRESSES = {'C1': 0xA2, 'C2': 0xA4, 'C3': 0xA6, 'C4': 0xA8, 'C5': 0xAA, 'C6': 0xAC}


@contextmanager
def spi_mode(chip):
    chip.write_pin(CHIP_SELECT, 0)
    time.sleep(SHORT_WAIT)
    yield
    chip.write_pin(CHIP_SELECT, 1)
    time.sleep(SHORT_WAIT)


def calculate_compensation(TEMP, SENS, OFF, dT):
    """In order to obtain best accuracy over temperature range, particularly in low temperature, it is recommended to
    compensate the non-linearity over the temperature. This can be achieved by correcting the calculated temperature,
    offset and sensitivity by a second order correction factor and will be recalculated with the standard calculation.

    :param TEMP: actual temperature (uncompensated)
    :param SENS: chip sensitivity
    :param OFF: offset at actual temperature
    :param dT: difference between actual and reference temperature
    :return: actual temperature, compensated for non-linearity in the chip
    """
    if TEMP >= 2000:
        return TEMP, OFF, SENS

    if TEMP < 2000:
        T2 = dT ** 2 / 2 ** 31
        OFF2 = 61 * (TEMP - 2000) ** 2 / 2 ** 4
        SENS2 = 2 * (TEMP - 2000) ** 2

    if TEMP <= -1500:
        OFF2 += 15 * (TEMP + 1500) ** 2
        SENS2 += 8 * (TEMP + 1500) ** 2

    TEMP -= T2
    OFF -= OFF2
    SENS -= SENS2

    return TEMP, OFF, SENS


def calculate_values(data, compensate=True):
    # dT = D2 - TREF = D2 - C5 * 2^8
    """Calculate the actual temperature and pressure, based on six calibration values and two measurements.

    :param data: a dictionary containing the six calibration values (C1... C6) and two measurements (D1, D2)
    :param compensate: boolean whether the pressure should be recalculated (for temperatures below 20 degrees)
    :return: a tuple containing the (0) temperature and (1) pressure
    """
    dT = data['D2'] - (data['C5'] * 2 ** 8)

    # TEMP = 20°C + dT * TEMPSENS = 2000 + dT * C6/2^23
    TEMP = 2000 + (dT * data['C6'] / 2 ** 23)

    # OFF = OFFT1 + TCO * dT = C2 * 2^17 + (C4 * dT) / 2^6
    OFF = data['C2'] * 2 ** 17 + (data['C4'] * dT) / 2 ** 6

    # SENS = SENST1 + TCS * dT = C1*2^16 + (C3*dT)/2^7
    SENS = data['C1'] * 2 ** 16 + (data['C3'] * dT) / 2 ** 7

    if compensate:
        TEMP, OFF, SENS = calculate_compensation(TEMP, SENS, OFF, dT)

    # P = D1 * SENS - OFF = (D1 * SENS / 2^21 - OFF) / 2^15
    P = (data['D1'] * SENS / 2 ** 21 - OFF) / 2 ** 15
    return round(TEMP / 100, 2), round(P / 100, 2)


def init_chip():
    """Before we can measure temperature and pressure, the chip needs to be initialized and reset.

    The process is relatively straight forward.
    First, pull the PS low to activate the SPI protocol
    Second, issue the reset command
    Third, pull the PS high

    Short waits are issued between each action to allow the chip to activate the proper routine

    :return: a reference to the chip that can be used to actually measure temperature and pressure
    """
    chip = GPIO()
    chip.pin_mode(CHIP_SELECT, chip.OUTPUT)
    chip.handle.digitalWrite(CHIP_SELECT, 1)
    time.sleep(LONG_WAIT)

    with spi_mode(chip):
        chip.send_data([RESET_COMMAND])

    time.sleep(LONG_WAIT)
    return chip


def get_calibration_value(chip, address):
    """Get a specific calibration values that is stored on the chip.

    The calibration values are hardwired in the chip, so this needs to be done only once. This is actually less straight
    forward. First, we activate the SPI protocol on the chip, by pulling the PS low. Then we send the address of the
    calibration value to the chip. We need to send 4 bytes, because the chip wants to send 32 bits back.
    The first byte always contains the value 254, the third byte always contains 255. The middle two bytes contain the
    actual calibration value (MSB). We need to pad the two bytes with zeros to get the proper value.
    Finally, we pull the PS high.

    :param chip: the chip
    :param address: the address where the calibration value is stored
    :return: the calibration value
    """
    with spi_mode(chip):
        chip.send_data([address, 0, 0, 0])
        return_data = chip.get_data()
        data = struct.unpack('>I', bytearray([0, 0]) + bytearray(return_data[1:3]))

    return data[0]


def get_measurement(chip, address):
    """Get a specific measurement, either pressure or temperature. This is determined based on the address

    How does this work?
    First, we indicate to the chip that we would like to get either a specific measurement. Then, we wait a little.
    Following the wait, we get the measurement from address 0x00 in four bytes. We ignore the first byte and use the
    remaining three to get the measurement. This value can be used to accurately calculate the actual temperature.

    :type address: specific value at address (either temperature or pressure)
    :return: the measurement
    """
    with spi_mode(chip):
        chip.send_data([address])

    with spi_mode(chip):
        chip.send_data([0x00, 0, 0, 0])
        return_data = chip.get_data()
        data = struct.unpack('>I', bytearray([0]) + bytearray(return_data[1:4]))

    return data[0]


def get_temperature(chip):
    """Get the raw temperature value from the chip

    :param chip: the chip
    :return: the raw temperature value
    """
    return get_measurement(chip, TEMPERATURE_ADDRESS)


def get_pressure(chip):
    """Get the raw pressure value from the chip

    :param chip: the chip
    :return: the raw pressure value
    """
    return get_measurement(chip, PRESSURE_ADDRESS)


def get_calibration_values(chip):
    """Get all calibration values from the chip

    :param chip: the chip from which to get the calibration values
    :return: a dictionary containing all calibration values (keys: C1... C6)
    """
    return {variable: get_calibration_value(chip, address) for (variable, address) in CALIBRATION_ADDRESSES.items()}


def loop(chip, calibration_values):
    """The main loop

    Uses the calibration values and the chip to calculate the actual temperature and pressure and prints them to sys.out

    :param chip: the chip
    :param calibration_values: a dictionary containing the calibration values (keys: C1...C6).
    """
    values = calibration_values.copy()

    while True:
        values['D1'] = get_pressure(chip)
        values['D2'] = get_temperature(chip)
        result = calculate_values(values)
        print("Temp: {0[0]}C, Press: {0[1]}".format(result))
        time.sleep(1)


if __name__ == '__main__':
    c = init_chip()
    values = get_calibration_values(c)
    sys.exit(loop(c, values))