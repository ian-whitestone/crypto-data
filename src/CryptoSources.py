"""This module holds the different classes for each cryptocurrency site or API
where data is retrieved from.

Each class has a main() method which returns data in the form:

results = {
    'fields': ['snap_time', 'close', 'ticker', 'source']
    'data': [
        ['2017-01-01 22:30', 14.12, 'BTC_ETH', 'poloniex'],
        ['2017-01-01 22:35', 14.11, 'BTC_ETH', 'poloniex'],
        ['2017-01-01 22:40', None, 'BTC_ETH', 'poloniex'],
        ['2017-01-01 22:45', 13.33, 'BTC_ETH', 'poloniex'],
        ...
    ]
}

Where fields is the corresponding column names in the database, and data is
a list of rows that contain each of those columns. Another example could be:

results = {
    'fields': ['snap_time', 'open', 'close', 'high', 'low', 'ticker', 'source']
    'data': [
        ['2017-01-01 22:30', 14.11, 14.12, 14.13, 14.11, 'BTC_ETH', 'poloniex'],
        ['2017-01-01 22:35', 14.12, 14.11, 14.14, 14.10, 'BTC_ETH', 'poloniex'],
        ['2017-01-01 22:40', None, None, None, None, 'BTC_ETH', 'poloniex'],
        ...
    ]
}

"""

from src.utils import DataCleaning, get_response, read_yaml, convert_to_epoch
import datetime
import logging as log

CONFIG = read_yaml('src/config.yaml')


def clean_data(data, fields):
    """Takes a list of dicts and cleans each field
    according to the cleaning functions specified in fields.

    Args:
        data (list): List of dicts, where each dict is {'field1': val1, ...}
        fields (dict): A dictionary that defines each fields cleaning function,
            along with any arguments required by that cleaning function. Fields
            must be in the following format:
            {
                'field1': {
                    'cleaning_func': 'func_name',
                    'args': {'arg1':val1, 'arg2'}
                },
                'field2':{

                }, ...
            }
            where the args component of each field is optional, and dependent on
            the cleaning function.
    Returns:
        cleaned_data (list): List of dicts, where each dict is
            {'field1': cleaned_val1, ...}. Note, the field names here are still
            the original field names from the API response.
    """
    log.info('Attempting to clean %s records' % (len(data)))
    cleaned_data = []
    all_fields = fields.keys()

    ## create a base dict with all the fields we expect in each record of data
    base_dict = {key: None for key in all_fields}

    for record in data:
        ## create a copy of the base_dict, to be updated with the cleaned values
        cleaned_record = base_dict.copy()

        for var in all_fields:
            val = record.get(var, None)
            if val:
                func = fields[var]['cleaning_func']
                cleaned_record[var] = getattr(DataCleaning, func)(val=val,
                                args=fields[var].get('args', None))
            else:
                cleaned_record[var] = None

        cleaned_data.append(cleaned_record)

    return cleaned_data

