"""
Unit tests for handler.py
"""
import unittest
import ujson as json
from development_version.src.handler import lambda_handler
import re


# ======================================================================================================================
# Tests
# ======================================================================================================================
class TestCase(unittest.TestCase):

    # ====================
    # Test base intents
    # ====================
    def test_launch(self):
        from development_version.test_events.test_launch import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        self.assertEqual(output['response']['outputSpeech']['text'], "Metro tracker is ready to give you train times.")

    def test_exit(self):
        from development_version.test_events.test_exit import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        self.assertEqual(output['response']['outputSpeech']['text'], "Goodbye.")

    def test_help(self):
        from development_version.test_events.test_help import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        # don't test exact output, cause it's really long. Just make sure it contains this substring.
        self.assertIn("What station would you like train times for?", output['response']['outputSpeech']['text'])

    # ==============================
    # Test all scenarios of GetTimes
    # ==============================
    # First test supposedly successful scenarios
    def test_get_times_bare(self):
        from development_version.test_events.test_GetTimes_bare import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        st_pattern = r'[\w\.\-]+(\s[\w\.\-]+)?'
        patterns = [
            r'There are currently no( \w+ line)? trains scheduled from {} to {}'.format(st_pattern, st_pattern),
            r'There are currently no( \w+ line)? trains scheduled for {}'.format(st_pattern),
            r'There is a(n)? \w+ line to {} in [\d\w]+ minute(s)?'.format(st_pattern),
            r'a ghost train to a ghost station in [\d\w]+ minute(s)?'.format(st_pattern)
        ]
        out_text = output['response']['outputSpeech']['text']
        match = any(re.search(p, out_text) for p in patterns)
        self.assertTrue(match)

    def test_get_times_src_dst(self):
        from development_version.test_events.test_GetTimes_src_dst import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        st_pattern = r'[\w\.\-]+(\s[\w\.\-]+)?'
        patterns = [
            r'There are currently no( \w+ line)? trains scheduled from {} to {}'.format(st_pattern, st_pattern),
            r'There are currently no( \w+ line)? trains scheduled for {}'.format(st_pattern),
            r'There is a(n)? \w+ line to {} in [\d\w]+ minute(s)?'.format(st_pattern),
            r'a ghost train to a ghost station in [\d\w]+ minute(s)?'.format(st_pattern)
        ]
        out_text = output['response']['outputSpeech']['text']
        match = any(re.search(p, out_text) for p in patterns)
        self.assertTrue(match)

    def test_get_times_dst(self):
        from development_version.test_events.test_GetTimes_dst import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        st_pattern = r'[\w\.\-]+(\s[\w\.\-]+)?'
        patterns = [
            r'There are currently no( \w+ line)? trains scheduled from {} to {}'.format(st_pattern, st_pattern),
            r'There are currently no( \w+ line)? trains scheduled for {}'.format(st_pattern),
            r'There is a(n)? \w+ line to {} in [\d\w]+ minute(s)?'.format(st_pattern),
            r'a ghost train to a ghost station in [\d\w]+ minute(s)?'.format(st_pattern)
        ]
        out_text = output['response']['outputSpeech']['text']
        match = any(re.search(p, out_text) for p in patterns)
        self.assertTrue(match)

    def test_get_times_src(self):
        from development_version.test_events.test_GetTimes_dst import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        st_pattern = r'[\w\.\-]+(\s[\w\.\-]+)?'
        patterns = [
            r'There are currently no( \w+ line)? trains scheduled from {} to {}'.format(st_pattern, st_pattern),
            r'There are currently no( \w+ line)? trains scheduled for {}'.format(st_pattern),
            r'There is a(n)? \w+ line to {} in [\d\w]+ minute(s)?'.format(st_pattern),
            r'a ghost train to a ghost station in [\d\w]+ minute(s)?'.format(st_pattern)
        ]
        out_text = output['response']['outputSpeech']['text']
        match = any(re.search(p, out_text) for p in patterns)
        self.assertTrue(match)

    def test_get_times_line_filtered(self):
        from development_version.test_events.test_GetTimes_lineFiltered import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        st_pattern = r'[\w\.\-\/]+(\s[\w\.\-\/]+)?'
        patterns = [
            r'There are currently no( \w+ line)? trains scheduled from {} to {}'.format(st_pattern, st_pattern),
            r'There are currently no( \w+ line)? trains scheduled for {}'.format(st_pattern),
            r'There is a(n)? \w+ line to {} in [\d\w]+ minute(s)?'.format(st_pattern),
            r'a ghost train to a ghost station in [\d\w]+ minute(s)?'.format(st_pattern)
        ]
        out_text = output['response']['outputSpeech']['text']
        match = any(re.search(p, out_text) for p in patterns)
        self.assertTrue(match)

    # Now test scenarios with missing data
    def test_get_times_no_origin(self):
        from development_version.test_events.test_GetTimes_no_origin import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        self.assertIn("Sorry, I didn't detect an origin station.", output['response']['outputSpeech']['text'])

    def test_get_times_no_home(self):
        from development_version.test_events.test_GetTimes_no_home import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        self.assertIn("Sorry, you don't currently have a home station set.", output['response']['outputSpeech']['text'])

    # Now test scenarios with invalid parameters supplied by user
    def test_get_times_invalid_dest(self):
        from development_version.test_events.test_GetTimes_invalid_destination import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        self.assertIn("Sorry, I don't recognize that destination.", output['response']['outputSpeech']['text'])

    def test_get_times_invalid_station(self):
        from development_version.test_events.test_GetTimes_invalid_station import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        self.assertIn("Sorry, I don't recognize that station.", output['response']['outputSpeech']['text'])

    def test_get_times_invalid_dst_line(self):
        from development_version.test_events.test_GetTimes_invalid_dst_line import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        self.assertIn("Rosslyn does not service red line trains.", output['response']['outputSpeech']['text'])

    def test_get_times_invalid_src_line(self):
        from development_version.test_events.test_GetTimes_invalid_src_line import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        self.assertIn("Rosslyn does not service red line trains.", output['response']['outputSpeech']['text'])

    def test_get_times_line_wrong(self):
        from development_version.test_events.test_GetTimes_lineWrong import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        self.assertIn("Dupont Circle does not service green line trains.", output['response']['outputSpeech']['text'])

    def test_get_times_no_intersection(self):
        from development_version.test_events.test_GetTimes_no_intersection import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        self.assertIn("Sorry, NoMa-Gallaudet U and Rosslyn don't connect.", output['response']['outputSpeech']['text'])

    # ==========================================
    # Test all scenarios of GetHome
    # ==========================================
    def test_get_home(self):
        from development_version.test_events.test_GetHome import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        self.assertIn("Your home station is currently set to Dupont Circle", output['response']['outputSpeech']['text'])

    def test_get_home_missing_home(self):
        from development_version.test_events.test_GetHome_missing_home import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        self.assertIn("You currently do not have a home station set", output['response']['outputSpeech']['text'])

    # ==========================================
    # Test all scenarios of UpdateHome
    # ==========================================
    def test_update_home(self):
        from development_version.test_events.test_UpdateHome_st import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        self.assertIn("OK, updated your home station to Metro Center", output['response']['outputSpeech']['text'])

    def test_update_home_invalid(self):
        from development_version.test_events.test_UpdateHome_invalidst import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        self.assertIn("please include the name of a valid metro station.", output['response']['outputSpeech']['text'])

    def test_update_home_no_st(self):
        from development_version.test_events.test_UpdateHome_no_st import jstring
        output = setup(jstring)
        self.assertIsInstance(output, dict)
        self.assertIn("please include the name of a valid metro station.", output['response']['outputSpeech']['text'])

    # ==========================================
    # Test all scenarios of OnFire
    # ==========================================
    def test_on_fire(self):
        from development_version.test_events.test_OnFire import jstring
        output = setup(jstring)
        patterns = [
            r"Not right this minute, but I'm sure it will be soon enough",
            r'As usual, the \w+ line is on fire today.',
            r'As usual, the \w+(\s\w+)+ lines are on fire today.'
        ]
        out_text = output['response']['outputSpeech']['text']
        match = any(re.search(p, out_text) for p in patterns)
        self.assertTrue(match)


def setup(jstring):
    event = json.loads(jstring)
    output = lambda_handler(event)
    return output
# ======================================================================================================================
# Run
# ======================================================================================================================
if __name__ == "__main__":
    unittest.main()