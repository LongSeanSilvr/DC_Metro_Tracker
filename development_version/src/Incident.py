

class Incident(object):
    def __init__(self, incident_json):
        self.delay_severity = incident_json['DelaySeverity']
        self.description = incident_json['Description']
        self.incident_type = incident_json['IncidentType']
        self.lines_affected = incident_json['LinesAffected'].split(";")
        self.passenger_delay = incident_json['PassengerDelay']
