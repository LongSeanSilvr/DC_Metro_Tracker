"""
This app returns train times for the Metro DC transit system.
To Profile: -m cProfile -o profile_results.prof
"""

from __future__ import print_function
import metro_tools as mt
import sys
import ujson as json

# Skill intents
from general_intents import Welcome
from general_intents import Help
from general_intents import Exit
from get_times import GetTimes
from home_intents import GetHome
from home_intents import UpdateHome
from on_fire import OnFire


# ======================================================================================================================
# Handler
# ======================================================================================================================
def lambda_handler(event, context=None):
    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])


# ======================================================================================================================
# Session Event Functions
# ======================================================================================================================
def on_launch(launch_request, session):
    mt.track_user(session, u'Launch')
    return Welcome().build_response()


def on_intent(intent_request, session):
    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']
    mt.track_user(session, intent_name)
    intent_dict = {
        'GetTimes': GetTimes,
        # 'CommuteEstimate': commute_estimate,
        # 'Incidents': get_incidents,
        'OnFire': OnFire,
        'UpdateHome': UpdateHome,
        'GetHome': GetHome,
        'Help': Help,
        'Exit': Exit
    }
    if intent_name in intent_dict.keys():
        return intent_dict[intent_name](intent, session).build_response()
    else:
        raise ValueError("Invalid intent")


# ======================================================================================================================
# Run if invoked directly
# ======================================================================================================================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        event_file = sys.argv[1]
        with open(event_file, "rb") as f:
            event = json.loads(f.read())
    else:
        with open("test_event.json", "rb") as f:
            event = json.loads(f.read())
    lambda_handler(event)
