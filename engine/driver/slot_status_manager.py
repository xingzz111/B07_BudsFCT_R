import time
import ast
import re
import threading

class SlotManager(object):
    TEST_STATUS = ("IDLE", "TESTING", "FINISH")

    def __init__(self, publisher=None):
        self._slot_test_status = ["IDLE", "IDLE", "IDLE", "IDLE"]
        self._lock = threading.RLock()

    def update_test_status(self, site):
        with self._lock:
            self._slot_test_status[site] = "TESTING"

    def update_finish_status(self, site):
        with self._lock:
            self._slot_test_status[site] = "FINISH"


    def check_other_slot_finish(self, site):
        with self._lock:
            for i in range(len(self._slot_test_status)):
                if i != site and self._slot_test_status[i] == "TESTING":
                    print(f"False>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>site{site}:{self._slot_test_status}")
                    return False
            print(f"True>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>site{site}:{self._slot_test_status}")
            return True


if __name__ == "__main__":
    pass