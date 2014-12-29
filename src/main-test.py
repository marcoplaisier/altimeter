#!/usr/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase
from main import calculate_values


class TestMain(TestCase):
    def test_example_values(self):
        result = calculate_values(
            {'D1': 6465444,
             'D2': 8077636,
             'C1': 46372,
             'C2': 43981,
             'C3': 29059,
             'C4': 27842,
             'C5': 31553,
             'C6': 28165})
        self.assertAlmostEqual(2000.22, result[0], 1)
        self.assertAlmostEqual(110002.95, result[1], 1)

    def test_below_twenty(self):
        result = calculate_values(
            {'D1': 6465444,
             'D2': 7720007,
             'C1': 46372,
             'C2': 43981,
             'C3': 29059,
             'C4': 27842,
             'C5': 31553,
             'C6': 28165})
        self.assertAlmostEqual(739.94, result[0], 1)
        self.assertAlmostEqual(107008.62, result[1], 1)

    def test_below_minus_fifteen(self):
        result = calculate_values(
            {'D1': 6465444,
             'D2': 7153507,
             'C1': 46372,
             'C2': 43981,
             'C3': 29059,
             'C4': 27842,
             'C5': 31553,
             'C6': 28165})
        self.assertAlmostEqual(-1500.19, result[0], 1)
        self.assertAlmostEqual(101841.60, result[1], 1)

    def test_no_compensation_example_values(self):
        result = calculate_values(
            {'D1': 6465444,
             'D2': 8077636,
             'C1': 46372,
             'C2': 43981,
             'C3': 29059,
             'C4': 27842,
             'C5': 31553,
             'C6': 28165}, compensate=False)
        self.assertAlmostEqual(2000.22, result[0], 1)
        self.assertAlmostEqual(110002.95, result[1], 1)

    def test_min_values(self):
        result = calculate_values(
            {'D1': 0,
             'D2': 0,
             'C1': 0,
             'C2': 0,
             'C3': 0,
             'C4': 0,
             'C5': 0,
             'C6': 0})
        self.assertAlmostEqual(2000, result[0], 1)
        self.assertAlmostEqual(0, result[1], 1)

    def test_max_values(self):
        result = calculate_values(
            {'D1': 16777216,
             'D2': 16777216,
             'C1': 65535,
             'C2': 65535,
             'C3': 65535,
             'C4': 65535,
             'C5': 65535,
             'C6': 65535})
        self.assertAlmostEqual(2002, result[0], 1)
        self.assertAlmostEqual(786444, result[1], 1)