from User import User
import build_response as br


class GetHome(object):
    def __init__(self, intent, session):
        self.card_title = "Home Station"
        self.reprompt_text = "Try saying what is my home station"
        self.user = User(session['user']['userId'])
        self.home = self.user.get_home()

    def build_response(self):
        if self.home:
            flag = "home_report"
        else:
            flag = "missing_home"
        return br.build_response(self.card_title, flag, station=self.home, reprompt_text=self.reprompt_text)


class UpdateHome(object):
    def __init__(self, intent, session):
        self.intent = intent
        self.card_title = "Updating Home Station"
        self.reprompt_text = "To update your home station say, for example, set my home station to Dupont Circle"
        self.user = User(session['user']['userId'])
        self.flag = self.set_flag()
        self.home = self.user.get_home()

    def set_flag(self):
        try:
            flag = self.user.set_home(self.intent['slots']['home']['value'])
        except:
            flag = 'invalid_home'
        return flag

    def build_response(self):
        return br.build_response(self.card_title, self.flag, station=self.home, reprompt_text=self.reprompt_text)

