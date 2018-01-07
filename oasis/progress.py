import sys


class Progress:
    """
    A silly little utility for reporting "percent complete" progress reports.
    """

    def __init__(self, total, report_increment=1):
        """
        :param total: The total number of items/elements being analyzed; the report method should be called this number
        of times during processing.
        :param report_increment: The percent complete modulo when report string should be output
        """
        self._total = total
        self._this = 0
        self._last_reported = 0
        self._report_increment = report_increment

    def report(self, format_str="  ... %s%% complete.\r",):
        """
        Notify that progress has been completed; produces a progress output string if the percent complete matches
        report_increment
        :param format_str: The string to be written (use %s as placeholder for percentage).
        :return: None
        """
        self._this += 1

        percent = int(float(self._this) / float(self._total) * 100)
        if percent != self._last_reported and percent % self._report_increment == 0:
            sys.stdout.write(format_str % str(percent))
            sys.stdout.flush()
            self._last_reported = percent
