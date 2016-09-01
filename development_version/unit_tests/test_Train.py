"""
Unit tests for ___
"""
import unittest

from development_version.src.Train import *
from development_version.src.Station import Station


# ======================================================================================================================
# Tests
# ======================================================================================================================
class TestCase(unittest.TestCase):

    def test_string_input(self):
        train = Train('Silver Spring', 'Farragut North', 'red')
        self.assertIsInstance(train.src, Station)
        self.assertIsInstance(train.dst, Station)

    def test_Station_input(self):
        src = Station('silver spring')
        dst = Station('farragut north')
        train = Train(src, dst)
        self.assertIsInstance(train.src, Station)
        self.assertIsInstance(train.dst, Station)

    def test_direction(self):
        train = Train('Silver Spring', 'Farragut North', 'red')
        self.assertEqual("negative", train.direction)

        train = Train('Silver Spring', 'Glenmont', 'red')
        self.assertEqual("positive", train.direction)

        train = Train('Silver Spring', 'Train', '--')
        self.assertEqual("any", train.direction)

    def test_farragut_mixup(self):
        train1 = Train('farragut', "metro center", "red")
        self.assertEqual("Farragut North", train1.src.name)
        train2 = Train('farragut', "metro center", "blue")
        self.assertEqual("Farragut West", train2.src.name)

    def test_stops_left(self):
        train1 = Train('noma', 'dupont circle', 'red')
        self.assertEqual(train1.stops_left, 6)
        train2 = Train('noma', 'farragut north', 'red')
        self.assertEqual(train2.stops_left, 5)
        self.assertFalse(train2.stops_left >= train1.stops_left)

    def test_ghost_train(self):
        train = Train("Metro Center", "Train", line="--")
        self.assertIsInstance(train, Train)

    def test_no_passenger(self):
        train = Train("Metro Center", "No Passenger", line="no", time="--")
        self.assertIsInstance(train, Train)

    def test_abort_instance(self):
        with self.assertRaises(SrcLineError):
            Train('Silver Spring', 'Pentagon', 'yellow')
        with self.assertRaises(DstLineError):
            Train('Silver Spring', 'Pentagon', 'red')
        with self.assertRaises(StationIntersectionError):
            Train('Silver Spring', 'Farragut West')
        with self.assertRaises(SameStationError):
            Train('Silver Spring', 'Silver Spring')


# ======================================================================================================================
# Run
# ======================================================================================================================
if __name__ == "__main__":
    unittest.main()
