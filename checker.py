from proxy_checker import ProxyChecker
from proxyscrape import create_collector, get_collector
from threading import Thread,current_thread,Lock
from multiprocessing.pool import ThreadPool as Pool
import requests
from queue import Queue
from timeit import default_timer as timer
from datetime import datetime, timedelta
import json
import logging
from types import SimpleNamespace
from tqdm import tqdm
import pytz
from bs4 import BeautifulSoup as bs
import time
from time import sleep
from pymongo import MongoClient,ASCENDING
import argparse
import os,sys


def clear():
    is_windows = sys.platform.startswith('win')
    if is_windows:
        os.system('cls')
    else:
        os.system('clear')

try:
    os.system('apt install libcurl4-openssl-dev libssl-dev')
except:
    clear()

# create logger
logger = logging.getLogger('Proxy Checker')
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s | %(name)s (%(threadName)s) | %(levelname)s | %(message)s',datefmt='%d/%m/%Y %I:%M:%S %p')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)

connection_string = 'NONE'

client = MongoClient(connection_string)
db = client.proxies
tz = pytz.timezone('Asia/Jerusalem')
parser = argparse.ArgumentParser(description="Proxy Grabber & Checker By MatanMalka94")
parser.add_argument("-c",type=int,default=5, help='the default cooldown is 5 minutes')
parser.add_argument("-t",type=int,default=50, help='default threads is 50')
parser.add_argument("-u",type=str,default='n', help='upload working proxies to mongodb funcunalty default is "n" use "y" to upload to your mongodb.')
parser.add_argument("-s",type=str,default='n', help='save to working proxies to txt file default is "n" use "y" to save to proxies.txt if file is not exists the script will create it automaticlly')
parser.add_argument("-l",type=str,default='n', help='run proxy grabber in loop ? default is "n" use "y" to run it loop')
args, leftovers = parser.parse_known_args()

types = ['http','socks4', 'socks5','https','http']
collector = create_collector('my-collector', types,refresh_interval=600)

checker = ProxyChecker()
working = []
working_proxies = []
bar = None
class ReadyProxy():
    def __init__(self,ip,port,protocols,anonymity,timeout,country,country_code,date) -> None:
        self.ip = ip
        self.port = port
        self.protocols = protocols
        self.anonymity = anonymity
        self.timeout = timeout
        self.country = country
        self.country_code = country_code
        self.date = date
        
    def __str__(self) -> str:
        return {
            'ip':self.ip,
            'port':self.port,
            'protocols':self.protocols,
            'anonymity':self.anonymity,
            'timeout':self.timeout,
            'country':self.country,
            'country_code':self.country_code,
            'date':self.date
        }
    
def proxyScrapeProxies():
    data = []
    #proxyscrape.com proxies
    for t in types:
        url = f'https://api.proxyscrape.com/?request=getproxies&proxytype=${t}&timeout=1200&country=all&ssl=all&anonymity=all'
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            content = str(response.content).split('\\r\\n')
            for ip in content:
                if ':' in ip:
                    d = ip.split(':')
                    data.append({'ip':d[0],'port':d[1]})
    #api.c99.nl proxies
    for t in types:
        url = f'https://api.c99.nl/proxylist?key=L270T-8QI3U-BRLJA-GAHD8&limit=4000&type={t}&anonimity=all&country=all'
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            content = str(response.content).split('<br />')
            for ip in content:
                if ':' in ip:
                    d = ip.split(':')
                    data.append({'ip':d[0],'port':d[1]})
        
    return data
        
def to_file():
    proxies = proxyScrapeProxies()
    t_proxies = collector.get_proxies()
    for proxy in t_proxies:
        proxies.append({'ip':proxy.host,'port':proxy.port})
    with open('proxies.txt','w',encoding='utf-8') as f:
        for proxy in proxies:
            f.write(f'{proxy["ip"]}:{proxy["port"]}\n')

       

def worker(q,lock):
    global working_proxies
    while True:
        proxy = q.get()
        c_ip = f'{proxy["ip"]}:{proxy["port"]}'
        
        result = checker.check_proxy(c_ip)
        if result:
            with lock:
                ready = ReadyProxy(proxy['ip'],proxy['port'],result['protocols'],result['anonymity'],result['timeout'],result['country'],result['country_code'],datetime.now(tz))
                working_proxies.append(ready)
                logger.info(f'{ready.ip}:{ready.port} is alive!')
        q.task_done()
    
