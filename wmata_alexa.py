"""
This app returns train times for the Metro DC transit system.
"""

from __future__ import print_function
import httplib
import urllib
import json


# ======================================================================================================================
# Handler
# ======================================================================================================================
def lambda_handler(event, context=None):
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


# ======================================================================================================================
# Session event functions
# ======================================================================================================================
def on_session_started(session_started_request, session):
    print("on_session_started requestId={}, sessionId={}".format(session_started_request['requestId'],
                                                                 session['sessionId']))


def on_launch(launch_request, session):
    print("on_launch requestId={}, sessionId={}".format(launch_request['requestId'], session['sessionId']))
    return get_welcome_response()


def on_intent(intent_request, session):
    print("on_intent requestId={}, sessionId={}".format(intent_request['requestId'], session['sessionId']))
    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']
    if intent_name == "GetTimes":
        return get_times(intent, session)
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    print(
        "on_session_ended requestId={}, sessionId={}".format(session_ended_request['requestId'], session['sessionId']))


# ======================================================================================================================
# skill behaviour functions
# ======================================================================================================================
def get_welcome_response():
    card_title = "Welcome"
    session_attributes = {}
    speech_output = "Ok, ready to give you train times."
    reprompt_text = ("Ask for a train time by saying, for example, "
                     "when is the next train from Dupont Circle to Shady Grove?")
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_times(intent, session):
    card_title = intent['name']
    session_attributes = {}
    should_end_session = True
    try:
        station = intent['slots']['station']['value']
        station = get_equivalents(station)
        if len(intent['slots']['destination']) > 1:
            dest = intent['slots']['destination']['value']
            dest = get_equivalents(dest)
            times = query_station(station, dest)
            speech_output = get_speech_output(times, station, dest)
        else:
            times = query_station(station)
            speech_output = get_speech_output(times, station)
        reprompt_text = ""
    except KeyError:
        speech_output = "I'm not sure what station you are talking about. Please try again."
        reprompt_text = "Get metro times by saying, for example, when is the next train from Dupont Circle."
    print(speech_output)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def query_station(station, destination=None):
    station_data = get_stations()
    st_options = get_options(station, station_data)
    st_code = st_options[st_options.keys()[0]].keys()[0]
    times = retrieve_times(st_code)

    if destination is not None:
        # Easter eggs
        if any(destination == x for x in ["dulles", "mordor"]):
            return destination

        # Find correct farragut
        if "farragut" in (station, destination):
            (station, destination) = which_farragut(station, destination)
            # recalculate station options
            st_options = get_options(station)

        dest_options = get_options(destination)
        intersection = [x for x in st_options.keys() if x in dest_options.keys()]

        if not intersection:
            return "no_intersection"
        else:
            shared_line = intersection[0]
            st_code = st_options[shared_line].keys()[0]
            st_index = st_options[shared_line][st_code]
            dest_station = dest_options[shared_line].keys()[0]
            dest_index = dest_options[shared_line][dest_station]
            dest_trajectory = int(dest_index) - int(st_index)
        times = filter_times(times, intersection, station_data, st_index, dest_trajectory)

    return times


def retrieve_times(st_code):
    headers = {'api_key': '0b6b7bdc525a4abc9d0ad9879bd5d17b',}
    params = urllib.urlencode({})
    try:
        conn = httplib.HTTPSConnection('api.wmata.com')
        conn.request("GET", "/StationPrediction.svc/json/GetPrediction/{}?{}".format(st_code, params), "{body}",
                     headers)
        response = conn.getresponse()
        data = json.loads(response.read())
        conn.close()
    except:
        return None
    line_codes = get_line_codes()
    try:
        times = [(line_codes[train[u'Line']], train[u'DestinationName'], train[u'Min']) for train in data[u'Trains']]
    except KeyError:
        return "unknown_line"
    return times


