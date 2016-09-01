"""
Unit tests for get_incidents.py
"""
import unittest
import ujson as json
from development_version.src.Incident import Incident
from development_version.src.get_incidents import GetIncidents


# ======================================================================================================================
# Tests
# ======================================================================================================================
class TestCase(unittest.TestCase):

    # Static Methods
    def test_incidents_query(self):
        self.assertIsInstance(GetIncidents.query_api(), dict)

    def test_slot_extraction(self):
        from development_version.test_events.test_Incidents_alerts import jstring
        intent, session = setup(jstring)
        self.assertEqual(GetIncidents.retrieve_slot_value(intent, 'line'), 'red line')
        self.assertEqual(GetIncidents.retrieve_slot_value(intent, 'incidenttype'), 'alerts')

    # Ensure correct setup
    def test_setup(self):
        from development_version.test_events.test_Incidents_alerts import jstring
        intent, session = setup(jstring)
        test_incident = GetIncidents(intent, session)
        self.assertEqual(test_incident.line, 'red')
        self.assertEqual(test_incident.type, 'alerts')
        self.assertIsInstance(test_incident.json_data, dict)
        self.assertIsInstance(test_incident.all_incidents, list)
        self.assertIsInstance(test_incident.all_incidents[0], Incident)




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