def start_scanning():
    global args
    global working_proxies
    global bar
    logger.info(f'system has been started.')
    q = Queue()
    lock = Lock()
    num_threads = args.t
    for i in range(num_threads):
        thread = Thread(target=worker,args=(q,lock))
        thread.daemon = True
        thread.start()
    logger.info(f'{num_threads} threads loaded.')
        
    logger.info('getting proxies...')
    proxies = proxyScrapeProxies()
    t_proxies = collector.get_proxies()#{'code': 'us'})
    for proxy in t_proxies:
        proxies.append({'ip':proxy.host,'port':proxy.port})
    proxies = [dict(t) for t in {tuple(d.items()) for d in proxies}]
    # bar = tqdm(total=len(proxies), disable=False,desc='checking proxies.. ')
    
    logger.info(f'found {len(proxies)} proxies')
    for proxy in proxies:
        q.put(proxy)
    
    q.join()
    logger.info(f'Total working Proxies: {len(working_proxies)}')
    if args.u.lower() =='y':
        obj = {
                'check_date':datetime.now(tz),
                'proxies': [ i.__str__() for i in working_proxies ],
                'count':len(working_proxies)
            }
        doc = db.lists.insert_one(obj)
        logger.info(f'inserted scan to db scan id: {doc.inserted_id}')

        
    return working_proxies
    

def run():
    
    global bar 
    
    pool = Pool(args.threads)
    start = timer()
    print('getting proxies...')
    proxies = proxyScrapeProxies()
    t_proxies = collector.get_proxies()
    for proxy in t_proxies:
        proxies.append({'ip':proxy.host,'port':proxy.port})
        
    proxies = [dict(t) for t in {tuple(d.items()) for d in proxies}]
    print(f'Found {len(proxies)} Proxies')
    
    bar = tqdm(total=len(proxies), disable=False,desc='checking proxies.. ')

    
    pool.map(worker, proxies)
    pool.close()
    pool.join()
        
    bar.close()
    end = timer()
    print('total working:',len(working),'time:',timedelta(seconds=end-start))
    print('saving check to db...')
    obj = {
            'check_date':datetime.now(tz),
            'proxies': [ i.__str__() for i in working ],
            'count':len(working)
        }
    doc = db.lists.insert_one(obj)
    print('inserted list to db id:',doc.inserted_id)
    return working

def save_to_txt_file():
    global working_proxies
    if args.s.lower() =='y':
        print(f'Saving Working Proxies ({len(working_proxies)}) to proxies.txt')
        with open('proxies.txt','w') as fx:
            fx.write('')
        fx.close()
        
        with open('proxies.txt','w') as f:
            for proxy in working_proxies:
                if len(proxy.protocols) > 1:
                    for protocol in proxy.protocols:
                        f.write(f'{protocol}://{proxy.ip}:{proxy.port}\n')
                else:
                    f.write(f'{proxy.protocols[0]}://{proxy.ip}:{proxy.port}\n')
                    
    print(f'Saved Working Proxies ({len(working_proxies)}) to proxies.txt')


def main():
    global working_proxies
    global connection_string
    
    print(f'\t\tProxy Grabber & Checker By MatanMalka94\n')
    print(f'--Script Settings--')
    print(f'Threads:',args.t)
    print(f'Cooldown:',args.c,'Minute(s)')
    print(f'Upload to MongoDB:',args.u)
    print(f'Save To txt File:',args.s)
    print(f'Run Script in Loop:',args.l)
    
    if connection_string == 'NONE' and args.u.lower() =='y':
        print('[##ALERT##] please set your connection string for mongodb!')
    
    input('\n\nAre you sure you want to run this script with this settings ?\npress any key to start the script or CTRL+C to quit.\n')
    logger.info(f'Proxy Grabber & Checker has been started!')
    if args.l.lower() == 'y':    
        while True:
            start_scanning()
            logger.info(f'system has been restarted searching for new proxies...')
            save_to_txt_file()
            working_proxies = []
            logger.info(f'Cooldown has been started for {args.c} minute(s)')
            time.sleep(60 * args.c)
    else:
        start_scanning()
        logger.info(f'system has been restarted searching for new proxies...')
        save_to_txt_file()
        input('Script Done, Press any Key to quit.')
        
        
        


def apiC99Proxies():
    url = f'https://www.proxyrotator.com/free-proxy-list/1/#free-proxy-list'
    response = requests.get(url)
    if response.status_code == 200:
        soup = bs(response.text, 'lxml')
        rows = soup.find_all('tr')
        for row in rows:
            print(row)


if __name__ == "__main__":
    main()
                    