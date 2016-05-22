"""
This app returns train times for the Metro DC transit system.
"""

from __future__ import print_function
import httplib
import urllib
import json
import re
import boto3

# ======================================================================================================================
# Handler
# ======================================================================================================================
def lambda_handler(event, context=None):
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    # Call on_session_started if new
    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])
    # Request Types
    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


# ======================================================================================================================
# Session Event Functions
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
    elif intent_name == "CommuteEstimate":
        return commute_estimate(intent, session)
    elif intent_name == "Incidents":
        return get_incidents(intent, session)
    elif intent_name == "OnFire":
        return on_fire()
    elif intent_name == "UpdateHome":
        return update_home(intent, session)
    elif intent_name == "GetHome":
        return get_home(session)
    elif intent_name == "Help":
        return help_response()
    elif intent_name == "Exit":
        return exit_app()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    print(
        "on_session_ended requestId={}, sessionId={}".format(session_ended_request['requestId'], session['sessionId']))


# ======================================================================================================================
# Skill Behavior: Welcome Response
# ======================================================================================================================
def get_welcome_response():
    card_title = "Welcome"
    session_attributes = {}
    speech_output = "Metro tracker is ready to give you train times."
    reprompt_text = ("What station would you like train times for?")
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, should_end_session, reprompt_text))


# ======================================================================================================================
# Skill Intent: Commute Estimate
# ======================================================================================================================
def commute_estimate(intent, session):
    card_title = "Commute Estimate"
    should_end_session = True
    session_attributes = {}
    station_data = get_stations()

    user_id = session['user']['userId']
    home = lookup_home(user_id)

    # Validate that user has given a recognized source station. If not, set to home
    try:
        st = essentialize_station_name(intent['slots']['source']['value'])
        if st in ("home", "here"):
            if home:
                st = home
            else:
                speech_output, should_end_session = get_speech_output("no_home")
                print(speech_output)
                return build_response(session_attributes, build_speechlet_response(card_title, speech_output,
                                                                                   should_end_session))

        station = station_lookup(st, station_data, home)

        if not station:
            speech_output, should_end_session = get_speech_output("invalid_station")
            print(speech_output)
            return build_response(session_attributes, build_speechlet_response(card_title, speech_output,
                                                                               should_end_session))
    except KeyError:
        if home:
            station = home
        else:
            speech_output, should_end_session = get_speech_output("no_origin")
            print(speech_output)
            return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, should_end_session))

    try:
        dst = essentialize_station_name(intent['slots']['destination']['value'])
        if dst in ("home", "here"):
            if home:
                dst = home
            else:
                speech_output, should_end_session = get_speech_output("no_home")
                print(speech_output)
                return build_response(session_attributes, build_speechlet_response(card_title, speech_output,
                                                                                   should_end_session))

        destination = station_lookup(dst, station_data, home)
        if not destination:
            speech_output, should_end_session = get_speech_output("invalid_destination")
            print(speech_output)
            return build_response(session_attributes, build_speechlet_response(card_title, speech_output,
                                                                               should_end_session))
    except KeyError:
        speech_output, should_end_session = get_speech_output("no_destination")
        print(speech_output)
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, should_end_session))

    # Check for Farragut mixup
    station_options = get_options(station, station_data)
    if "farragut" in (station, destination):
        (station, destination) = which_farragut(station, destination, station_options, station_data)
        # recalculate station options
        station_options = get_options(station, station_data)
    destination_options = get_options(destination, station_data)

    # Get travel time estimate and construct speech output
    estimate = retrieve_estimate(station_options, destination_options)
    speech_output, should_end_session = get_speech_output(estimate, station, destination)
    print(speech_output)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, should_end_session))


def retrieve_estimate(station_options, destination_options):
    # check for shared line between source and destination
    intersection = [x for x in station_options.keys() if x in destination_options.keys()]

    # throw error if stations don't share a line
    if not intersection:
        return "no_intersection"
    # otherwise grab station codes for source and dest on shared line and get travel estimate
    else:
        shared_line = intersection[0]
        station_code = station_options[shared_line].keys()[0]
        destination_code = destination_options[shared_line].keys()[0]
        estimate = api_estimate(station_code, destination_code)
        return estimate


