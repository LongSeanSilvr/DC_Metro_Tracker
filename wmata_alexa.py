"""
This app returns train times for the Metro DC transit system.
"""

from __future__ import print_function
import sys
import httplib
import urllib
import json

def lambda_handler(event):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])


    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


def on_session_started(session_started_request, session):
    """ Called when the session starts """
    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "GetTimes":
        return get_time(intent, session)
    elif intent_name == "GetDestTimes":
        return get_dest_times(intent, session)
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here

# --------------- Functions that control the skill's behavior ------------------


def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Ok, ready to give you train times."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Ask for a train time by saying, for example, " \
                    "when is the next train from Dupont Circle to Shady Grove?"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for riding metro." \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def get_time(intent, session):
    card_title = intent['name']
    session_attributes = {}
    should_end_session = False

    if 'station' in intent['slots']:
        station = intent['slots']['station']['value']
        times = query_station(station)
        str_time = format_time(times)
        if times:
            speech_output = "Here are the next trains arriving at {}. {}".format(station, str_time)
            print(speech_output)
        else:
            speech_output = "There are currently no trains scheduled for {}.".format(station)
            print(speech_output)
        reprompt_text = "Ask me about trains at a specific station."
    else:
        speech_output = "I'm not sure what station you are talking about. " \
                        "Please try again."
        reprompt_text = "I'm not sure what station you need. " \
                        "Get metro times by saying, " \
                        "when is the next train from Dupont Circle."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_dest_times(intent, session):
    card_title = intent['name']
    session_attributes = {}
    should_end_session = False

    if 'station' and 'destination' in intent['slots']:
        station = intent['slots']['station']['value']
        dest = intent['slots']['destination']['value']
        times = query_station(station, dest)
        str_time = format_time2(times)
        if times:
            speech_output = "The next trains arriving at {} going to {} will be here in: {}".format(station, dest, str_time)
            print(speech_output)
        else:
            speech_output = "There are currently no trains scheduled for {} going to {}.".format(station, dest)
            print(speech_output)
        reprompt_text = "Ask me about trains at a specific station."
    else:
        speech_output = "I'm not sure what stations you are talking about. " \
                        "Please try again."
        reprompt_text = "I'm not sure what stations you need. " \
                        "Get metro times by saying, " \
                        "when is the next train from Dupont Circle to Shady Grove."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def query_station(station, destination = None):
    station_data = json.loads("""{"blue": {"C01": {"Name": "Metro Center", "line_index": "14"}, "C02": {"Name": "McPherson Square", "line_index": "13"}, "C03": {"Name": "Farragut West", "line_index": "12"}, "C04": {"Name": "Foggy Bottom-GWU", "line_index": "11"}, "C05": {"Name": "Rosslyn", "line_index": "10"}, "C06": {"Name": "Arlington Cemetery", "line_index": "09"}, "C07": {"Name": "Pentagon", "line_index": "08"}, "C08": {"Name": "Pentagon City", "line_index": "07"}, "C09": {"Name": "Crystal City", "line_index": "06"}, "C10": {"Name": "Ronald Reagan Washington National Airport", "line_index": "05"}, "C12": {"Name": "Braddock Road", "line_index": "04"}, "C13": {"Name": "King St-Old Town", "line_index": "03"}, "D01": {"Name": "Federal Triangle", "line_index": "15"}, "D02": {"Name": "Smithsonian", "line_index": "16"}, "D03": {"Name": "L'Enfant Plaza", "line_index": "17"}, "D04": {"Name": "Federal Center SW", "line_index": "18"}, "D05": {"Name": "Capitol South", "line_index": "19"}, "D06": {"Name": "Eastern Market", "line_index": "20"}, "D07": {"Name": "Potomac Ave", "line_index": "21"}, "D08": {"Name": "Stadium-Armory", "line_index": "22"}, "G01": {"Name": "Benning Road", "line_index": "23"}, "G02": {"Name": "Capitol Heights", "line_index": "24"}, "G03": {"Name": "Addison Road-Seat Pleasant", "line_index": "25"}, "G04": {"Name": "Morgan Boulevard", "line_index": "26"}, "G05": {"Name": "Largo Town Center", "line_index": "27"}, "J02": {"Name": "Van Dorn Street", "line_index": "02"}, "J03": {"Name": "Franconia-Springfield", "line_index": "01"}}, "green": {"E01": {"Name": "Mt Vernon Sq 7th St-Convention Center", "line_index": "12"}, "E02": {"Name": "Shaw-Howard U", "line_index": "13"}, "E03": {"Name": "U Street/African-Amer Civil War Memorial/Cardozo", "line_index": "14"}, "E04": {"Name": "Columbia Heights", "line_index": "15"}, "E05": {"Name": "Georgia Ave-Petworth", "line_index": "16"}, "E06": {"Name": "Fort Totten", "line_index": "17"}, "E07": {"Name": "West Hyattsville", "line_index": "18"}, "E08": {"Name": "Prince George's Plaza", "line_index": "19"}, "E09": {"Name": "College Park-U of MD", "line_index": "20"}, "E10": {"Name": "Greenbelt", "line_index": "21"}, "F01": {"Name": "Gallery Pl-Chinatown", "line_index": "11"}, "F02": {"Name": "Archives-Navy Memorial-Penn Quarter", "line_index": "10"}, "F03": {"Name": "L'Enfant Plaza", "line_index": "09"}, "F04": {"Name": "Waterfront", "line_index": "08"}, "F05": {"Name": "Navy Yard-Ballpark", "line_index": "07"}, "F06": {"Name": "Anacostia", "line_index": "06"}, "F07": {"Name": "Congress Heights", "line_index": "05"}, "F08": {"Name": "Southern Avenue", "line_index": "04"}, "F09": {"Name": "Naylor Road", "line_index": "03"}, "F10": {"Name": "Suitland", "line_index": "02"}, "F11": {"Name": "Branch Ave", "line_index": "01"}}, "orange": {"C01": {"Name": "Metro Center", "line_index": "13"}, "C02": {"Name": "McPherson Square", "line_index": "12"}, "C03": {"Name": "Farragut West", "line_index": "11"}, "C04": {"Name": "Foggy Bottom-GWU", "line_index": "10"}, "C05": {"Name": "Rosslyn", "line_index": "09"}, "D01": {"Name": "Federal Triangle", "line_index": "14"}, "D02": {"Name": "Smithsonian", "line_index": "15"}, "D03": {"Name": "L'Enfant Plaza", "line_index": "16"}, "D04": {"Name": "Federal Center SW", "line_index": "17"}, "D05": {"Name": "Capitol South", "line_index": "18"}, "D06": {"Name": "Eastern Market", "line_index": "19"}, "D07": {"Name": "Potomac Ave", "line_index": "20"}, "D08": {"Name": "Stadium-Armory", "line_index": "21"}, "D09": {"Name": "Minnesota Ave", "line_index": "22"}, "D10": {"Name": "Deanwood", "line_index": "23"}, "D11": {"Name": "Cheverly", "line_index": "24"}, "D12": {"Name": "Landover", "line_index": "25"}, "D13": {"Name": "New Carrollton", "line_index": "26"}, "K01": {"Name": "Court House", "line_index": "08"}, "K02": {"Name": "Clarendon", "line_index": "07"}, "K03": {"Name": "Virginia Square-GMU", "line_index": "06"}, "K04": {"Name": "Ballston-MU", "line_index": "05"}, "K05": {"Name": "East Falls Church", "line_index": "04"}, "K06": {"Name": "West Falls Church-VT/UVA", "line_index": "03"}, "K07": {"Name": "Dunn Loring-Merrifield", "line_index": "02"}, "K08": {"Name": "Vienna/Fairfax-GMU", "line_index": "01"}}, "red": {"A01": {"Name": "Metro Center", "line_index": "15"}, "A02": {"Name": "Farragut North", "line_index": "14"}, "A03": {"Name": "Dupont Circle", "line_index": "13"}, "A04": {"Name": "Woodley Park-Zoo/Adams Morgan", "line_index": "12"}, "A05": {"Name": "Cleveland Park", "line_index": "11"}, "A06": {"Name": "Van Ness-UDC", "line_index": "10"}, "A07": {"Name": "Tenleytown-AU", "line_index": "09"}, "A08": {"Name": "Friendship Heights", "line_index": "08"}, "A09": {"Name": "Bethesda", "line_index": "07"}, "A10": {"Name": "Medical Center", "line_index": "06"}, "A11": {"Name": "Grosvenor-Strathmore", "line_index": "05"}, "A12": {"Name": "White Flint", "line_index": "04"}, "A13": {"Name": "Twinbrook", "line_index": "03"}, "A14": {"Name": "Rockville", "line_index": "02"}, "A15": {"Name": "Shady Grove", "line_index": "01"}, "B01": {"Name": "Gallery Pl-Chinatown", "line_index": "16"}, "B02": {"Name": "Judiciary Square", "line_index": "17"}, "B03": {"Name": "Union Station", "line_index": "18"}, "B04": {"Name": "Rhode Island Ave-Brentwood", "line_index": "20"}, "B05": {"Name": "Brookland-CUA", "line_index": "21"}, "B06": {"Name": "Fort Totten", "line_index": "22"}, "B07": {"Name": "Takoma", "line_index": "23"}, "B08": {"Name": "Silver Spring", "line_index": "24"}, "B09": {"Name": "Forest Glen", "line_index": "25"}, "B10": {"Name": "Wheaton", "line_index": "26"}, "B11": {"Name": "Glenmont", "line_index": "27"}, "B35": {"Name": "NoMa-Gallaudet U", "line_index": "19"}}, "silver": {"C01": {"Name": "Metro Center", "line_index": "15"}, "C02": {"Name": "McPherson Square", "line_index": "14"}, "C03": {"Name": "Farragut West", "line_index": "13"}, "C04": {"Name": "Foggy Bottom-GWU", "line_index": "12"}, "C05": {"Name": "Rosslyn", "line_index": "11"}, "D01": {"Name": "Federal Triangle", "line_index": "16"}, "D02": {"Name": "Smithsonian", "line_index": "17"}, "D03": {"Name": "L'Enfant Plaza", "line_index": "18"}, "D04": {"Name": "Federal Center SW", "line_index": "19"}, "D05": {"Name": "Capitol South", "line_index": "20"}, "D06": {"Name": "Eastern Market", "line_index": "21"}, "D07": {"Name": "Potomac Ave", "line_index": "22"}, "D08": {"Name": "Stadium-Armory", "line_index": "23"}, "G01": {"Name": "Benning Road", "line_index": "24"}, "G02": {"Name": "Capitol Heights", "line_index": "25"}, "G03": {"Name": "Addison Road-Seat Pleasant", "line_index": "26"}, "G04": {"Name": "Morgan Boulevard", "line_index": "27"}, "G05": {"Name": "Largo Town Center", "line_index": "28"}, "K01": {"Name": "Court House", "line_index": "10"}, "K02": {"Name": "Clarendon", "line_index": "09"}, "K03": {"Name": "Virginia Square-GMU", "line_index": "08"}, "K04": {"Name": "Ballston-MU", "line_index": "07"}, "K05": {"Name": "East Falls Church", "line_index": "06"}, "N01": {"Name": "McLean", "line_index": "05"}, "N02": {"Name": "Tysons Corner", "line_index": "04"}, "N03": {"Name": "Greensboro", "line_index": "03"}, "N04": {"Name": "Spring Hill", "line_index": "02"}, "N06": {"Name": "Wiehle-Reston East", "line_index": "01"}}, "yellow": {"C07": {"Name": "Pentagon", "line_index": "08"}, "C08": {"Name": "Pentagon City", "line_index": "07"}, "C09": {"Name": "Crystal City", "line_index": "06"}, "C10": {"Name": "Ronald Reagan Washington National Airport", "line_index": "05"}, "C12": {"Name": "Braddock Road", "line_index": "04"}, "C13": {"Name": "King St-Old Town", "line_index": "03"}, "C14": {"Name": "Eisenhower Avenue", "line_index": "02"}, "C15": {"Name": "Huntington", "line_index": "01"}, "E01": {"Name": "Mt Vernon Sq 7th St-Convention Center", "line_index": "12"}, "E02": {"Name": "Shaw-Howard U", "line_index": "13"}, "E03": {"Name": "U Street/African-Amer Civil War Memorial/Cardozo", "line_index": "14"}, "E04": {"Name": "Columbia Heights", "line_index": "15"}, "E05": {"Name": "Georgia Ave-Petworth", "line_index": "16"}, "E06": {"Name": "Fort Totten", "line_index": "17"}, "F01": {"Name": "Gallery Pl-Chinatown", "line_index": "11"}, "F02": {"Name": "Archives-Navy Memorial-Penn Quarter", "line_index": "10"}, "F03": {"Name": "L'Enfant Plaza", "line_index": "09"}}}""")
    headers = {
        # Request headers
        'api_key': '0b6b7bdc525a4abc9d0ad9879bd5d17b',
    }
    params = urllib.urlencode({
    })

    class Found(Exception): pass
    try:
        for line in station_data:
            for code in station_data[line]:
                if station.lower() in station_data[line][code]['Name'].lower():
                    st_code = code
                    st_index = station_data[line][code]['line_index']
                    st_line = line
                    raise Found
    except Found:
        pass

    try:
        conn = httplib.HTTPSConnection('api.wmata.com')
        conn.request("GET", "/StationPrediction.svc/json/GetPrediction/{}?{}".format(st_code, params), "{body}",
                     headers)
        response = conn.getresponse()
        data = response.read()
        data = json.loads(data)
        times = [(train[u'DestinationName'], train[u'Min']) for train in data[u'Trains']]
        conn.close()
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

    if destination is not None:
        class Found(Exception): pass
        try:
            for code in station_data[st_line]:
                if destination.lower() in station_data[line][code]['Name'].lower():
                    dest_code = code
                    dest_index = station_data[line][code]['line_index']
                    dest_line = line
                    raise Found
        except Found:
            pass

        dest_trajectory = int(dest_index) - int(st_index)

        all_times = times
        times = []
        for time in all_times:
            for line in station_data:
                found = False
                for code in station_data[line]:
                    if time[0].lower() in station_data[line][code]['Name'].lower():
                        target_index = station_data[line][code]['line_index']
                        found = True
                        break
                if found:
                    targ_trajectory = int(target_index) - int(st_index)
                    if (targ_trajectory <= dest_trajectory < 0) or (0 < dest_trajectory <= targ_trajectory):
                        times.append(time)
    return times

def format_time(times):
    stringt = ""
    times = [(time[0], time[1]) for time in times if time[1] not in ("BRD","ARR")]
    for i,time in enumerate(times):
        if len(times)-i == 1:
            stringt += "and "
        stringt += "towards {} in {} minutes. ".format(time[0], time[1])
    return stringt

def format_time2(times):
    stringt = ""
    times = [(time[0], time[1]) for time in times if time[1] not in ("BRD","ARR")]
    for i,time in enumerate(times):
        if len(times)-i == 1:
            stringt += "and "
        stringt += "{} minutes, ".format(time[1])
    return stringt
# --------------- Helpers that build all of the responses ----------------------


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': 'SessionSpeechlet - ' + title,
            'content': 'SessionSpeechlet - ' + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

# =====================================

if __name__ == "__main__":
    with open("test_event.json", "rb") as f:
        event = json.loads(f.read())
    lambda_handler(event)
