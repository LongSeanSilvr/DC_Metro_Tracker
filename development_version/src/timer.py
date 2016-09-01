from time import time


class Timer(object):
    """
    Decorator that times whatever function it decorates
    """
    def __init__(self, fn):
        self.fn = fn

    def __call__(self, *args):
        start = time()

        self.fn(*args)

        sec_tot = int(time() - start)
        hrs = sec_tot / 3600
        min = (sec_tot / 60) - (hrs * 60)
        sec = sec_tot % 60
        runtime = "HRS: {} MINS: {} SECS: {}".format(hrs, min, sec)

        print "\nCompleted in: {}".format(runtime)