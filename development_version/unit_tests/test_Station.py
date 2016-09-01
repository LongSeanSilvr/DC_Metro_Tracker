"""
Unit tests for Station class
"""
import unittest
from development_version.src.Station import *


# ======================================================================================================================
# Tests
# ======================================================================================================================
class TestCase(unittest.TestCase):

    def test_static_methods(self):
        self.assertEqual("branch", Station.essentialize_station_name("Branch aves"))

    def test_good_case(self):
        my_station = Station('metro center')

        # test lines
        self.assertIsInstance(my_station.lines, list)
        self.assertEqual(4, len(my_station.lines))

        # test st_codes
        self.assertIsInstance(my_station.station_codes, list)
        self.assertEqual(2, len(my_station.station_codes))

        # test info
        self.assertIsInstance(my_station.line_details, list)
        self.assertEqual(4, len(my_station.line_details))

        # test that class correctly identifies and corrects non-standard names
        my_station = Station("no my")
        self.assertEqual("NoMa-Gallaudet U", my_station.name)

    def test_ghost_station(self):
        self.assertIsInstance(Station("Ghost"), Station)

    def test_no_passenger(self):
        self.assertIsInstance(Station("Train"), Station)

    def test_abort_instance(self):
        with self.assertRaises(InvalidStationError):
            Station('the moon')
        with self.assertRaises(NoHomeError):
            Station('home', user_id='the moon')
        with self.assertRaises(NoOriginError):
            Station(user_id='the moon')


# ======================================================================================================================
# Run
# ======================================================================================================================
if __name__ == "__main__":
    unittest.main()