import build_response as br
import httplib
import metro_tools as mt
import re
import ujson as json
import urllib
from development_version.src.Incident import Incident


# ======================================================================================================================
# Skill Intent: Get Incidents
# ======================================================================================================================
class GetIncidents(object):
    def __init__(self, intent, session):
        self.card_title = "Incident Report"
        self.reprompt_text = "Ask about delays or alerts for a particular station"
        self.line = self.retrieve_slot_value(intent, 'line').split()[0]
        self.type = self.retrieve_slot_value(intent, 'incidenttype')
        self.json_data = self.query_api()
        self.all_incidents = [Incident(thing) for thing in self.json_data['Incidents']] if \
            type(self.json_data) is dict else None

    @staticmethod
    def query_api():
        headers = {'api_key': '0b6b7bdc525a4abc9d0ad9879bd5d17b',}
        params = urllib.urlencode({})
        try:
            conn = httplib.HTTPSConnection('api.wmata.com')
            conn.request("GET", "/Incidents.svc/json/Incidents?{}".format(params), "{body}", headers)
            response = conn.getresponse()
            data = json.loads(response.read())
            conn.close()
        except Exception:
            return None
        return data

    @staticmethod
    def retrieve_slot_value(intent, slot):
        val = intent['slots'][slot]['value'] if len(intent['slots'][slot]) > 1 else None
        return val

    def inc_text_builder(self, events, type, line=None):
        speech_output = ""
        for event in events:
            if event:
                speech_output += "{} ".format(event)

        if not speech_output:
            if line:
                if "line" not in line:
                    line += " line"
                speech_output = "There are  currently no {} listed for the {}".format(type, line)
            else:
                speech_output = "There are currently no {} listed.".format(type)

        if line is not None:
            speech_output = re.sub(r'[\w/]+ Line: ', '', speech_output)
            speech_output = speech_output.replace(r':', ',')
        speech_output = speech_output.replace(r'&', 'and')
        speech_output = speech_output.replace(r'/', ' and ')
        speech_output = speech_output.replace(r'Hgts', 'Heights')
        speech_output = speech_output.replace(r'btwn', 'between')
        speech_output = re.sub(r'\balt\b', 'alternative', speech_output)
        speech_output = re.sub(r'\bmin\b', 'minutes', speech_output)
        speech_output = re.sub(r'\bBlu\b', 'Blue', speech_output)
        speech_output = re.sub(r'\bOrg\b', 'Orange', speech_output)
        return speech_output

    #if incident_data is None:
    #    flag = "conn_problem"
    #    br.build_response(card_title, flag, start, reprompt_text=reprompt_text)
    #
    #try:
    #    incidents = incident_data['Incidents']
    #except KeyError:
    #    flag = "conn_problem"
    #    return br.build_response(card_title, flag, start, reprompt_text=reprompt_text)
    #
    #if not incidents:
    #    flag = "no_incidents"
    #    return br.build_response(card_title, flag, start, reprompt_text=reprompt_text)
    #else:
    #    # Does user want a specific incident type?
    #    try:
    #        type = intent['slots']['incidenttype']['value']
    #    except KeyError:
    #        type = "incidents"
    #
    #    # Does user want a specific line?
    #    try:
    #        line = intent['slots']['line']['value']
    #    except KeyError:
    #        line = None
    #
    #    # Get requested events
    #    if type == "incidents":
    #        events = [inc_line_filter(incident, line) for incident in incident_data['Incidents']]
    #    else:
    #        events = [inc_line_filter(incident, line) for incident in incident_data['Incidents'] if
    #                  incident['IncidentType'].lower() in type]
    #
    #    flag = 'incidents'
    #    text = inc_text_builder(events, type, line)
    #    return br.build_response(card_title, flag, start, text=text, reprompt_text=reprompt_text)


#def inc_line_filter(incident, line):
#    affected_lines = incident["LinesAffected"].split(";")
#    if line is None:
#        return incident['Description']
#    else:
#        for affected_line in affected_lines:
#            if affected_line and (line in mt.code2line(affected_line)):
#                return incident['Description']
#
#