def filter_times(times, intersection, station_data, st_index, dest_trajectory):
    filtered_times = []
    for time in times:
        if not time[2]:
            continue
        for line in intersection:
            for code in station_data[line]:
                if time[1].lower() == "train":
                    target_index = "a ghost station"
                    break
                if time[1].lower() in station_data[line][code]['Name'].lower():
                    target_index = station_data[line][code]['line_index']
                    break
            if target_index == "a ghost station":
                filtered_times.append(time)
                break
            else:
                targ_trajectory = int(target_index) - int(st_index)
                if (targ_trajectory <= dest_trajectory < 0) or (0 < dest_trajectory <= targ_trajectory):
                    filtered_times.append(time)
    return filtered_times


def which_farragut(station, destination, st_options, station_data):
    if "farragut" in destination:
        if "red" in st_options.keys():
            destination = "farragut north"
        elif any(x in st_options.keys() for x in ["blue", "orange", "silver"]):
            destination = "farragut west"
    dest_options = get_options(destination, station_data)
    if "farragut" in station:
        if "red" in dest_options.keys():
            station = "farragut north"
        elif any(x in dest_options.keys() for x in ["blue", "orange", "silver"]):
            station = "farragut west"
    return station, destination


def get_options(station, station_data):
    st_options = {}
    for line in station_data:
        for code in station_data[line]:
            if station.lower() in station_data[line][code]['Name'].lower():
                st_code = code
                st_index = station_data[line][code]['line_index']
                st_line = line
                st_options[st_line] = {st_code: st_index}
    return st_options


