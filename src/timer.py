"Class to time the runtime of calculation files"

import time
import logging
import os

log = logging.getLogger(__name__)


class Timer:
    "This class should be initiated at the start of each calculation's `run` function."

    def __init__(self):
        "Starts the timer"
        self.start_time = time.time()

    def end_timer(self, file):
        "Ends timer and prints file runtime"
        self.runtime = time.time() - self.start_time
        log.info(f"{file.split('/')[-1]} ran in {round(self.runtime, 1)} sec")
