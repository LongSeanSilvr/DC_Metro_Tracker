"""
Unit tests for get_times.py
"""
import unittest
from development_version.src.get_times import *
import ujson as json


# ======================================================================================================================
# Tests
# ======================================================================================================================
class TestCase(unittest.TestCase):

    # STATIC METHODS
    # get_station_info
    def test_get_station_info_src(self):
        from development_version.test_events.test_GetTimes_src_dst import jstring as js
        js = json.loads(js)
        intent = js['request']['intent']
        session = js['session']
        src = GetTimes.get_station_info(intent, session)

        self.assertIsInstance(src, Station)
        self.assertEqual(src.name, "Metro Center")
        self.assertEqual(['blue', 'orange', 'silver', 'red'], src.lines)

    def test_get_station_info_dst(self):
        from development_version.test_events.test_GetTimes_src_dst import jstring as js
        intent, session = setup(js)
        dst = GetTimes.get_station_info(intent, session, dst=True)

        self.assertIsInstance(dst, Station)
        self.assertEqual(dst.name, "Tenleytown-AU")
        self.assertEqual(['red'], dst.lines)

    def test_station_info_infer_home(self):
        from development_version.test_events.test_GetTimes_dst import jstring as js
        intent, session = setup(js)
        src = GetTimes.get_station_info(intent, session)

        self.assertIsInstance(src, Station)
        self.assertEqual("Dupont Circle", src.name)

    def test_station_info_no_origin(self):
        from development_version.test_events.test_GetTimes_no_origin import jstring as js
        intent, session = setup(js)
        src = GetTimes.get_station_info(intent, session)

        self.assertIsInstance(src, str)
        self.assertEqual("no_origin", src)

    def test_station_info_no_home(self):
        from development_version.test_events.test_GetTimes_no_home import jstring as js
        intent, session = setup(js)
        src = GetTimes.get_station_info(intent, session)

        self.assertIsInstance(src, str)
        self.assertEqual("no_home", src)

    def test_station_info_invalid_station(self):
        from development_version.test_events.test_GetTimes_invalid_station import jstring as js
        intent, session = setup(js)
        src = GetTimes.get_station_info(intent, session)

        self.assertIsInstance(src, str)
        self.assertEqual("invalid_station", src)

    def test_station_info_invalid_destination(self):
        from development_version.test_events.test_GetTimes_invalid_destination import jstring as js
        intent, session = setup(js)
        dst = GetTimes.get_station_info(intent, session, dst=True)

        self.assertIsInstance(dst, str)
        self.assertEqual("invalid_destination", dst)

    def test_station_info_no_dst(self):
        from development_version.test_events.test_GetTimes_src import jstring as js
        intent, session = setup(js)
        dst = GetTimes.get_station_info(intent, session, dst=True)

        self.assertEqual(None, dst)

    # get_line_info
    def test_get_line_info_while_line(self):
        from development_version.test_events.test_GetTimes_lineFiltered import jstring as js
        intent, session = setup(js)
        line = GetTimes.get_line_info(intent)

        self.assertIsInstance(line, unicode)
        self.assertEqual(line, "blue")

    def test_get_line_info_no_line(self):
        from development_version.test_events.test_GetTimes_no_line import jstring as js
        intent, session = setup(js)
        line = GetTimes.get_line_info(intent)

        self.assertEqual(line, None)

    # retrieve_times
    def test_retrieve_times(self):
        train_list = GetTimes.retrieve_times("C05")
        self.assertIsInstance(train_list, list)
        self.assertIsInstance(train_list[0], Train)

    def test_retrieve_times_bad_code(self):
        train_list = GetTimes.retrieve_times("Cfish")
        self.assertIsInstance(train_list, str)
        self.assertEqual(train_list, "unknown_line")

    # fiilter engine
    def test_filter_direction(self):
        ideal_train = Train("metro center", "rosslyn")

        test1 = Train("metro center", "rosslyn", "blue", '8')
        self.assertTrue(GetTimes.filter_engine(test1, ideal_train))

        test2 = Train("metro center", "franconia", "blue", '8')
        self.assertTrue(GetTimes.filter_engine(test2, ideal_train))

        test3 = Train("metro center", "airport", "blue", '8')
        self.assertTrue(GetTimes.filter_engine(test3, ideal_train))

        test4 = Train("metro center", "largo", "blue", '8')
        self.assertFalse(GetTimes.filter_engine(test4, ideal_train))

        test5 = Train("metro center", "Train", "--", '8') #ghost trains have no direction
        self.assertTrue(GetTimes.filter_engine(test5, ideal_train))

        test6 = Train("metro center", "Train", "ghost", '8') #ghost trains have no direction
        self.assertTrue(GetTimes.filter_engine(test6, ideal_train))

    def test_filter_time(self):
        ideal_train = Train("metro center", "rosslyn")

        test1 = Train("metro center", "rosslyn", "blue", 'ARR')
        self.assertFalse(GetTimes.filter_engine(test1, ideal_train))

        test2 = Train("metro center", "rosslyn", "blue", 'BRD')
        self.assertFalse(GetTimes.filter_engine(test2, ideal_train))

        test3 = Train("metro center", "rosslyn", "blue")
        self.assertFalse(GetTimes.filter_engine(test3, ideal_train))

        test4 = Train("metro center", "rosslyn", "blue", '1')
        self.assertTrue(GetTimes.filter_engine(test4, ideal_train))

    def test_filter_lines(self):
        ideal_train = Train("metro center", "mclean")

        test1 = Train("metro center", "largo", "blue", '8')
        self.assertFalse(GetTimes.filter_engine(test1, ideal_train))

        test2 = Train("metro center", "clarendon", "orange", '8')
        self.assertFalse(GetTimes.filter_engine(test2, ideal_train))

        test3 = Train("metro center", "willy", "silver", '8')
        self.assertTrue(GetTimes.filter_engine(test3, ideal_train))

    #INSTANTIATION
    # ensure correct setup, ideal-train creation, and output
    def test_get_times_src_dst(self):
        from development_version.test_events.test_GetTimes_src_dst import jstring as js
        intent, session = setup(js)

        # ensure creation
        test_obj = GetTimes(intent, session)
        self.assertIsInstance(test_obj, GetTimes)
        self.assertEqual(test_obj.src.name, "Metro Center")
        self.assertEqual(test_obj.dst.name, "Tenleytown-AU")
        self.assertEqual(test_obj.line, "red")

        # ensure correct setup of ideal_train
        ideal_train = test_obj.build_ideal_train()
        self.assertEqual(ideal_train.src.name, "Metro Center")
        self.assertEqual(ideal_train.dst.name, "Tenleytown-AU")
        self.assertEqual(ideal_train.line, "red")
        self.assertEqual(ideal_train.direction, "negative")

        # ensure correct output
        self.assertIsInstance(test_obj.return_trains(), list)

    def test_get_times_src(self):
        from development_version.test_events.test_GetTimes_src import jstring as js
        intent, session = setup(js)

        # ensure creation
        test_obj = GetTimes(intent, session)
        self.assertIsInstance(test_obj, GetTimes)
        self.assertEqual(test_obj.src.name, "Brookland-CUA")
        self.assertEqual(test_obj.dst, None)
        self.assertEqual(test_obj.line, None)

        # ensure correct setup of ideal_train
        ideal_train = test_obj.build_ideal_train()
        self.assertEqual(ideal_train.src.name, "Brookland-CUA")
        self.assertEqual(ideal_train.dst, None)
        self.assertEqual(ideal_train.line, None)
        self.assertEqual(ideal_train.direction, None)

        # ensure correct output
        self.assertIsInstance(test_obj.return_trains(), list)

    def test_get_times_infer_home(self):
        from development_version.test_events.test_GetTimes_dst import jstring as js
        intent, session = setup(js)
        test_obj = GetTimes(intent, session)

        # ensure creation
        self.assertIsInstance(test_obj, GetTimes)
        self.assertEqual(test_obj.src.name, "Dupont Circle")
        self.assertEqual(test_obj.dst.name, "NoMa-Gallaudet U")
        self.assertEqual(test_obj.line, None)

        # ensure correct setup of ideal_train
        ideal_train = test_obj.build_ideal_train()
        self.assertEqual(ideal_train.src.name, "Dupont Circle")
        self.assertEqual(ideal_train.dst.name, "NoMa-Gallaudet U")
        self.assertEqual(ideal_train.line, None)
        self.assertEqual(ideal_train.direction, "positive")

        # ensure correct output
        self.assertIsInstance(test_obj.return_trains(), list)

    def test_get_times_same_station(self):
        from development_version.test_events.test_GetTimes_same_stations import jstring as js
        intent, session = setup(js)
        test_obj = GetTimes(intent, session)

        # ensure creation
        self.assertIsInstance(test_obj, GetTimes)
        self.assertEqual(test_obj.src.name, "Metro Center")
        self.assertEqual(test_obj.dst.name, "Metro Center")
        self.assertEqual(test_obj.line, "red")

        # ensure correct setup of ideal_train
        ideal_train = test_obj.build_ideal_train()
        self.assertIsInstance(ideal_train, str)
        self.assertEqual(ideal_train, "same_stations")

        # ensure correct output
        self.assertEqual(test_obj.return_trains(), "same_stations")

    def test_get_times_no_intersection(self):
        from development_version.test_events.test_GetTimes_no_intersection import jstring as js
        intent, session = setup(js)
        test_obj = GetTimes(intent, session)

        # ensure creation
        self.assertIsInstance(test_obj, GetTimes)
        self.assertEqual(test_obj.src.name, "NoMa-Gallaudet U")
        self.assertEqual(test_obj.dst.name, "Rosslyn")
        self.assertEqual(test_obj.line, None)

        # ensure correct setup of ideal_train
        ideal_train = test_obj.build_ideal_train()
        self.assertIsInstance(ideal_train, str)
        self.assertEqual(ideal_train, "no_intersection")

        # ensure correct output
        self.assertEqual(test_obj.return_trains(), "no_intersection")

    def test_get_times_invalid_src_line(self):
        from development_version.test_events.test_GetTimes_invalid_src_line import jstring as js
        intent, session = setup(js)
        test_obj = GetTimes(intent, session)

        # ensure creation
        self.assertIsInstance(test_obj, GetTimes)
        self.assertEqual(test_obj.src.name, "Rosslyn")
        self.assertEqual(test_obj.dst.name, "Metro Center")
        self.assertEqual(test_obj.line, "red")

        # ensure correct setup of ideal_train
        ideal_train = test_obj.build_ideal_train()
        self.assertIsInstance(ideal_train, str)
        self.assertEqual(ideal_train, "invalid_src_line")

        # ensure correct output
        self.assertEqual(test_obj.return_trains(), "invalid_src_line")

    def test_get_times_invalid_dst_line(self):
        from development_version.test_events.test_GetTimes_invalid_dst_line import jstring as js
        intent, session = setup(js)
        test_obj = GetTimes(intent, session)

        # ensure creation
        self.assertIsInstance(test_obj, GetTimes)
        self.assertEqual(test_obj.src.name, "Metro Center")
        self.assertEqual(test_obj.dst.name, "Rosslyn")
        self.assertEqual(test_obj.line, "red")

        # ensure correct setup of ideal_train
        ideal_train = test_obj.build_ideal_train()
        self.assertIsInstance(ideal_train, str)
        self.assertEqual(ideal_train, "invalid_dst_line")

        # ensure correct output
        self.assertEqual(test_obj.return_trains(), "invalid_dst_line")

    def test_easter_eggs_mordor(self):
        from development_version.test_events.test_GetTimes_Mordor import jstring as js
        intent, session = setup(js)
        test_obj = GetTimes(intent, session)
        # ensure creation
        self.assertIsInstance(test_obj, GetTimes)
        # ensure correct output
        self.assertEqual(test_obj.return_trains(), "mordor")

    def test_easter_eggs_dulles(self):
        from development_version.test_events.test_GetTimes_Dulles import jstring as js
        intent, session = setup(js)
        test_obj = GetTimes(intent, session)
        # ensure creation
        self.assertIsInstance(test_obj, GetTimes)
        # ensure correct output
        self.assertEqual(test_obj.return_trains(), "dulles")


def setup(jst):
    js = json.loads(jst)
    intent = js['request']['intent']
    session = js['session']
    return intent, session
# ======================================================================================================================
# Run
# ======================================================================================================================
if __name__ == "__main__":
    unittest.main()