def get_stations():
    station_data = json.loads(
        """{"blue": {"C01": {"Name": "Metro Center", "line_index": "14"}, "C02": {"Name": "McPherson Square", "line_index": "13"}, "C03": {"Name": "Farragut West", "line_index": "12"}, "C04": {"Name": "Foggy Bottom-GWU", "line_index": "11"}, "C05": {"Name": "Rosslyn", "line_index": "10"}, "C06": {"Name": "Arlington Cemetery", "line_index": "09"}, "C07": {"Name": "Pentagon", "line_index": "08"}, "C08": {"Name": "Pentagon City", "line_index": "07"}, "C09": {"Name": "Crystal City", "line_index": "06"}, "C10": {"Name": "Ronald Reagan Washington National Airport", "line_index": "05"}, "C12": {"Name": "Braddock Road", "line_index": "04"}, "C13": {"Name": "King St-Old Town", "line_index": "03"}, "D01": {"Name": "Federal Triangle", "line_index": "15"}, "D02": {"Name": "Smithsonian", "line_index": "16"}, "D03": {"Name": "L'Enfant Plaza", "line_index": "17"}, "D04": {"Name": "Federal Center SW", "line_index": "18"}, "D05": {"Name": "Capitol South", "line_index": "19"}, "D06": {"Name": "Eastern Market", "line_index": "20"}, "D07": {"Name": "Potomac Ave", "line_index": "21"}, "D08": {"Name": "Stadium-Armory", "line_index": "22"}, "G01": {"Name": "Benning Road", "line_index": "23"}, "G02": {"Name": "Capitol Heights", "line_index": "24"}, "G03": {"Name": "Addison Road-Seat Pleasant", "line_index": "25"}, "G04": {"Name": "Morgan Boulevard", "line_index": "26"}, "G05": {"Name": "Largo Town Center", "line_index": "27"}, "J02": {"Name": "Van Dorn Street", "line_index": "02"}, "J03": {"Name": "Franconia-Springfield", "line_index": "01"}}, "green": {"E01": {"Name": "Mt Vernon Sq 7th St-Convention Center", "line_index": "12"}, "E02": {"Name": "Shaw-Howard U", "line_index": "13"}, "E03": {"Name": "U Street/African-Amer Civil War Memorial/Cardozo", "line_index": "14"}, "E04": {"Name": "Columbia Heights", "line_index": "15"}, "E05": {"Name": "Georgia Ave-Petworth", "line_index": "16"}, "E06": {"Name": "Fort Totten", "line_index": "17"}, "E07": {"Name": "West Hyattsville", "line_index": "18"}, "E08": {"Name": "Prince George's Plaza", "line_index": "19"}, "E09": {"Name": "College Park-U of MD", "line_index": "20"}, "E10": {"Name": "Greenbelt", "line_index": "21"}, "F01": {"Name": "Gallery Pl-Chinatown", "line_index": "11"}, "F02": {"Name": "Archives-Navy Memorial-Penn Quarter", "line_index": "10"}, "F03": {"Name": "L'Enfant Plaza", "line_index": "09"}, "F04": {"Name": "Waterfront", "line_index": "08"}, "F05": {"Name": "Navy Yard-Ballpark", "line_index": "07"}, "F06": {"Name": "Anacostia", "line_index": "06"}, "F07": {"Name": "Congress Heights", "line_index": "05"}, "F08": {"Name": "Southern Avenue", "line_index": "04"}, "F09": {"Name": "Naylor Road", "line_index": "03"}, "F10": {"Name": "Suitland", "line_index": "02"}, "F11": {"Name": "Branch Ave", "line_index": "01"}}, "orange": {"C01": {"Name": "Metro Center", "line_index": "13"}, "C02": {"Name": "McPherson Square", "line_index": "12"}, "C03": {"Name": "Farragut West", "line_index": "11"}, "C04": {"Name": "Foggy Bottom-GWU", "line_index": "10"}, "C05": {"Name": "Rosslyn", "line_index": "09"}, "D01": {"Name": "Federal Triangle", "line_index": "14"}, "D02": {"Name": "Smithsonian", "line_index": "15"}, "D03": {"Name": "L'Enfant Plaza", "line_index": "16"}, "D04": {"Name": "Federal Center SW", "line_index": "17"}, "D05": {"Name": "Capitol South", "line_index": "18"}, "D06": {"Name": "Eastern Market", "line_index": "19"}, "D07": {"Name": "Potomac Ave", "line_index": "20"}, "D08": {"Name": "Stadium-Armory", "line_index": "21"}, "D09": {"Name": "Minnesota Ave", "line_index": "22"}, "D10": {"Name": "Deanwood", "line_index": "23"}, "D11": {"Name": "Cheverly", "line_index": "24"}, "D12": {"Name": "Landover", "line_index": "25"}, "D13": {"Name": "New Carrollton", "line_index": "26"}, "K01": {"Name": "Court House", "line_index": "08"}, "K02": {"Name": "Clarendon", "line_index": "07"}, "K03": {"Name": "Virginia Square-GMU", "line_index": "06"}, "K04": {"Name": "Ballston-MU", "line_index": "05"}, "K05": {"Name": "East Falls Church", "line_index": "04"}, "K06": {"Name": "West Falls Church-VT/UVA", "line_index": "03"}, "K07": {"Name": "Dunn Loring-Merrifield", "line_index": "02"}, "K08": {"Name": "Vienna/Fairfax-GMU", "line_index": "01"}}, "red": {"A01": {"Name": "Metro Center", "line_index": "15"}, "A02": {"Name": "Farragut North", "line_index": "14"}, "A03": {"Name": "Dupont Circle", "line_index": "13"}, "A04": {"Name": "Woodley Park-Zoo/Adams Morgan", "line_index": "12"}, "A05": {"Name": "Cleveland Park", "line_index": "11"}, "A06": {"Name": "Van Ness-UDC", "line_index": "10"}, "A07": {"Name": "Tenleytown-AU", "line_index": "09"}, "A08": {"Name": "Friendship Heights", "line_index": "08"}, "A09": {"Name": "Bethesda", "line_index": "07"}, "A10": {"Name": "Medical Center", "line_index": "06"}, "A11": {"Name": "Grosvenor-Strathmore", "line_index": "05"}, "A12": {"Name": "White Flint", "line_index": "04"}, "A13": {"Name": "Twinbrook", "line_index": "03"}, "A14": {"Name": "Rockville", "line_index": "02"}, "A15": {"Name": "Shady Grove", "line_index": "01"}, "B01": {"Name": "Gallery Pl-Chinatown", "line_index": "16"}, "B02": {"Name": "Judiciary Square", "line_index": "17"}, "B03": {"Name": "Union Station", "line_index": "18"}, "B04": {"Name": "Rhode Island Ave-Brentwood", "line_index": "20"}, "B05": {"Name": "Brookland-CUA", "line_index": "21"}, "B06": {"Name": "Fort Totten", "line_index": "22"}, "B07": {"Name": "Takoma", "line_index": "23"}, "B08": {"Name": "Silver Spring", "line_index": "24"}, "B09": {"Name": "Forest Glen", "line_index": "25"}, "B10": {"Name": "Wheaton", "line_index": "26"}, "B11": {"Name": "Glenmont", "line_index": "27"}, "B35": {"Name": "NoMa-Gallaudet U", "line_index": "19"}}, "silver": {"C01": {"Name": "Metro Center", "line_index": "15"}, "C02": {"Name": "McPherson Square", "line_index": "14"}, "C03": {"Name": "Farragut West", "line_index": "13"}, "C04": {"Name": "Foggy Bottom-GWU", "line_index": "12"}, "C05": {"Name": "Rosslyn", "line_index": "11"}, "D01": {"Name": "Federal Triangle", "line_index": "16"}, "D02": {"Name": "Smithsonian", "line_index": "17"}, "D03": {"Name": "L'Enfant Plaza", "line_index": "18"}, "D04": {"Name": "Federal Center SW", "line_index": "19"}, "D05": {"Name": "Capitol South", "line_index": "20"}, "D06": {"Name": "Eastern Market", "line_index": "21"}, "D07": {"Name": "Potomac Ave", "line_index": "22"}, "D08": {"Name": "Stadium-Armory", "line_index": "23"}, "G01": {"Name": "Benning Road", "line_index": "24"}, "G02": {"Name": "Capitol Heights", "line_index": "25"}, "G03": {"Name": "Addison Road-Seat Pleasant", "line_index": "26"}, "G04": {"Name": "Morgan Boulevard", "line_index": "27"}, "G05": {"Name": "Largo Town Center", "line_index": "28"}, "K01": {"Name": "Court House", "line_index": "10"}, "K02": {"Name": "Clarendon", "line_index": "09"}, "K03": {"Name": "Virginia Square-GMU", "line_index": "08"}, "K04": {"Name": "Ballston-MU", "line_index": "07"}, "K05": {"Name": "East Falls Church", "line_index": "06"}, "N01": {"Name": "McLean", "line_index": "05"}, "N02": {"Name": "Tysons Corner", "line_index": "04"}, "N03": {"Name": "Greensboro", "line_index": "03"}, "N04": {"Name": "Spring Hill", "line_index": "02"}, "N06": {"Name": "Wiehle-Reston East", "line_index": "01"}}, "yellow": {"C07": {"Name": "Pentagon", "line_index": "08"}, "C08": {"Name": "Pentagon City", "line_index": "07"}, "C09": {"Name": "Crystal City", "line_index": "06"}, "C10": {"Name": "Ronald Reagan Washington National Airport", "line_index": "05"}, "C12": {"Name": "Braddock Road", "line_index": "04"}, "C13": {"Name": "King St-Old Town", "line_index": "03"}, "C14": {"Name": "Eisenhower Avenue", "line_index": "02"}, "C15": {"Name": "Huntington", "line_index": "01"}, "E01": {"Name": "Mt Vernon Sq 7th St-Convention Center", "line_index": "12"}, "E02": {"Name": "Shaw-Howard U", "line_index": "13"}, "E03": {"Name": "U Street/African-Amer Civil War Memorial/Cardozo", "line_index": "14"}, "E04": {"Name": "Columbia Heights", "line_index": "15"}, "E05": {"Name": "Georgia Ave-Petworth", "line_index": "16"}, "E06": {"Name": "Fort Totten", "line_index": "17"}, "F01": {"Name": "Gallery Pl-Chinatown", "line_index": "11"}, "F02": {"Name": "Archives-Navy Memorial-Penn Quarter", "line_index": "10"}, "F03": {"Name": "L'Enfant Plaza", "line_index": "09"}}}""")
    return station_data