class Coindesk():
    """Class that can be called to retrieve data from the coindesk site internal
    APIs.
    """
    def __init__(self, ticker, start_date=None, end_date=None):
        """
        Args:
            ticker (str): Accepts USD for bitcoin, ETH for ethereum.
            start_date (str): start date in format YYYY-mm-dd. Defaults to
                yesterday.
            end_date (str): end date in format YYYY-mm-dd. Defaults to today.
        """
        self.source = 'coindesk'
        self.config = CONFIG.get(self.source, None)
        if self.config is None:
            log.error('%s has not been added to ./config.yaml. Exiting...'
                % self.source)

        self.base_url = ('https://api.coindesk.com/charts/data?output=json&'
            'data=close&index={0}&startdate={1}&enddate={2}'
            '&exchanges=bpi&dev=1')
        self.url = None

        self.tickers = ['USD', 'ETH']
        self.default_ticker = 'USD'
        self.ticker = ticker

        self.date_format = '%Y-%m-%d'
        self.start_date = start_date
        self.end_date = end_date

        self._validate_dates()
        self._validate_ticker()


        self._build_url()
        return

    def _validate_dates(self):
        today_dt = datetime.datetime.today()
        today = today_dt.strftime(self.date_format)
        yest_dt = today_dt -datetime.timedelta(1)
        yest = yest_dt.strftime(self.date_format)

        start_dt_check = DataCleaning.check_date(date_text=self.start_date,
                            date_format=self.date_format)
        end_dt_check = DataCleaning.check_date(date_text=self.end_date,
                            date_format=self.date_format)

        if self.start_date is None or start_dt_check == False:
            log.warning('Incorrect start date supplied, defaults to %s' % yest)
            self.start_date = yest
        elif datetime.datetime.strptime(self.start_date, self.date_format) \
                > today_dt:
            self.start_date = yest

        if self.end_date is None or end_dt_check == False:
            log.warning('Incorrect end date supplied, defaults to %s' % today)
            self.end_date = today
        elif datetime.datetime.strptime(self.end_date, self.date_format) \
                > today_dt:
            self.end_date = today

        return

    def _validate_ticker(self):
        if self.ticker not in self.tickers:
            log.warning('Specified ticker %s not in Coindesk allowable tickers.'
                'Defaulting to %s.' % (self.ticker, self.default_ticker))
            self.ticker = self.default_ticker
        return

    def _build_url(self):
        self.url = self.base_url.format(self.ticker, self.start_date,
                                            self.end_date)
        return

    def _parse_response(self, resp):
        """Takes the response object and returns data as a list of dicts, where
        each dict is in the form {'field1':val1, 'field2':val2} where each field
        has been defined in the fields key of ./config.yaml.
        """
        data = None
        try:
            log.debug('Attempting to parse response')
            raw_data = eval(resp.text.replace('cb(','').replace(');',''))
            data = [{'timestamp': record[0], 'price': record[1]}
                        for record in raw_data['bpi']]
        except Exception as e:
            log.error('Unable to parse response. Error %s' % (e))
        return data


    def main(self):
        resp = get_response(self.url)
        if resp is None:
            log.warning('No response object returned. Exiting...')
            return

        data = self._parse_response(resp)
        if data is None:
            log.warning('No data was parsed from response. Exiting...')
            return

        cleaned_data = clean_data(data, self.config['fields'])

        field_map = {d['mapped_name']:key
                        for key, d in self.config['fields'].items()}

        injection_data = []
        table_fields = [key for key in field_map.keys()]

        ##TODO: coindesk randomly returns shit outside of specified range,
        ## delete anything outside of start date/end date
        for record in cleaned_data:
            injection_record = []
            for key in table_fields:
                injection_record.append(record[field_map[key]])
            injection_record += [self.ticker, self.source]
            injection_data.append(injection_record)

        table_fields += ['ticker', 'data_source']
        return {'fields': table_fields, 'data': injection_data}




