import logging as log
import time
import argparse


from CryptoSources import Coindesk, Poloniex
import postgrez


logname = time.strftime("%Y_%m_%d-%H_%M")
log.basicConfig(
    format='%(asctime)s  - %(module)s - %(levelname)s - %(message)s',
    level=log.DEBUG)#, # Change debug level to choose how verbose you want logging to be
    # filename=os.path.join('logs', logname+".txt"))


parser = argparse.ArgumentParser(description='Crypto Data - Main Program')

parser.add_argument('--ticker', default='', help='Ticker to use')
parser.add_argument('--start', default='', help='Start date. YYYY-mm-dd')
parser.add_argument('--end', default='', help='End date. YYYY-mm-dd')
parser.add_argument('--source', default='Poloniex',
                        help='Source to pull data from')
parser.add_argument('--period', default=30, help='Time interval frequency for '
                        'historical data, in minutes')
args = parser.parse_args()


## TODO: pull the last date historized automatically

if args.source == 'Poloniex':
    crypto = Poloniex(args.ticker, start_date=args.start, end_date=args.end,
                            period=int(args.period)*60)
elif args.source == 'Coindesk':
    crypto = Coindesk(args.ticker, args.start, args.end)

results = crypto.main()

if results:
    postgrez.load('crypto', 'hist_prices', data=results['data'],
                    columns=results['fields'])
