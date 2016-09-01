import boto3
import build_response as br
from datetime import datetime
from time import time
import ujson as json


# ======================================================================================================================
# Auxiliary and Shared Functions
# ======================================================================================================================
def code2line(line, reverse=False):
    line = line.strip()
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


def track_user(session, action):
    client = boto3.client('dynamodb')
    User_ID = session['user']['userId']
    now = datetime.now()
    access_time = "{} -- {:02d}:{:02d}".format(now.date(), now.hour, now.minute)
    client.update_item(TableName='MetroTracker_Users', Key={'User_ID': {'S': User_ID}},
                       ExpressionAttributeValues={":Last_Accessed": {"S": access_time},
                                                  ":Function": {"S": action}},
                       UpdateExpression='SET Last_Accessed = :Last_Accessed,'
                                        'Intent = :Function')

