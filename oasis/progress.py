import sys


class Progress:

    def __init__(self, total, report_increment=1):
        self._total = total
        self._this = 0
        self._last_reported = 0
        self._report_increment = report_increment

    def report(self, format_str="  ... %s%% complete.\r",):
        self._this += 1

        percent = int(float(self._this) / float(self._total) * 100)
        if percent != self._last_reported and percent % self._report_increment == 0:
            sys.stdout.write(format_str % str(percent))
            sys.stdout.flush()
            self._last_reported = percent
