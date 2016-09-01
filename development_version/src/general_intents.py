import build_response as br


# ======================================================================================================================
# Skill Behavior: Welcome Response
# ======================================================================================================================
class Welcome(object):
    def __init__(self):
        self.card_title = "Welcome"
        self.reprompt_text = "What station would you like train times for?"
        self.flag = "welcome"

    def build_response(self):
        output = br.build_response(self.card_title, self.flag, reprompt_text=self.reprompt_text)
        return output


# ======================================================================================================================
# Skill Intent: Help
# ======================================================================================================================
class Help(object):
    def __init__(self, intent, session):   # Parameters are here so handler can treat this like the other intent classes
        self.card_title = "Help"
        self.reprompt_text = "What station would you like train times for?"
        self.flag = "help"

    def build_response(self):
        output = br.build_response(self.card_title, self.flag, reprompt_text=self.reprompt_text)
        return output


# ======================================================================================================================
# Skill Intent: Quit
# ======================================================================================================================
class Exit(object):
    def __init__(self, intent, session):   # Parameters are here so handler can treat this like the other intent classes
        self.card_title = "Exiting"
        self.flag = "exit"

    def build_response(self):
        output = br.build_response(self.card_title, self.flag)
        return output