def api_estimate(station_code, destination_code):
    if station_code == destination_code:
        return "same_stations"
    headers = {'api_key': '0b6b7bdc525a4abc9d0ad9879bd5d17b',}
    params = urllib.urlencode({'FromStationCode': station_code, 'ToStationCode': destination_code,})
    try:
        conn = httplib.HTTPSConnection('api.wmata.com')
        conn.request("GET", "/Rail.svc/json/jSrcStationToDstStationInfo?{}".format(params), "{body}", headers)
        response = conn.getresponse()
        data = json.loads(response.read())
        conn.close()
        commute_time = data['StationToStationInfos'][0]['RailTime']
        return commute_time
    except:
        return "conn_problem"


# ======================================================================================================================
# Skill Intent: Get Times
# ======================================================================================================================
def get_times(intent, session):
    card_title = "Train Times"
    session_attributes = {}
    should_end_session = True
    reprompt_text = "What station would you like train times for?"

    user_id = session['user']['userId']
    home = lookup_home(user_id)

    try:
        # Grab station info from intent
        station = intent['slots']['station']['value']
        station = essentialize_station_name(station)
        if station in ("home", "here"):
            if home:
                station = home
            else:
                speech_output, should_end_session = get_speech_output("no_home")
                print(speech_output)
                return build_response(session_attributes, build_speechlet_response(
                    card_title, speech_output, should_end_session, reprompt_text))
    except:
        # if no station specified, treat home as origin point if user has set a home station
        if home:
            station = home
        # otherwise, throw an error about supplying an origin.
        else:
            speech_output, should_end_session = get_speech_output("no_origin")
            return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, should_end_session, reprompt_text))

    # Grab destination info
    if len(intent['slots']['destination']) > 1:
        dest = intent['slots']['destination']['value']
        dest = essentialize_station_name(dest)
        if dest in ("home", "here"):
            if home:
                dest = home
            else:
                speech_output, should_end_session = get_speech_output("no_home")
                print(speech_output)
                return build_response(session_attributes, build_speechlet_response(card_title, speech_output,
                                                                                   should_end_session))
    else:
        dest = None

    # Grab line info
    if len(intent['slots']['line']) > 1:
        line = intent['slots']['line']['value']
        line = line.split()[0]  # if line is in the form "x line", set line to x
    else:
        line = None

    # retrieve train times for supplied params and construct speech output
    (times, station, destination) = query_station(station, dest, line, home)

    speech_output, should_end_session = get_speech_output(times, station, destination, line)
    print(speech_output)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, should_end_session, reprompt_text))


def query_station(station, destination, line, home):
    station_data = get_stations()
    station = station_lookup(station, station_data, home)

    # Validate supplied station
    if not station:
        return "invalid_station", station, destination
    st_options = get_options(station, station_data)

    # Validate supplied line
    if line:
        try:
            st_code = st_options[line].keys()[0]
        except KeyError:
            return "invalid_source_line", station, destination
    else:
        st_code = st_options[st_options.keys()[0]].keys()[0]

    # Retrieve train times for given source station
    times = retrieve_times(st_code)
    if line:
        times = filter_times(times, station_data, line)

    if destination is not None:

        # Easter eggs
        if any(destination.lower() == x for x in ["dulles", "mordor"]):
            return destination, station, destination

        # Validate destination
        destination = station_lookup(destination, station_data, home)
        if not destination:
            return "invalid_destination", station, destination
        if destination == station:
            return "same_stations", station, destination

        # Check for Farragut mix-up
        if "farragut" in (station, destination):
            (station, destination) = which_farragut(station, destination, st_options, station_data)
            # recalculate station options
            st_options = get_options(station, station_data)

        # Grab possible lines/st_codes for destination station
        dest_options = get_options(destination, station_data)

        # Check if specified line goes to destination station - if not, break
        if line and (line not in dest_options.keys()):
            return "invalid_dest_line", station, destination

        # Find shared line between source and dest
        intersection = [x for x in st_options.keys() if x in dest_options.keys()]

        # If no shared line, alert user
        if not intersection:
            return "no_intersection", station, destination

        # Otherwise calculate the trajectory and filter trains in wrong direction or which don't go far enough.
        else:
            shared_line = intersection[0]
            st_code = st_options[shared_line].keys()[0]
            st_index = st_options[shared_line][st_code]
            dest_station = dest_options[shared_line].keys()[0]
            dest_index = dest_options[shared_line][dest_station]
            dest_trajectory = int(dest_index) - int(st_index)
            times = filter_times(times, station_data, intersection, st_index, dest_trajectory)

    return times, station, destination