def get_line_codes():
    line_codes = {"RD": "red line",
                  "BL": "blue line",
                  "OR": "orange line",
                  "SV": "silver line",
                  "YL": "yellow line",
                  "GR": "green line",
                  "--": "ghost train",
                  "": "ghost train",
                  "Train": "ghost train",
                  "No": "no passenger train"}
    return line_codes


def get_equivalents(station):
    if any(name in station.lower() for name in ["gallery", "china"]):
        station = "gallery"
    if "king st" in station.lower():
        station = "old town"
    if "vernon" in station.lower():
        station = "vernon"
    if "willy" in station.lower():
        station = "wiehle-reston east"
    if ("stadium" or "armory") in station.lower():
        station = "stadium-armory"
    if any(name in station.lower() for name in ["franconia", "springfield"]):
        station = "franconia-springfield"
    if any(name in station.lower() for name in ["african", "you street"]):
        station = "U street"
    if ("maryland") in station.lower():
        station = "college park"
    if any(name in station.lower() for name in ["navy yard", "baseball", "nats park"]):
        station = "navy yard"
    if "howard" in station.lower():
        station = "howard"
    if "prince" in station.lower():
        station = "prince"
    if any(name in station.lower() for name in ["university of virginia", "virginia tech"]):
        station = "west falls church"
    if "american university" in station.lower():
        station = "tenleytown"
    if "grosvenor" in station.lower():
        station = "grosvenor"
    if "catholic" in station.lower():
        station = "brookland"
    if "gallaudet" in station.lower():
        station = "noma"
    if "georgia ave" in station.lower():
        station = "petworth"
    if "minnesota" in station.lower():
        station = "minnesota"
    if "potomac" in station.lower():
        station = "potomac"
    if "branch" in station.lower():
        station = "branch"
    if "rhode" in station.lower():
        station = "rhode island"
    if "dallas" in station.lower():
        station = "dulles"
    if any(station.lower() == x for x in ["know my", "number", "know muh", "no my"]):
        station = "noma"
    return station