class Poloniex():
    """Class that can be called to retrieve data from the poloniex site internal
    APIs.
    """
    def __init__(self, ticker_pair, start_date=None, end_date=None,
        period=1800):
        """
        Args:
            ticker (str): Accepts a ticker pair in the form ticker1_ticker2
                i.e. BTC_ETH or BTC_LTC.
            start_date (str): start date in format YYYY-mm-dd. Defaults to
                yesterday.
            end_date (str): end date in format YYYY-mm-dd. Defaults to today.
            period (int): Interval to retrieve quotes for in seconds. Defaults
                to 30 min (1800s)
        """
        self.source = 'poloniex'
        self.config = CONFIG.get(self.source, None)
        if self.config is None:
            log.error('%s has not been added to ./config.yaml. Exiting...'
                % self.source)

        self.base_url = ('https://poloniex.com/public?command=returnChartData'
            '&currencyPair=BTC_ETH&start=1498881600&end=9999999999&period=300')
        self.base_url = ('https://poloniex.com/public?command=returnChartData'
            '&currencyPair={0}&start={1}&end={2}&period={3}')
        self.url = None

        self.ticker = ticker_pair
        self.period = period

        self.date_format = '%Y-%m-%d'
        self.start_date = start_date
        self.end_date = end_date

        self._validate_dates()
        self._convert_dates()
        self._validate_ticker()


        self._build_url()
        return

    def _validate_dates(self):
        today_dt = datetime.datetime.today()
        today = today_dt.strftime(self.date_format)
        yest_dt = today_dt -datetime.timedelta(1)
        yest = yest_dt.strftime(self.date_format)

        start_dt_check = DataCleaning.check_date(date_text=self.start_date,
                            date_format=self.date_format)
        end_dt_check = DataCleaning.check_date(date_text=self.end_date,
                            date_format=self.date_format)

        if self.start_date is None or start_dt_check == False:
            log.warning('Incorrect start date supplied, defaults to %s' % yest)
            self.start_date = yest

        elif datetime.datetime.strptime(self.start_date, self.date_format) \
                > today_dt:
            self.start_date = yest

        if self.end_date is None or end_dt_check == False:
            log.warning('Incorrect end date supplied, defaults to %s' % today)
            self.end_date = today
        elif datetime.datetime.strptime(self.end_date, self.date_format) \
                > today_dt:
            self.end_date = today

        return

    def _convert_dates(self):
        self.start_date = convert_to_epoch(self.start_date)
        self.end_date = convert_to_epoch(self.end_date)
        return

    def _validate_ticker(self):
        if '_' not in self.ticker:
            raise Exception('Invalid ticker supplied. Ticker must be in format'
                             ' ticker1_ticker2')
        base_ticker = self.ticker.split('_')[0]
        quote_ticker = self.ticker.split('_')[1]

        if base_ticker not in self.config['tickers'].keys():
            raise Exception('Base ticker %s not in Poloniex supported base '
                        'tickers: %s' %
                        (base_ticker, list(self.config['tickers'].keys())))

        if quote_ticker not in self.config['tickers'][base_ticker]:
            raise Exception('Quote ticker %s not in Poloniex supported tickers '
                        'for base ticker %s: %s' % (quote_ticker, base_ticker,
                        self.config['tickers'][base_ticker]))

        return

    def _build_url(self):
        self.url = self.base_url.format(self.ticker, self.start_date,
                                            self.end_date, self.period)
        return

    def _parse_response(self, resp):
        """Takes the response object and returns data as a list of dicts, where
        each dict is in the form {'field1':val1, 'field2':val2} where each field
        has been defined in the fields key of ./config.yaml.
        """
        data = None
        try:
            log.debug('Attempting to parse response')
            data = resp.json()
        except Exception as e:
            log.error('Unable to parse response. Error %s' % (e))
        return data


    def main(self):
        resp = get_response(self.url)
        if resp is None:
            log.warning('No response object returned. Exiting...')
            return

        data = self._parse_response(resp)
        if data is None:
            log.warning('No data was parsed from response. Exiting...')
            return

        if isinstance(data, dict) and 'error' in data.keys():
            log.error('No data returned from response. Error message %s. '
                        'Exiting...' % data['error'])
            return

        cleaned_data = clean_data(data, self.config['fields'])

        field_map = {d['mapped_name']:key
                        for key, d in self.config['fields'].items()}

        injection_data = []
        table_fields = [key for key in field_map.keys()]
        for record in cleaned_data:
            injection_record = []
            for key in table_fields:
                injection_record.append(record[field_map[key]])
            injection_record += [self.ticker, self.source]
            injection_data.append(injection_record)

        table_fields += ['ticker', 'data_source']
        return {'fields': table_fields, 'data': injection_data}
