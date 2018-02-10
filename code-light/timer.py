# -*- coding: UTF-8 -*-
# The license of this file is unknown.
# The code is based on this file from GitHub
# https://github.com/jalmeroth/homie-python/blob/master/homie/timer.py

import time
import logging
import threading
logger = logging.getLogger(__name__)


class InfiniteTimer(threading.Thread):
    """A Timer class that does not stop."""

    def __init__(self, t, f, group=None, target=None, name=None):
        threading.Thread.__init__(self, group=group, target=target, name=name)
        self.daemon = True
        self.t = t
        self.f = f

    def run(self):
        starttime = time.time()
        while True:
            self.f()
            # figure out how much sleep remains, after f() was executed
            delay = self.t - ((time.time() - starttime) % self.t)
            # logger.debug("Delay: {}".format(delay))
            time.sleep(delay)
