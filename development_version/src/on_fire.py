import build_response as br
import re
import ujson as json
import urllib


# ======================================================================================================================
# Skill Intent: On Fire?
# ======================================================================================================================
class OnFire(object):
    def __init__(self, intent, session):
        self.card_title = "Is Metro On Fire?"
        self.reprompt_text = "Ask whether the metro is on fire"
        self.fire_lines = self.lines_on_fire()

    @staticmethod
    def lines_on_fire():
        try:
            fire_data = urllib.urlopen("https://ismetroonfire.com/fireapi").read()
            fire_data = json.loads(fire_data)
            fire_lines = [line for line in fire_data['counts'] if fire_data['counts'][line]]
            flag = fire_lines
        except Exception:
            flag = "fire_conn_prob"
        return flag

    def build_response(self):
        if self.fire_lines == "fire_conn_problem":
            flag = "fire_conn_problem"
            speech_output = None

        elif not self.fire_lines:
            flag = "fire_report"
            speech_output = "Not right this minute, but I'm sure it will be soon enough"

        elif isinstance(self.fire_lines, list):
            flag = "fire_report"

            if len(self.fire_lines) == 1:
                speech_output = "As usual, the {} line is on fire today.".format(self.fire_lines[0])

            else:
                speech_output = "As usual, "
                for i in xrange(len(self.fire_lines)):
                    if len(self.fire_lines) - i == 1:
                        speech_output += "and "
                    speech_output += "the {} line, ".format(self.fire_lines[i])
                speech_output = speech_output[0:-2]
                speech_output += " are on fire today."
                if len(self.fire_lines) == 2:
                    speech_output = re.sub(r', and', r' and', speech_output)

        else:
            flag = "unknown error"
            speech_output = None

        return br.build_response(self.card_title, flag=flag, text=speech_output,
                                 reprompt_text=self.reprompt_text)