def retrieve_times(st_code):
    headers = {'api_key': '0b6b7bdc525a4abc9d0ad9879bd5d17b',}
    params = urllib.urlencode({})

    try:
        # Query WMATA API
        conn = httplib.HTTPSConnection('api.wmata.com')
        conn.request("GET", "/StationPrediction.svc/json/GetPrediction/{}?{}".format(st_code, params), "{body}",
                     headers)
        response = conn.getresponse()
        data = json.loads(response.read())
        conn.close()
    except:
        # Throw error if anything at all goes wrong with get request
        return None

    try:
        times = [(code2line(train[u'Line']), train[u'DestinationName'], train[u'Min']) for train in data[u'Trains']]
    except KeyError:
        # Throw error if API returns a blank or wonky line that is not recognized by code2line()
        return "unknown_line"

    return times


def filter_times(times, station_data, lines, st_index=None, dest_trajectory=None):
    filtered_times = []
    for time in times:
        if filter_times_engine(time, station_data, lines, st_index, dest_trajectory):
            filtered_times.append(time)
    return filtered_times


def filter_times_engine(time, station_data, lines, st_index, dest_trajectory):
    # skip trains with no time info
    if not time[2]:
        return False

    # Skip if train is already boarding or arriving -- unless you live in the station, you're not catching that one.
    if time[2] in ("BRD", "ARR"):
        return False
    train_line = time[0].split()[0]

    # Skip if train is on wrong line
    if train_line not in lines:
        return False

    # If dest_trajectory is None, no destination is specified. In this case, skip the next steps and return True
    if not dest_trajectory:
        return True

    # Get station code of train end point
    st_code = None
    for code in station_data[train_line]:
        if time[1].lower() in station_data[train_line][code]['Name'].lower():
            st_code = code
            break

    # Get index of train end point.
    if time[1].lower() == "train":
        # Return true if station is unknown, since it may be going in right direction
        return True
    else:
        try:
            target_index = station_data[train_line][st_code]['line_index']
        except KeyError:
            # Skip if line index is undefined for some reason
            return False

    # Compare trajectories to filter for trains in right direction and going far enough
    targ_trajectory = int(target_index) - int(st_index)
    if (targ_trajectory <= dest_trajectory < 0) or (0 < dest_trajectory <= targ_trajectory):
        return True
    else:
        return False


# ======================================================================================================================
# Skill Intent: Get Incidents
# ======================================================================================================================
def get_incidents(intent, session):
    session_attributes = {}
    should_end_session = True
    card_title = "Incident Report"
    reprompt_text = "Ask about delays or alerts for a particular station"

    incident_data = incidents_from_api()

    if incident_data is None:
        speech_output, should_end_session = get_speech_output("conn_problem")
    elif not incident_data['Incidents']:
        speech_output, should_end_session = get_speech_output("no_incidents")
    else:
        events = []
        try:
            type = intent['slots']['incidenttype']['value']
        except:
            type = "incidents"

        if len(intent['slots']['line']) > 1:
            line = intent['slots']['line']['value']

            if type.lower() in "incidents":
                for incident in incident_data['Incidents']:
                    description = inc_line_filter(incident, line)
                    events.append(description)
            else:
                for incident in incident_data['Incidents']:
                    if incident['IncidentType'].lower() in type:
                        description = inc_line_filter(incident, line)
                        events.append(description)
        else:
            for incident in incident_data['Incidents']:
                if type in 'incidents':
                    description = incident['Description']
                    events.append(description)
                else:
                    if incident['IncidentType'].lower() in type:
                        description = incident['Description']
                        events.append(description)

        speech_output = ""
        for event in events:
            if event:
                speech_output += "{} ".format(event)

        if not speech_output:
            if len(intent['slots']['line']) > 1:
                if "line" not in line:
                    line += " line"
                speech_output = "There are  currently no {} listed for the {}".format(type, line)
            else:
                speech_output = "There are currently no {} listed.".format(type)

        speech_output = speech_output.replace(r'&', 'and')
        speech_output = speech_output.replace(r'btwn', 'between')
        speech_output = re.sub(r'\balt\b', 'alternative', speech_output)
        speech_output = re.sub(r'\bmin\b', 'minutes', speech_output)
        speech_output = re.sub(r'\w+ Line: ', '', speech_output)
        speech_output = speech_output.replace(r':', ',')
    print(speech_output)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, should_end_session, reprompt_text))


