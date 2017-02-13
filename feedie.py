#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# IRC Bot to announce RSS FEED
#
#   Creator: meigrafd
#   Copyright (C) 2017 by meiraspi@gmail.com published under the Creative Commons License (BY-NC-SA)
#
# Based on:
# https://github.com/mrsmn/wookie
# https://github.com/jaraco/irc
#
# Required:
# apt-get install python-feedparser
# wget http://sourceforge.net/projects/python-irclib/files/python-irclib/0.4.8/python-irclib-0.4.8.tar.gz
# tar -zxvf python-irclib-0.4.8.tar.gz && rm python-irclib-0.4.8.tar.gz && cd python-irclib-0.4.8  
# python setup.py install
#
# Requires at last Python 2.7.9 for ssl support. How to install: http://unix.stackexchange.com/a/110163
#
# TODO:
# http://stackoverflow.com/a/36572948
#
#

from __future__ import print_function
from urllib import urlencode
from datetime import timedelta
from irclib import SimpleIRCClient
from urllib2 import (urlopen, URLError, HTTPError)
from config import (feedie, network, feeds)
from Queue import Queue
import re
import os
import sys
import time
import irclib
import random
import socket
import signal
import itertools
import threading
import feedparser
import sgmllib
import urllib2
import utils



def _termHandler(signalNumber, stackFrame):
    raise SystemExit, 'Signal #%s.' % signalNumber

signal.signal(signal.SIGTERM, _termHandler)


class feed_Proceed(threading.Thread):
    def __init__(self, bot, queue):
        threading.Thread.__init__(self)
        self.setDaemon(1)
        self.bot = bot
        self.queue = queue
    
    def run(self):
        while 1:
            feed, name = self.queue.get()
            self.bot.feed_refresh(feed, name)


class Queue_Manager(threading.Thread):
    def __init__(self, connection, delay=network['announce_delay']):
        threading.Thread.__init__(self)
        self.setDaemon(1)
        self.connection = connection
        self.delay = delay
        self.event = threading.Event()
        self.queue = []
    
    def run(self):
        while 1:
            self.event.wait()
            while self.queue:
                (msg, target) = self.queue.pop(0)
                try:
                    self.connection.privmsg(target, msg)
                except irclib.ServerNotConnectedError as error:
                    print(error)
                    
                time.sleep(self.delay)
            self.event.clear()
    
    def send(self, msg, target):
        self.queue.append((msg.strip(), target))
        self.event.set()


class ReconnectStrategy(object):
    min_interval = 60
    max_interval = 300
    
    def __init__(self, **attrs):
        vars(self).update(attrs)
        assert 0 <= self.min_interval <= self.max_interval
        self._check_scheduled = False
        self.attempt_count = itertools.count(1)

    def run(self, bot):
        self.bot = bot
        
        if self._check_scheduled:
            return
        
        # calculate interval in seconds based on connection attempts
        intvl = 2**next(self.attempt_count) - 1
        
        # limit the max interval
        intvl = min(intvl, self.max_interval)
        
        # add jitter and truncate to integer seconds
        intvl = int(intvl * random.random())
        
        # limit the min interval
        intvl = max(intvl, self.min_interval)
        
        threading.Timer(intvl, self.check).start()
        #self.bot.reactor.scheduler.execute_after(intvl, self.check)
        self._check_scheduled = True
    
    def check(self):
        self._check_scheduled = False
        if not self.bot.connection.is_connected():
            self.run(self.bot)
            self.bot.jump_server()


