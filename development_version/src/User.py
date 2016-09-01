"""
User Class
"""
import boto3
from Station import Station, InvalidStationError


class User(object):
    def __init__(self, user_id):
        self.user_id = user_id

    def set_home(self, station_name):
        try:
            home = Station(station_name)
            client = boto3.client('dynamodb')
            try:
                client.update_item(TableName='metro_times_user_ids',
                                   Key={'user_id': {'S': self.user_id}},
                                   ExpressionAttributeValues={":home": {"S": home.name}},
                                   UpdateExpression='SET home = :home')
                flag = "home_updated"
            except Exception:
                flag = "UserID_Database_prob"
        except InvalidStationError:
            flag = "invalid_home"
        return flag

    def get_home(self):
        client = boto3.client('dynamodb')
        try:
            home_item = client.get_item(TableName='metro_times_user_ids', Key={'user_id': {'S': self.user_id}},
                                        ProjectionExpression="home")
            home = home_item['Item']['home']['S']
        except Exception:
            home = None
        return home