def incidents_from_api():
    headers = {'api_key': '0b6b7bdc525a4abc9d0ad9879bd5d17b',}
    params = urllib.urlencode({})
    try:
        conn = httplib.HTTPSConnection('api.wmata.com')
        conn.request("GET", "/Incidents.svc/json/Incidents?%s" % params, "{body}", headers)
        response = conn.getresponse()
        data = json.loads(response.read())
        conn.close()
    except Exception:
        return None
    return data


def inc_line_filter(incident, line):
    description = ""
    affected_lines = incident["LinesAffected"].split(";")
    for affected_line in affected_lines:
        if affected_line and (line in code2line(affected_line)):
            description = incident['Description']
    return description


# ======================================================================================================================
# Skill Intent: Update Home station
# ======================================================================================================================
def update_home(intent, session):
    card_title = "Updating Home Station"
    should_end_session = True
    session_attributes = {}
    reprompt_text = "to update your home station say, for example, set my home station to Dupont Circle"

    station_data = get_stations()
    user_id = session['user']['userId']

    try:
        home = intent['slots']['home']['value']
    except KeyError:
        speech_output, should_end_session = get_speech_output("missing_home")
        print(speech_output)
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, should_end_session, reprompt_text))

    home = essentialize_station_name(home)
    home = station_lookup(home, station_data, home)

    client = boto3.client('dynamodb')

    try:
        client.update_item(TableName='metro_times_user_ids', Key={'user_id': {'S': user_id}},
                           ExpressionAttributeValues={":home": {"S": home}}, UpdateExpression='SET home = :home')
    except Exception:
        speech_output, should_end_session = get_speech_output("UserID_Database_prob")
        print(speech_output)
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, should_end_session, reprompt_text))

    speech_output, should_end_session = get_speech_output("home_updated", home)
    print(speech_output)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, should_end_session, reprompt_text))


# ======================================================================================================================
# Skill Intent: query home station
# ======================================================================================================================
def get_home(session):
    card_title = "Home Station"
    should_end_session = True
    session_attributes = {}
    reprompt_text = "Try saying what is my home station"

    user_id = session['user']['userId']
    home = lookup_home(user_id)

    if home is not None:
        speech_output = "Your home station is currently set to {}".format(home)
    else:
        speech_output = "You currently do not have a home station set."

    print(speech_output)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, should_end_session, reprompt_text))

# ======================================================================================================================
# Skill Intent: On Fire?
# ======================================================================================================================
def on_fire():
    card_title = "Is Metro On Fire?"
    session_attributes = {}
    should_end_session = True
    reprompt_text = "Ask whether the metro is on fire"

    # Grab Data from Fire API
    try:
        #fire_data = '{"counts":{"red":false,"orange":false,"yellow":false,"green":false,"blue":false,"silver":false},"message":"Negative"}'
        fire_data = urllib.urlopen("https://ismetroonfire.com/fireapi").read()
        fire_data = json.loads(fire_data)
    except:
        speech_output = "I'm having trouble reaching 'ismetroonfire.com.' please try again in a few minutes."
        print(speech_output)
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, should_end_session, reprompt_text))

    # Make list of lines currently on fire
    fire_lines = []
    for line in fire_data['counts']:
        if fire_data['counts'][line]:
            fire_lines.append(line)

    # Construct appropriate Speech output
    if fire_lines:
        if len(fire_lines) == 1:
            speech_output = "Why yes, the {} line is on fire today.".format(fire_lines[0])
        else:
            speech_output = "Why yes, "
            for i in xrange(0,len(fire_lines)):
                if len(fire_lines)-i == 1:
                    speech_output += "and "
                speech_output += "the {} line, ".format(fire_lines[i])
            speech_output = speech_output[0:-2]
            speech_output += " are on fire today."
            if len(fire_lines) == 2:
                speech_output = re.sub(r', and', r' and', speech_output)
    else:
        speech_output = "Not yet!"

    print(speech_output)
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, should_end_session, reprompt_text))

