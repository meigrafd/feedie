**feedie** is a simple easy-to-use iRC RSS FEED bot written in Python.

## Features

* Easy configuration
* No heavy database required
* SSL support
* Support for additional commands
* IRC Colors
* Supports TinyURL short urls

## Required:

```
apt-get install python-feedparser
wget http://sourceforge.net/projects/python-irclib/files/python-irclib/0.4.8/python-irclib-0.4.8.tar.gz
tar -zxvf python-irclib-0.4.8.tar.gz && rm python-irclib-0.4.8.tar.gz && cd python-irclib-0.4.8  
python setup.py install
```


For SSL Support we need at last Python 2.7.9
```
apt-get update
apt-get install build-essential checkinstall libbz2-dev libsqlite3-dev libreadline-dev zlib1g-dev libncurses5-dev libssl-dev libgdbm-dev
cd /usr/src
wget https://www.python.org/ftp/python/2.7.13/Python-2.7.13.tgz
tar xhf Python-2.7.13.tgz
cd Python-2.7.13
./configure
make
checkinstall
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