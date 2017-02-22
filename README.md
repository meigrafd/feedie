**feedie** is a simple easy-to-use iRC RSS FEED bot written in Python.

## Features

* Easy configuration
* Supports multiple Feeds and Channels
* Supports short urls
* IRC Colors


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