# ======================================================================================================================
# Skill Intent: Help
# ======================================================================================================================
def help_response():
    card_title = "Help"
    session_attributes = {}
    should_end_session = False
    reprompt_text = "What station would you like train times for?"
    speech_output = ("I can give you train arrival times, travel time estimates, or let you know about alerts on a "
                     "particular metro line. What station would you like train times for?")
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, should_end_session, reprompt_text))


# ======================================================================================================================
# Skill Intent: Quit
# ======================================================================================================================
def exit_app():
    card_title = "Exiting"
    session_attributes = {}
    should_end_session = True
    reprompt_text = ""
    speech_output = "Goodbye."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, should_end_session, reprompt_text))


# ======================================================================================================================
# Auxiliary and Shared Functions
# ======================================================================================================================
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
    with open("stations.json", "rb") as f:
        station_data = json.loads(f.read())
    return station_data


def station_lookup(station, station_data, home):
    name = ""
    if station.lower() in ("here", "home", "my home"):
        return home
    for line in station_data:
        for code in station_data[line]:
            if station.lower() in station_data[line][code]['Name'].lower():
                name = station_data[line][code]['Name'].lower()
    return name


def code2line(line, reverse=False):
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
    if (not reverse) and (line in line_codes.keys()):
        code = line_codes[line]
        return code
    elif reverse:
        code = None
        for key, value in line_codes.iteritems():
            if line in value:
                code = key
                break
    else:
        code = None
    return code


def lookup_home(user):
    client = boto3.client('dynamodb')
    try:
        home_item = client.get_item(TableName='metro_times_user_ids', Key={'user_id': {'S': user}},
                                    ProjectionExpression="home")
        home = home_item['Item']['home']['S']
    except Exception:
        home = None

    return home


def essentialize_station_name(station):
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
    if "maryland" in station.lower():
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
    if "zoo" in station.lower():
        station = "zoo"
    if "verizon" in station.lower():
        station = "gallery place"
    if "national mall" in station.lower():
        station = "smithsonian"
    if "dallas" in station.lower():
        station = "dulles"
    if "airport" in station.lower():
        station = "airport"
    if station.lower() in ("know my", "number", "know muh", "no my", "know much"):
        station = "noma"
    return station


