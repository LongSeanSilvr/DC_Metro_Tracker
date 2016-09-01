import build_response as br
import metro_tools as mt
import httplib
from Train import *
from Station import *

import ujson as json
import urllib


# ======================================================================================================================
# Skill Intent: Get Times
# ======================================================================================================================
class GetTimes(object):
    def __init__(self, intent, session):
        self.session = session
        self.intent = intent
        self.user_id = session['user']['userId']
        self.card_title = "Train Times"
        self.reprompt_text = "What station would you like train times for?"
        self.src = self.get_station_info(self.intent, self.session)
        self.dst = self.get_station_info(self.intent, self.session, dst=True)
        self.line = self.get_line_info(self.intent)
        self.ideal_train = self.build_ideal_train()
        self.matching_trains = self.return_trains()

    def return_trains(self):
        """
        Check that src and dst are of class Station, and ideal_train is of class Train. If either class failed to build,
        they will have returned error strings instead of the target objects. If this is the case, return the error str.
        Otherwise, return the results
        :return: returns an error message if either src, dst, or ideal_train is an error string. Else returns list of
        upcoming trains for queried station.
        """
        if isinstance(self.src, (str, unicode)):
            return self.src
        elif isinstance(self.dst, (str, unicode)):
            return self.dst
        elif not isinstance(self.ideal_train, Train):
            return self.ideal_train

        upcoming_trains = self.query_station(self.ideal_train)

        if isinstance(upcoming_trains, list):
            return upcoming_trains
        else:
            return "unknown_error"

    def build_response(self):
        """
        Constructs speech output based on what is stored in self.matching_trains
        :return: json string containing alexa-formatted speech response
        """
        return br.build_response(self.card_title, self.matching_trains, station=self.src, destination=self.dst,
                                 line=self.line, reprompt_text=self.reprompt_text)

    @staticmethod
    def get_station_info(intent, session, dst=False):
        """
        Creates a station object out of the information in the intent and session.
        :param intent: parsed json intent from lambda handler
        :param session: parsed json session from lambda handler
        :param dst: if true, extracts destination-station name instead of src-station
        :return: either a station object created from the intent/session info, or error string saying what went wrong
        """
        if dst:
            try:
                station_name = intent['slots']['destination']['value'].lower()
                if station_name in ("mordor", "dulles"):                  # Easter eggs
                    return station_name
            except KeyError:
                return None
        else:
            try:
                station_name = intent['slots']['station']['value']
            except KeyError:
                station_name = None
        user_id = session['user']['userId']

        try:
            station = Station(station_name, user_id)
            return station
        except NoHomeError:
            flag = "no_home"
        except NoOriginError:
            flag = "no_origin"
        except InvalidStationError:
            if not dst:
                flag = "invalid_station"
            else:
                flag = "invalid_destination"
        except Exception:
            flag = "unknown_error"
        return flag

    @staticmethod
    def get_line_info(intent):
        """
        Retrieves line info out of an intent, if there is line info to grab.
        :param intent: parsed json intent from handler
        :return: string containing line name, or None if no line is specified in the intent
        """
        try:
            line = intent['slots']['line']['value']
            line = line.split()[0]
        except KeyError:
            line = None
        return line

    def build_ideal_train(self):
        """
        Construct the ideal train desired by user based on src, dst, and line provided
        :return: Train object or error string indicating what went wrong
        """
        try:
            ideal_train = Train(self.src, self.dst, self.line, self.user_id)
            return ideal_train
        except SrcLineError:
            flag = "invalid_src_line"
        except DstLineError:
            flag = "invalid_dst_line"
        except StationIntersectionError:
            flag = "no_intersection"
        except SameStationError:
            flag = "same_stations"
        except Exception:
            flag = "unknown_error"
        return flag

    @staticmethod
    def retrieve_times(st_code):
        """
        Retrieves upcoming train times for station specified.
        :param st_code: 3 digit alphanumeric station code for any station in the DC metro system
        :return: list of upcoming trains or error string indicating what went wrong
        """
        headers = {'api_key': '0b6b7bdc525a4abc9d0ad9879bd5d17b',} # WMATA developer API key
        params = urllib.urlencode({})

        try:
            # Query WMATA API
            conn = httplib.HTTPSConnection('api.wmata.com')
            conn.request("GET", "/StationPrediction.svc/json/GetPrediction/{}?{}".format(st_code, params), "{body}",
                         headers)
            response = conn.getresponse()
            data = json.loads(response.read())
            conn.close()
        except Exception:
            # Throw error if anything at all goes wrong with get request
            return "WMATA_connection_problem"

        try:
            trains = [Train(train[u'LocationName'], train[u'DestinationName'], mt.code2line(train[u'Line']).split()[0],
                            train[u'Min']) for train in data[u'Trains']]
        except KeyError:
            # Throw error if API returns a blank or wonky train-line that is not recognized by code2line()
            return "unknown_line"

        return trains

    def query_station(self, ideal_train):
        """
        Gets a list of upcoming trains in the WMATA system with the same characteristics as user's ideal train
        :param ideal_train: Train object to use in filtering all upcoming trains in WMATA system
        :return: filtered list of upcoming trains, or error string indicating what went wrong
        """

        # Get train list
        trains = self.retrieve_times(ideal_train.src.station_code(ideal_train.line))

        # Filter trains if there are trains to filter
        trains = self.filter_times(trains, ideal_train) if isinstance(trains, list) else trains

        # Check for Easter Eggs
        if ideal_train.dst is not None:
            if any(ideal_train.dst.name.lower() == x for x in ["dulles", "mordor"]):
                return ideal_train.dst.name.lower()

        return trains

    def filter_times(self, trains, ideal_train):
        filtered_times = []
        for train in trains:
            if self.filter_engine(train, ideal_train):
                filtered_times.append(train)
        return filtered_times

    @staticmethod
    def filter_engine(train, ideal_train):
        """
        Checks whether characteristics of train match those of the ideal_train
        :param train: Train object to check
        :param ideal_train: Train object against which to check
        :return: Boolean. Returns True if characteristics of train match those of ideal_train, False otherwise.
        """
        # skip trains with no time info
        if not train.time:
            return False

        # Skip if train is already boarding or arriving -- unless you live in the station, you're not catching that one.
        elif train.time in ("BRD", "ARR"):
            return False

        # Skip if train is on wrong line for src
        elif train.line not in ideal_train.src.lines and train.line not in ("--", "ghost"):
            return False

        # Skip if train is on wrong line for dst
        elif ideal_train.dst and train.line not in ideal_train.dst.lines and train.line not in ("--", "ghost"):
            return False

        # If no destination is specified, skip the next steps and return True
        elif not ideal_train.dst:
            return True

        # Compare trajectories to filter for trains in right direction
        elif train.direction != "any" and train.direction != ideal_train.direction:
            return False

        # Compare last stops to make sure train goes far enough
        elif train.stops_left < ideal_train.stops_left:
            return False

        else:
            return True