class _feedie(SimpleIRCClient):
    def __init__(self):
        irclib.SimpleIRCClient.__init__(self)
        self.start_time = time.time()
        self.queue = Queue_Manager(self.connection)
        self.feed_queue = Queue()
        self.feed_proceed_manager = feed_Proceed(self, self.feed_queue)
        self.reconnection_interval = 10
        self.channels = utils.IrcDict()
        self.recon = ReconnectStrategy(min_interval=self.reconnection_interval)
        
        self.urlShorter = utils.URLShortener(feedie['shorten_service'])
        
        self.lastRequest = {}
        self.cachedFeeds = {}
        
        self.BLACK = '\x0301'
        self.BLUE = '\x0302'
        self.RED = '\x0304'
        self.YELLOW = '\x0308'
        self.GREEN = '\x0303'
        self.PURPLE = '\x0306'
        self.PINK = '\x0313'
        self.ORANGE = '\x0307'
        self.TEAL = '\x0310'
        self.BOLD = '\x02'
        self.ITALIC = '\x1D'
        self.UNDERLINE = '\x1F'
        self.SWAP = '\x16'
        self.END = '\x0F'
    
    
    def on_welcome(self, serv, ev):
        if network['password']:
            serv.privmsg("nickserv", "IDENTIFY {}".format(network['password']))
            serv.privmsg("chanserv", "SET irc_auto_rejoin ON")
            serv.privmsg("chanserv", "SET irc_join_delay 0")
        
        for name in feeds[0]:
            if not feeds[0][name]['enabled']:
                continue
            try:
                serv.join(feeds[0][name]['channel'], key=feeds[0][name]['channel_key'])
            except:
                serv.join(feeds[0][name]['channel'])
        
        try:
            self.history_manager()
            time.sleep(2)
            self.queue.start()
            self.feed_proceed_manager.start()
            #self.feed_refresh()
            self.initFeedRefreshTimers()
        except (OSError, IOError) as error:
            serv.disconnect()
            print(error)
            sys.exit(1)
    
    
    def on_disconnect(self, serv, env):
        self.channels = utils.IrcDict()
        self.recon.run(self)
    
    
    def on_rss_entry(self, chan=None, text=''):
        if chan:
            self.queue.send(text, chan)
        else:
            for name in feeds[0]:
                self.queue.send(text, feeds[0][name]['channel'])
    
    
    def on_kick(self, serv, ev):
        serv.join(ev.target())
    
    
    def on_invite(self, serv, ev):
        serv.join(ev.arguments()[0])
    
    
    def on_ctcp(self, serv, ev):
        if ev.arguments()[0].upper() == 'VERSION':
            serv.ctcp_reply(ev.source().split('!')[0], network['bot_name'])
    
    
    def on_privmsg(self, serv, ev):
        author = irclib.nm_to_n(ev.source())
        message = ev.arguments()[0].strip()
        arguments = message.split(' ')
        if author in feedie['bot_owner']:
            if '.say' == arguments[0] and len(arguments) > 2:
                serv.privmsg(arguments[1], message.replace(arguments[0], '').replace(arguments[1], '')[2:])
            if '.act' == arguments[0] and len(arguments) > 2:
                serv.action(arguments[1], message.replace(arguments[0], '').replace(arguments[1], '')[2:])
            if '.join' == arguments[0] and len(arguments) > 2:
                serv.join(message[3:])
            if '.part' == arguments[0] and len(arguments) > 2:
                serv.part(message[3:])
    
    
    def on_pubmsg(self, serv, ev):
        author = irclib.nm_to_n(ev.source())
        message = ev.arguments()[0].strip()
        arguments = message.split(' ')
        chan = ev.target()
        if network['pubmsg_log']:
            event_time = time.strftime('[%H:%M:%S]', time.localtime())
            record = '{0} {1}: {2}'.format(event_time, author, message)
            with open(self.irc_entries, "a") as f:
                f.write("{}\n".format(record))
            print(record)
        if author in feedie['bot_owner']:
            try:
                if ev.arguments()[0].lower() == feedie['cmd_prefix']+'restart':
                    #self.restart_bot(serv, ev)
                    print("..missing feature..")
                if ev.arguments()[0].lower() == feedie['cmd_prefix']+'quit':
                    serv.disconnect()
                    sys.exit(1)
            except OSError as error:
                serv.disconnect()
                print(error)
                sys.exit(1)

        if feedie['cmd_prefix']+'help' == arguments[0].lower():
            serv.privmsg(
                chan, '{0}{2}{3}Available commands:{0}{1} {4}help || '
                      '{4}version || {4}uptime || {4}restart || {4}quit || {4}feeds'.format(
                            self.BOLD, self.END, self.UNDERLINE, self.BLUE, feedie['cmd_prefix']))

        if feedie['cmd_prefix']+'version' == arguments[0].lower():
            serv.privmsg(chan, '{0}{1}{2}{3}'.format(self.BOLD, self.BLUE, network['bot_name'], self.END))

        if feedie['cmd_prefix']+'uptime' == arguments[0].lower():
            uptime_raw = round(time.time() - self.start_time)
            uptime = timedelta(seconds=uptime_raw)
            serv.privmsg(chan, '{0}{3}[UPTIME]{4} {2}{1}'.format(self.BOLD, self.END, uptime, self.TEAL, self.BLACK))

        if feedie['cmd_prefix']+'feeds' == arguments[0].lower():
            for name in feeds[0]:
                if not feeds[0][name]['enabled']:
                    continue
                if not feeds[0][name]['channel'] == chan:
                    continue
                self.queue.send('{0}: {1}'.format(self.mircColor(name, feeds[0][name]['color']), feeds[0][name]['url']), chan)
    
    
    def history_manager(self):
        #home = '{}/.feedie_logs'.format(os.environ.get('HOME'))
        home = '/tmp'
        self.feedie_path = os.path.dirname(os.path.realpath(__file__))
        if network['pubmsg_log']:
            if os.path.exists(home) is False:
                os.system('mkdir {}'.format(home))
            self.irc_entries = '{}/irc-entries'.format(home)
            if os.path.exists(self.irc_entries) is False:
                os.system('touch {}'.format(self.irc_entries))
    
    
    def disconnect(self, msg="I'll be back!"):
        self.connection.disconnect(msg)
    
    
    def jump_server(self, msg="Changing servers"):
        """Connect to a new server, possibly disconnecting from the current."""
        if self.connection.is_connected():
            self.connection.disconnect(msg)
        self._connect()
    
    
    def bold(self, s):
        """Returns the string s, bolded."""
        return '\x02%s\x02' % s
    
    
    def reverse(self, s):
        """Returns the string s, reverse-videoed."""
        return '\x16%s\x16' % s
    
    
    def underline(self, s):
        """Returns the string s, underlined."""
        return '\x1F%s\x1F' % s
    
    def stripBold(self, s):
        """Returns the string s, with bold removed."""
        return s.replace('\x02', '')
    
    
    _stripColorRe = re.compile(r'\x03(?:\d{1,2},\d{1,2}|\d{1,2}|,\d{1,2}|)')
    def stripColor(self, s):
        """Returns the string s, with color removed."""
        return _stripColorRe.sub('', s)
    
    
    def stripReverse(self, s):
        """Returns the string s, with reverse-video removed."""
        return s.replace('\x16', '')
    
    
    def stripUnderline(self, s):
        """Returns the string s, with underlining removed."""
        return s.replace('\x1f', '').replace('\x1F', '')
    
    
    def stripFormatting(self, s):
        """Returns the string s, with all formatting removed."""
        # stripColor has to go first because of some strings, check the tests.
        s = stripColor(s)
        s = stripBold(s)
        s = stripReverse(s)
        s = stripUnderline(s)
        return s.replace('\x0f', '').replace('\x0F', '')
    
    
    def mircColor(self, s, fg=None, bg=None):
        """Returns s with the appropriate mIRC color codes applied."""
        if fg is None and bg is None:
            return s
        elif bg is None:
            fg = mircColors[str(fg)]
            return '\x03%s%s\x03' % (fg.zfill(2), s)
        elif fg is None:
            bg = mircColors[str(bg)]
            # According to the mirc color doc, a fg color MUST be specified if a
            # background color is specified.  So, we'll specify 00 (white) if the
            # user doesn't specify one.
            return '\x0300,%s%s\x03' % (bg.zfill(2), s)
        else:
            fg = mircColors[str(fg)]
            bg = mircColors[str(bg)]
            # No need to zfill fg because the comma delimits.
            return '\x03%s,%s%s\x03' % (fg, bg.zfill(2), s)
    
    
    def canonicalColor(self, s, bg=False, shift=0):
        """Assigns an (fg, bg) canonical color pair to a string based on its hash
        value.  This means it might change between Python versions.  This pair can
        be used as a *parameter to mircColor.  The shift parameter is how much to
        right-shift the hash value initially.
        """
        h = hash(s) >> shift
        fg = h % 14 + 2 # The + 2 is to rule out black and white.
        if bg:
            bg = (h >> 4) & 3 # The 5th, 6th, and 7th least significant bits.
            if fg < 8:
                bg += 8
            else:
                bg += 2
            return (fg, bg)
        else:
            return (fg, None)
    
    
    def _getConverter(self, feed):
        toText = utils.htmlToText
        if 'encoding' in feed:
            return lambda s: toText(s).strip().encode(feed['encoding'], 'replace')
        else:
            return lambda s: toText(s).strip()
    
    
    def getHeadlines(self, feed):
        headlines = []
        conv = self._getConverter(feed)
        for d in feed['items']:
            if 'title' in d:
                title = conv(d['title'])
                link = d.get('link')
                if link:
                    headlines.append((title, link))
                else:
                    headlines.append((title, None))
        return headlines
    
    
    def getFeed(self, url):
        def error(s):
            return {'items': [{'title': s}]}
        try:
            #print('Downloading new feed from %u' % url)
            results = feedparser.parse(url)
            if 'bozo_exception' in results:
                raise results['bozo_exception']
        except sgmllib.SGMLParseError:
            return error('Invalid (unparsable) RSS feed.')
        except socket.timeout:
            return error('Timeout downloading feed.')
        except Exception, e:
            # These seem mostly harmless.  We'll need reports of a kind that isn't.
            print('Allowing bozo_exception "%r" through.' % e)
        if results.get('feed', {}):
            self.cachedFeeds[url] = results
            self.lastRequest[url] = time.time()
        else:
            print('Not caching results; feed is empty.')
        try:
            return self.cachedFeeds[url]
        except KeyError:
            # If there's a problem retrieving the feed, we should back off
            # for a little bit before retrying so that there is time for
            # the error to be resolved.
            self.lastRequest[url] = time.time() - .5 * 180
            return error('Unable to download feed.')
    
    
    def feed_refresh__old(self):
        for name in feeds[0]:
            if not feeds[0][name]['enabled']:
                continue
            
            url = feeds[0][name]['url']
            try:
                oldresults = self.cachedFeeds[url]
                oldheadlines = self.getHeadlines(oldresults)
            except KeyError:
                oldheadlines = []
            
            if not network['startup_announces'] and not oldheadlines:
                newresults = self.getFeed(url)
                continue
            else:
                newresults = self.getFeed(url)
                newheadlines = self.getHeadlines(newresults)
            
            if len(newheadlines) == 1:
                s = newheadlines[0][0]
                if s in ('Timeout downloading feed.', 'Unable to download feed.'):
                    print('%s %u', s, url)
                    return
            
            def canonize(headline):
                return (tuple(headline[0].lower().split()), headline[1])
            
            oldheadlines = set(map(canonize, oldheadlines))
            
            for (i, headline) in enumerate(newheadlines):
                if canonize(headline) in oldheadlines:
                    newheadlines[i] = None
            newheadlines = filter(None, newheadlines) # Removes Nones.
            
            if newheadlines:
                for headline in newheadlines:
                    if headline[1]:
                        title = headline[0]
                        short_url = self.urlShorter.shorten_url(headline[1])
                        if not short_url or short_url == 'Error': short_url = url
                        feedName = self.mircColor(name, feeds[0][name]['color'])
                        feedTitle = self.mircColor(title, 'blue')
                        try:
                            chan = feeds[0][name]['channel']
                        except KeyError:
                            # send to all channels
                            chan = None
                        self.on_rss_entry(chan=chan, text='{0} {1} {2}'.format(feedName, feedTitle, self.underline(short_url)))
        threading.Timer(network['feeds_refresh_delay'], self.feed_refresh).start()
    
    
    def initFeedRefreshTimers(self):
        for feed in feeds:
            for name in feed:
                if not feed[name]['enabled']:
                    continue
                try:
                    refresh_time = feed[name]['refresh_delay']
                except KeyError:
                    refresh_time = network['default_refresh_delay']
                threading.Timer(refresh_time, self.timedFeedRefresh, (feed,name,refresh_time,)).start()
    
    
    def timedFeedRefresh(self, feed, name, refresh_time):
        self.feed_queue.put( (feed, name) )
        threading.Timer(refresh_time, self.timedFeedRefresh, (feed,name,refresh_time,)).start()
    
    
    def feed_refresh(self, feed, name):
        url = feed[name]['url']
        try:
            oldresults = self.cachedFeeds[url]
            oldheadlines = self.getHeadlines(oldresults)
        except KeyError:
            oldheadlines = []
        
        if not network['startup_announces'] and not oldheadlines:
            newresults = self.getFeed(url)
            return
        else:
            newresults = self.getFeed(url)
            newheadlines = self.getHeadlines(newresults)
        
        if len(newheadlines) == 1:
            s = newheadlines[0][0]
            if s in ('Timeout downloading feed.', 'Unable to download feed.'):
                print('%s %u', s, url)
                return
        
        def canonize(headline):
            return (tuple(headline[0].lower().split()), headline[1])
        
        oldheadlines = set(map(canonize, oldheadlines))
        
        for (i, headline) in enumerate(newheadlines):
            if canonize(headline) in oldheadlines:
                newheadlines[i] = None
        newheadlines = filter(None, newheadlines) # Removes Nones.
        
        if newheadlines:
            for headline in newheadlines:
                if headline[1]:
                    title = headline[0]
                    short_url = self.urlShorter.shorten_url(headline[1])
                    if not short_url or short_url == 'Error': short_url = url
                    feedName = self.mircColor(name, feed[name]['color'])
                    feedTitle = self.mircColor(title, 'blue')
                    try:
                        chan = feed[name]['channel']
                    except KeyError:
                        # send to all channels
                        chan = None
                    self.on_rss_entry(chan=chan, text='{0} {1} {2}'.format(feedName, feedTitle, self.underline(short_url)))


mircColors = utils.IrcDict({
    'white': '0',
    'black': '1',
    'blue': '2',
    'green': '3',
    'red': '4',
    'brown': '5',
    'purple': '6',
    'orange': '7',
    'yellow': '8',
    'light green': '9',
    'teal': '10',
    'light blue': '11',
    'dark blue': '12',
    'pink': '13',
    'dark grey': '14',
    'light grey': '15',
    'dark gray': '14',
    'light gray': '15',
})

# We'll map integers to their string form so mircColor() is simpler.
for (k, v) in mircColors.items():
    if k is not None: # Ignore empty string for None.
        sv = str(v)
        mircColors[sv] = sv


def main():
    try:
        bot = _feedie()
        bot.connect(network['server'], network['port'], network['bot_nick'], network['bot_name'], ssl=network['SSL'], ipv6=network['ipv6'])
        bot.start()

    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    except OSError, error:
        print(error)
        sys.exit(1)
    except irclib.ServerConnectionError, error:
        print(error)
        sys.exit(1)


if __name__ == "__main__":
    main()


#EOF