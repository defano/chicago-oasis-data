import urllib2
import tempfile
import os.path


class DataSet:

    def __init__(self, force_reload=False):
        self.__force_reload = force_reload

    def get_dictionary(self):
        raise Exception("Bug! Not implemented in subclass.")

    def get_remote_url(self):
        raise Exception("Bug! Not implemented in subclass.")

    def get_local_filename(self):
        raise Exception("Bug! Not implemented in subclass.")

    def preprocess_downloaded_file(self, data):
        """
        Performs any required transformation on the downloaded data prior to it being used in analysis.

        Override in subclasses to allow different data sources to be pre-processed differently. Datasets that require
        no pre-processing should simply return the input argument.

        :param data: The data to be pre-processed
        :return: The pre-processed data; simply return 'data' to perform no pre-processing
        """
        return data

    def get_cache_file_path(self):
        """
        An absolute, local, file path where this dataset is stored on disk.
        :return:
        """
        return self.get_cache_directory() + '/' + self.get_local_filename()

    def get_cache_directory(self):
        """
        Gets the directory where cache files are stored, typically the OS-provided "temp" directory.
        :return: The directory where cached files are stored
        """
        return tempfile.gettempdir()

    def read_cache(self):
        """
        Returns the requested dataset, downloading it and storing it in the cache if needed.

        :return: An absolute path to the data saved on the local filesystem
        """
        cache_file_path = self.get_cache_file_path()
        if os.path.exists(cache_file_path) and not self.__force_reload:
            # print("Getting cached data from " + cache_file_path)
            return cache_file_path
        else:
            print("Downloading data from " + self.get_remote_url() + ". (It's going to space, give it a minute.)")
            self.__force_reload = False       # Do not download more than once, even when forced
            return self.load_cache(cache_file_path)

    def load_cache(self, cache_file_path):
        """
        Downloads the given URL and stores the data at the given file path.
        :param cache_file_path: The location on the filesystem where the data should be written
        :return: cache_file_path
        """
        cache_file = open(cache_file_path, 'w')
        data = urllib2.urlopen(self.get_remote_url())
        try:
            cache_file.write(self.preprocess_downloaded_file(data.read()))
            print(cache_file)
        finally:
            cache_file.close()
        return cache_file_path

    def validate(self, csv):
        """
        Validates that the dataset contains all columns used by this analysis.

        Determines which columns are required by evaluating self for instance variables whose name starts with "ROW_".
        Subclasses should define an instance variable for every row in the dataset they expect to be consumed. 

        :param csv: A CSV DictReader containing the loaded data
        :return: The CSV DictReader passed as an argument (for method chaining)
        """
        for row in self.__dict__.keys():
            if row.startswith("ROW_") and self.__dict__[row] not in csv.fieldnames:
                raise Exception("Row missing from dataset: " + str(self.__dict__[row]))
        return csv
