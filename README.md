# Proxy Grabber & Checker

### Features
- Save working proxies to txt file
- Upload working proxies to mongodb for more functionality
- Run script in Loop/Once and upload every new scan to mongodb/ save to txt file
- Multithreading functionality (default threads is 50)
- Scanning all proxy Types  http/https/socks4/5

### Installation & Requirements
`pip install  -r requirements.txt`

`for windows install curl to work currectly`

`edit connection_string in script from "NONE" to your mongodb connection string`

### How To Run?
    script settings:
    
    -s = save to txt file use y/n to use the feature
    -u =upload to mongodb  y/n to use the feature
    -t = threads default is 50
    -l = run script in loop  y/n to use the feature
    -c= cooldown default is 5 minutes
	
	running example:
	python3 checker.py -t=75 -l=n -u=y -s=n -c=0


### Grabbing Sources
- [proxyscrape.com](http://proxyscrape.com "proxyscrape.com")
- [c99.nl](http://c99.nl "c99.nl")
- [free-proxy-list.net](https://free-proxy-list.net/anonymous-proxy.html "free-proxy-list.net")
- [proxy-daily.com](http://www.proxy-daily.com "proxy-daily.com") 
- [socks-proxy.net](https://www.socks-proxy.net "socks-proxy.net")
- [sslproxies.org](https://www.sslproxies.org "sslproxies.org")
- [us-proxy.org](https://www.us-proxy.org "us-proxy.org")
