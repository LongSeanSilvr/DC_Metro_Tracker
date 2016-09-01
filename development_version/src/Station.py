"""
Station class for use in Metro_Tracker.py
"""
import ujson as json
from boto3 import client


class Station(object):
    with open("stations.json", "rb") as f:
        station_data = json.loads(f.read())

    def __new__(cls, station_name=None, user_id=None):
        # Fail to instantiate if neither argument is supplied
        if not station_name and not user_id:
            raise ValueError

        # Fail to instantiate if invalid station is provided
        elif (
                    station_name and
                    not station_name.lower() in ("here", "home", "my home") and
                    not any(cls.essentialize_station_name(station_name.lower()) in station.lower() for
                            station in Station.station_data.keys())
        ):
            raise InvalidStationError

        else:
            return super(Station, cls).__new__(cls)

    def __init__(self, station_name=None, user_id=None):
        # fix common mis-hearings in station_name (e.g. "willy reston" rather than "Wiehle Reston"
        station_name = self.essentialize_station_name(station_name)
        # Get home station as origin if no origin specified or user asks for home as origin
        station_name = self.home_check(station_name, user_id)

        # set fields
        self.name = [station for station in Station.station_data.keys() if station_name.lower() in station.lower()][0]
        self.full_details = Station.station_data[self.name]
        self.line_details = [{line: Station.station_data[self.name][line]} for line in Station.station_data[self.name]]
        self.lines = [line for line in Station.station_data[self.name]]
        self.station_codes = list({Station.station_data[self.name][line]['code'] for line in
                                   Station.station_data[self.name]})

    def home_check(self, station_name, user_id):
        if station_name is None or station_name.lower() in ("here", "home", "my home"):
            try:
                return self.lookup_home(user_id)
            except:
                error = NoHomeError if station_name else NoOriginError
                raise error
        else:
            return station_name

    def station_code(self, line):
        code = self.full_details[line]['code'] if line else self.full_details[self.lines[0]]['code']
        return code

    def line_index(self, line):
        return self.full_details[line]['line_index']

    @staticmethod
    def lookup_home(user_id):
        cl = client('dynamodb')
        home_item = cl.get_item(TableName='metro_times_user_ids', Key={'user_id': {'S': user_id}},
                                ProjectionExpression="home")
        station_name = home_item['Item']['home']['S']
        return station_name

    @staticmethod
    def essentialize_station_name(station):
        if station is None:
            return None
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


class InvalidStationError(ValueError):
    pass


class NoHomeError(ValueError):
    pass


class NoOriginError(ValueError):
    pass


# ======================================================================================================================
# run
# ======================================================================================================================
if __name__ == "__main__":
    Station("noma")
