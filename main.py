import logging as log
import time
from CryptoSources import Coindesk, Poloniex
import postgrez

logname = time.strftime("%Y_%m_%d-%H_%M")
log.basicConfig(
    format='%(asctime)s  - %(module)s - %(levelname)s - %(message)s',
    level=log.DEBUG)#, # Change debug level to choose how verbose you want logging to be
    # filename=os.path.join('logs', logname+".txt"))



# coindesk = Coindesk('USD', '2017-09-01', '2017-09-02')
# results = coindesk.main()

poloniex = Poloniex('BTC_ETH', '2017-09-01', '2017-09-02')
results = poloniex.main()

print (len(results['data']))
print (results['data'][0])

postgrez.load('crypto', 'hist_prices', data=results['data'],
                columns=results['fields'])
