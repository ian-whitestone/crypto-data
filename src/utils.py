import requests
import yaml
import logging as log
import time
import datetime

def read_yaml(yaml_file):
    """Read a yaml file.

    Args:
        yaml_file (str): Full path of the yaml file.

    Returns:
        data (dict): Dictionary of yaml_file contents.
            None is returned if an error occurs while reading.

    Raises:
        Exception: If the yaml_file cannot be opened
    """
    data = None
    try:
        with open(yaml_file) as f:
            # use safe_load instead load
            data = yaml.safe_load(f)
    except Exception as e:
        log.error('Unable to read file %s. Error: %s' % (yaml_file, e))
        raise
    return data

def convert_to_epoch(date, date_format='%Y-%m-%d'):
    """Convert a string date to Epoch GMT time.

    Args:
        date (str): Date string
        date_format (str): Date format of the supplied date string. Defaults to
            '%Y-%m-%d'

    Returns:
        epoch_time (int): Epoch GMT time

    """

    return int(time.mktime(time.strptime(date, date_format)))

def get_response(url):
    """Retrieve the response from a url.

    Args:
        url (str): Url to retrieve response from.

    Returns:
        resp (requests.models.Response): Requests response object. If the
            resp.status_code != 200, returns None
    """
    log.info('Retrieving response from %s' % url)
    resp = None
    try:
        resp = requests.get(url)#, data=json.dumps(r_payload), headers=self.headers)
        if resp.status_code != 200:
            resp = None
            log.error('Unable to get response, status code %s'
                        % resp.status_code)
    except Exception as e:
        log.error("Error getting response %s" % e)

    return resp


class DataCleaning():
    # TODO: rethink this class
    def __init__(self):
        pass

    @classmethod
    def check_int(cls, **kwargs):
        """Function to check if the field is an integer and convert if necessary"""
        int_check = isinstance(kwargs['val'], int )
        val = kwargs['val']
        if int_check == False:
            try:
                val = int(kwargs['val'])
            except Exception as e:
                log.debug('Unable to convert %s to an integer due to error %s'
                    % (val, e))
                val = None
        return val


    @classmethod
    def check_float(cls, **kwargs):
        """Function to check if the field is a float and convert if necessary"""
        float_check = isinstance(kwargs['val'], float )
        val = kwargs['val']
        if float_check == False:
            try:
                val = float(kwargs['val'])
            except Exception as e:
                log.debug('Unable to convert %s to an integer due to error %s'
                    % (val, e))
                val = None
        return val

    @classmethod
    def check_varchar(cls, **kwargs):
        """Function to censure the field is the correct length and
            trunctuate if necessary.
        """
        val = kwargs['val']
        try:
            cleaned_val = str(val)[0:kwargs['args']['length']]
            cleaned_val = cleaned_val.replace('\\','')
        except Exception as e:
            log.debug('Unable to convert %s to a string due to error %s' %
                    (val, e))
            cleaned_val = None
        return cleaned_val

    @classmethod
    def check_text(cls, **kwargs):
        """Function to ensure the field is a string"""
        val = kwargs['val']
        try:
            cleaned_val = str(val)
            cleaned_val = cleaned_val.replace('\\','')
        except Exception as e:
            log.debug('Unable to convert %s to a string due to error %s' %
                    (val, e))
            cleaned_val = None
        return cleaned_val

    @classmethod
    def do_none(cls, **kwargs):
        return kwargs['val']

    @classmethod
    def check_epoch(cls, **kwargs):
        """Checks if the supplied value is an 10 or 13 digit integer. If it is,
        returns a parsed time in the format '%Y-%m-%d %H:%M'. Otherwise, returns
        None.
        """
        timestamp = kwargs['val']
        if isinstance(timestamp, int) == False:
            try:
                timestamp = int(timestamp)
            except:
                return None

        if len(str(timestamp)) == 13:
            timestamp = int(timestamp/1000)
        elif len(str(timestamp)) != 10:
            return None

        return time.strftime('%Y-%m-%d %H:%M', time.gmtime(timestamp))

    @classmethod
    def check_date(cls, **kwargs):
        date_text = kwargs['date_text']
        date_format = (kwargs['date_format'] if kwargs['date_format']
                        else '%Y-%m-%d')
        if isinstance(date_text, str) == False:
            return False

        try:
            datetime.datetime.strptime(date_text, date_format)
            return True
        except ValueError:
            # raise ValueError("Incorrect data format, should be YYYY-MM-DD")
            return False
