# crypto-data

This is a quick repo I pulled together for fetching and storing historical cryptocurrency data from various sources. Each source is programmed as an individual class in `CryptoSources.py`. Currently, I have Coindesk and Poloniex as two different data sources.


## Usage
First, create a table in a Postgres database.

```sql
CREATE TABLE hist_prices (
  snap_time timestamp,
  ticker VARCHAR(10),
  data_source VARCHAR(30),
  high DECIMAL,
  low DECIMAL,
  open DECIMAL,
  close DECIMAL,
  weighted_avg DECIMAL,
  base_volume DECIMAL,
  quote_volume DECIMAL
)
```

Then install [postgrez](https://github.com/ian-whitestone/postgrez) and setup your database connection parameters in the `~/.postgrez` yaml config file. Once setup, you can run the following:

`$ python main.py --source poloniex --ticker BTC_ETH --start 2017-07-01 --end 2017-09-01 --period 5`

to retrieve and store pricing data for the Bitcoin/Ethereum pair at 5-minute intervals.

## Behind the scenes
This project implements a simple ETL pipeline. After each source's API is hit, the retrieved data is sent through a set of cleaning functions, as specified by the `config.yaml` file. These functions do things like check if the supplied fields are integers, floats, dates, or epoch dates and convert where necessary.

The config file looks like this:

```yaml
coindesk:
  fields:
    timestamp:
      cleaning_func: check_epoch
      mapped_name: snap_time
    price:
      cleaning_func: check_float
      mapped_name: close

poloniex:

```

For each field returned in the Coindesk API response (i.e. timestamp & price), it specifies the cleaning function to pass each value through, and the associated column name in the database. The latter is done since each source won't necessarily have all the fields in `hist_prices`. With coindesk, they only have a price and a timestamp.
