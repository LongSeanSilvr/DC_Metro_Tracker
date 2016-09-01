import metro_tools as mt
from Station import Station


# ======================================================================================================================
# Response builder
# ======================================================================================================================
def build_response(title, flag, station=None, destination=None, line=None, text=None,
                   reprompt_text="", session_attributes=""):

    output, should_end_session = get_speech_output(flag, station, destination, line, text)

    speechlet_response = {
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

    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


def get_speech_output(flag, station, destination, line, text):
    if isinstance(station, Station):
        station = station.name
    if isinstance(destination, Station):
        destination = destination.name

    # Base function responses
    if flag == 'welcome':
        speech_output = "Metro tracker is ready to give you train times."
        should_end_session = False
    elif flag == 'help':
        speech_output = ("I can give you train arrival times, travel time estimates, or let you know about alerts on "
                         "a particular metro line. What station would you like train times for?")
        should_end_session = False
    elif flag == 'exit':
        speech_output = "Goodbye."
        should_end_session = True

    # Incident Responses
    elif flag == 'incidents':
        speech_output = text
        should_end_session = True
    elif flag == "no_incidents":
        speech_output = "There are no incidents or alerts currently listed for any metro line."
        should_end_session = True
    elif flag == "fire_report":
        speech_output = text
        should_end_session = True

    # Home Responses
    elif flag == "home_updated":
        speech_output = "OK, updated your home station to {}".format(station)
        should_end_session = True
    elif flag == "home_report":
        speech_output = "Your home station is currently set to {}".format(station)
        should_end_session = True

    # Commute Estimate Responses
    elif isinstance(flag, int):
        if flag == 1:
            speech_output = "The current travel time between {} and {} is {} minute.".format(station, destination, flag)
        else:
            speech_output = "The current travel time between {} and {} is {} minutes.".format(station, destination,
                                                                                              flag)
        should_end_session = True
    elif flag in ("mordor", "Mordor"): # not Pythonic, but flag might be a list, so don't want to call .lower() on it.
        speech_output = "One does not simply metro to Mordor."
        should_end_session = True
    elif flag in ("dulles", "Dulles"):
        speech_output = "One does not simply metro to Dulles."
        should_end_session = True

    # Train report
    elif isinstance(flag, list):
        str_time = mt.format_time(flag)
        if str_time:
            speech_output = "There is {}".format(str_time)
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

    # Missing Info Responses
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
        speech_output = "You currently do not have a home station set."
        should_end_session = True

    # Invalid Input Responses
    elif flag == "invalid_home":
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
    elif flag == "invalid_src_line":
        speech_output = "Sorry, {} does not service {} line trains. Please try again.".format(station, line)
        should_end_session = False
    elif flag == "invalid_dst_line":
        speech_output = "Sorry, {} does not service {} line trains. Please try again".format(destination, line)
        should_end_session = False
    elif flag == "no_intersection":
        speech_output = ("Sorry, {} and {} don't connect. Please try again ".format(station, destination) +
                         "using stations on the same metro line.")
        should_end_session = False
    elif flag == "same_stations":
        speech_output = "Those are the same stations you silly goose! Please try again."
        should_end_session = False

    # Connection Problem responses:
    elif flag is None:
        speech_output = "I'm having trouble reaching the Metro Transit website. Please try again in a few minutes."
        should_end_session = True
    elif flag == "conn_problem":
        speech_output = "I'm having trouble accessing the Metro transit website. Please try again in a few minutes."
        should_end_session = True
    elif flag == "UserID_Database_prob":
        speech_output = "Sorry, I'm having trouble accessing the Metro Tracker database. Please try again in a " \
                        "few minutes."
        should_end_session = True
    elif flag == "fire_conn_prob":
        speech_output = "I'm having trouble reaching 'ismetroonfire.com.' please try again in a few minutes."
        should_end_session = True
    elif flag == "unknown_station":
        speech_output = "The Metro transit website is unresponsive. Please try again in a few minutes."
        should_end_session = True

    # Unrecognized line from GetTimes
    elif line == "line":
        speech_output = "sorry, I don't recognize that line. Please repeat your request using a valid metro line."
        should_end_session = False

    # Unknown Problem
    else:
        speech_output = "Hmm. I seem to have encountered an internal error. Please try your request again."
        should_end_session = False

    return speech_output, should_end_session