def format_time(times):
    response = ""
    times = [(time[0], time[1], time[2]) for time in times if time[2] not in ("BRD", "ARR")]
    for i, time in enumerate(times):
        line = time[0]
        station = time[1]
        minutes = time[2]

        # replace weird station artifacts with intelligible names
        if station.lower() == "train":
            station = "a ghost station"
        if station.lower() == "no passenger":
            station = "an undisclosed station"

        # handle blank minutes field
        if not minutes:
            minutes = "unknown"

        # add 'and' before the last train in the list
        if len(times) != 1 and len(times) - i == 1:
            response += "and "

        # add proper indef articles to speech response
        if line == "orange line":
            response += "an "
        else:
            response += "a "

        # singularize 'minutes' if minutes = 1
        if minutes == "1":
            response += "{} to {} in {} minute, ".format(line, station, minutes)
        else:
            response += "{} to {} in {} minutes, ".format(line, station, minutes)

    # remove comma from end of line and replace with period.
    if response:
        stringt = response[:-1]
        stringt += "."

    return response


def get_speech_output(times, station, destination=None):
    if times is None:
        speech_output = "I'm having trouble reaching the Metro Transit website. Please try again in a few minutes."
    elif times == "unknown_station":
        speech_output = "The Metro transit website is unresponsive. Please try again in a few minutes."
    elif times == "no_intersection":
        speech_output = "Those stations don't connect. Please try again."
    elif times == "mordor":
        speech_output = "One does not simply metro to Mordor."
    elif times == "dulles":
        speech_output = "One does not simply metro to dulles."
    else:
        str_time = format_time(times)
        if str_time:
            speech_output = "there is {}".format(str_time)
        else:
            if destination:
                speech_output = "There are currently no trains scheduled from {} to {}.".format(station, destination)
            else:
                speech_output = "There are currently no trains scheduled for {}.".format(station)
    return speech_output


# ======================================================================================================================
# helpers
# ======================================================================================================================
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


# ======================================================================================================================
# Run if invoked
# ======================================================================================================================
if __name__ == "__main__":
    with open("test_event.json", "rb") as f:
        event = json.loads(f.read())
    lambda_handler(event)
