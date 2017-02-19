**feedie** is a simple easy-to-use iRC RSS FEED bot written in Python.

## Features

* Easy configuration
* No heavy database required
* Support for additional commands
* IRC Colors
* Supports short urls


## Required:
```
apt-get install python3-pip libffi-dev
pip3 install pyopenssl feedparser irc requests sgmllib3k
```

## Installation:
```
$ cd /home/<username>  
$ git clone https://github.com/meigrafd/feedie.git
$ cd feedie
```

Edit the config.py file to suit your needs, then:

```
$ bash start.sh
```