def get_speech_output(flag, station=None, destination=None, line=None):
    # Fix speech errors in station names before constructing speech output
    if station:
        station = fix_speech(station)
    if destination:
        destination = fix_speech(destination)

    # Construct appropriate speech output based on flag passed
    if flag is None:
        speech_output = "I'm having trouble reaching the Metro Transit website. Please try again in a few minutes."
        should_end_session = True
    # Unrecognized line from GetTimes
    elif line == "line":
        speech_output = "sorry, I don't recognize that line. Please repeat your request using a valid metro line."
        should_end_session = False
    elif flag == "unknown_station":
        speech_output = "The Metro transit website is unresponsive. Please try again in a few minutes."
        should_end_session = True
    elif flag == "no_origin":
        speech_output = "Sorry, I didn't detect an origin station. Please repeat your request including a valid " \
                        "origin station, or set a default home station."
        should_end_session = False
    elif flag == "no_destination":
        speech_output = "Sorry, I didn't detect a destination. Please repeat your request including a destination" \
                        "in order to get travel times."
        should_end_session = False
    elif flag == "no_home":
        speech_output = "Sorry, you don't currently have a home station set. Please try again using specific " \
                        "station names, or set a default home station."
        should_end_session = False
    elif flag == "missing_home":
        speech_output = "To set your home station please include the name of a valid metro station. For " \
                        "instance, try saying: 'set my home station to Fort Totten.'"
        should_end_session = False
    elif flag == "invalid_destination":
        speech_output = ("Sorry, I don't recognize that destination. Please repeat your request using a valid "
                         "metro station.")
        should_end_session = False
    elif flag == "invalid_station":
        speech_output = "Sorry, I don't recognize that station. Please repeat your request using a valid metro station."
        should_end_session = False
    elif flag == "invalid_source_line":
        speech_output = "Sorry, {} does not service {} line trains. Please try again.".format(station, line)
        should_end_session = False
    elif flag == "invalid_dest_line":
        speech_output = "Sorry, {} does not service {} line trains. Please try again".format(destination, line)
        should_end_session = False
    elif flag == "no_intersection":
        speech_output = ("Sorry, {} and {} don't connect. Please try again ".format(station, destination) +
                         "using stations on the same metro line.")
        should_end_session = False
    elif flag in ("mordor", "Mordor"):
        speech_output = "One does not simply metro to Mordor."
        should_end_session = True
    elif flag in ("dulles", "Dulles"):
        speech_output = "One does not simply metro to dulles."
        should_end_session = True
    elif flag == "conn_problem":
        speech_output = "I'm having trouble accessing the Metro transit website. Please try again in a few minutes."
        should_end_session = True
    elif flag == "UserID_Database_prob":
        speech_output = "Sorry, I'm having trouble accessing the Metro Tracker database. Please try again in a " \
                        "few minutes."
        should_end_session = True
    elif flag == "same_stations":
        speech_output = "Those are the same stations you silly goose! Please try again."
        should_end_session = False
    elif flag == "no_incidents":
        speech_output = "There are no incidents or alerts currently listed for any metro line."
        should_end_session = True
    elif flag == "home_updated":
        speech_output = "OK, updated your home station to {}".format(station)
        should_end_session = True
    elif isinstance(flag, int):
        if flag == 1:
            speech_output = "The current travel time between {} and {} is {} minute.".format(station, destination, flag)
        else:
            speech_output = "The current travel time between {} and {} is {} minutes.".format(station, destination,
                                                                                              flag)
        should_end_session = True
    elif isinstance(flag, list):
        str_time = format_time(flag)
        if str_time:
            speech_output = "there is {}".format(str_time)
        else:
            if line:
                if "line" not in line:
                    line += " line"
                if destination:
                    speech_output = "There are currently no {} trains scheduled from {} to {}.".format(line, station,
                                                                                                       destination)
                else:
                    speech_output = "There are currently no {} trains scheduled for {}.".format(line, station)
            else:
                if destination:
                    speech_output = "There are currently no trains scheduled from {} to {}.".format(station,
                                                                                                    destination)
                else:
                    speech_output = "There are currently no trains scheduled for {}.".format(station)
        should_end_session = True
    else:
        speech_output = "Hmm. I seem to have encountered an internal error. Please try your request again."
        should_end_session = False
    return speech_output, should_end_session

def fix_speech(station_name):
    station_name = re.sub(r"-cua", r" C U A", station_name)
    station_name = re.sub(r"-udc", r" U D C", station_name)
    station_name = re.sub(r"-gmu", r" G M U", station_name)
    station_name = re.sub(r"-mu", r" M U", station_name)
    station_name = re.sub(r"-au", r" A U", station_name)
    station_name = re.sub(r"St-", r"street ", station_name, re.IGNORECASE)
    station_name = re.sub(r'gallaudet u', r'Gallaudet University', station_name)
    station_name = re.sub(r"-u of md", r"University of Maryland", station_name)
    return station_name

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
            response += "{} to {} in {} minute, ".format(line, fix_speech(station), minutes)
        else:
            response += "{} to {} in {} minutes, ".format(line, fix_speech(station), minutes)

    # remove comma from end of line and replace with period.
    if response:
        response = response[:-2]
        response += "."

    return response


# ======================================================================================================================
# helpers
# ======================================================================================================================
def build_speechlet_response(title, output, should_end_session, reprompt_text=""):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
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
# Run if invoked directly
# ======================================================================================================================
if __name__ == "__main__":
    with open("test_event.json", "rb") as f:
        event = json.loads(f.read())
    lambda_handler(event)
