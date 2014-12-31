#!/usr/bin/python
# -*- coding: utf-8 -*-
from ctypes import c_ubyte

from unittest import TestCase
try:
    from unittest.mock import Mock, call, patch
except ImportError:
    from mock import Mock, call, patch
import main


class TestMain(TestCase):
    def test_example_values(self):
        result = main.calculate_values(
            {'D1': 6465444,
             'D2': 8077636,
             'C1': 46372,
             'C2': 43981,
             'C3': 29059,
             'C4': 27842,
             'C5': 31553,
             'C6': 28165})
        self.assertAlmostEqual(20.00, result[0], 1)
        self.assertAlmostEqual(1100.02, result[1], 1)

    def test_below_twenty(self):
        result = main.calculate_values(
            {'D1': 6465444,
             'D2': 7720007,
             'C1': 46372,
             'C2': 43981,
             'C3': 29059,
             'C4': 27842,
             'C5': 31553,
             'C6': 28165})
        self.assertAlmostEqual(7.39, result[0], 1)
        self.assertAlmostEqual(1070.08, result[1], 1)

    def test_below_minus_fifteen(self):
        result = main.calculate_values(
            {'D1': 6465444,
             'D2': 7153507,
             'C1': 46372,
             'C2': 43981,
             'C3': 29059,
             'C4': 27842,
             'C5': 31553,
             'C6': 28165})
        self.assertAlmostEqual(-15.00, result[0], 1)
        self.assertAlmostEqual(1018.41, result[1], 1)

    def test_no_compensation_example_values(self):
        result = main.calculate_values(
            {'D1': 6465444,
             'D2': 8077636,
             'C1': 46372,
             'C2': 43981,
             'C3': 29059,
             'C4': 27842,
             'C5': 31553,
             'C6': 28165}, compensate=False)
        self.assertAlmostEqual(20.00, result[0], 1)
        self.assertAlmostEqual(1100.02, result[1], 1)

    def test_min_values(self):
        result = main.calculate_values(
            {'D1': 0,
             'D2': 0,
             'C1': 0,
             'C2': 0,
             'C3': 0,
             'C4': 0,
             'C5': 0,
             'C6': 0})
        self.assertAlmostEqual(20.00, result[0], 1)
        self.assertAlmostEqual(0, result[1], 1)

    def test_max_values(self):
        result = main.calculate_values(
            {'D1': 16777216,
             'D2': 16777216,
             'C1': 65535,
             'C2': 65535,
             'C3': 65535,
             'C4': 65535,
             'C5': 65535,
             'C6': 65535})
        self.assertAlmostEqual(20.02, result[0], 1)
        self.assertAlmostEqual(7864.44, result[1], 1)

    def test_get_calibration_value(self):
        m = Mock()
        a = c_ubyte*4
        return_data = a(1,2,3,4)
        m.get_data = Mock(return_value=return_data)
        expected_result = 2*2**8 + 3*2**0 # see a[1] and a[2] in array
        m.write_pin = Mock()
        m.send_data = Mock()
        test_address = 0x00

        result = main.get_calibration_value(m, test_address)

        self.assertEqual(result, expected_result)
        m.send_data.assert_called_once_with([test_address, 0, 0, 0])
        m.write_pin.assert_has_calls([
            call(main.CHIP_SELECT, 0),
            call(main.CHIP_SELECT, 1),
        ])

    def test_get_measurement(self):
        m = Mock()
        m.write_pin = Mock()
        m.send_data = Mock()
        a = c_ubyte*4
        return_data = a(1,2,3,4)
        m.get_data = Mock(return_value=return_data)
        expected_result = 2*2**16 + 3*2**8 + 4*2**0
        test_address = 0x00

        result = main.get_measurement(m, test_address)

        self.assertEqual(result, expected_result)
        m.send_data.assert_has_calls([
            call([test_address]),
            call([0, 0, 0, 0])
        ])
        m.write_pin.assert_has_calls([
            call(main.CHIP_SELECT, 0),
            call(main.CHIP_SELECT, 1),
            call(main.CHIP_SELECT, 0),
            call(main.CHIP_SELECT, 1)
        ])

    def test_get_calibration_values(self):
        m = Mock()
        expected_result = {
            'C1': 1,
            'C2': 1,
            'C3': 1,
            'C4': 1,
            'C5': 1,
            'C6': 1,
        }

        with patch.object(main, 'get_calibration_value', return_value=1) as mock_method:
            result = main.get_calibration_values(m)
            mock_method.assert_has_calls([
                call(m, 0xA2),
                call(m, 0xA4),
                call(m, 0xA6),
                call(m, 0xA8),
                call(m, 0xAA),
                call(m, 0xAC)
            ], any_order=True)
            self.assertEqual(result, expected_result)
