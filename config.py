# -*- coding: utf-8 -*-

feedie = {
    'bot_owner': ['meigrafd'],
    'cmd_prefix': '@',
    #'shorten_service': 'v.gd', #requires ssl
    'shorten_service': 'tinyurl.com',
}

network = {
    'server': 'irc.jen.de.euirc.net',
    'port': 6667,
    'password': '',
    'bot_nick': 'FEED',
    'bot_name': 'feedie pyBot v1.0',
    'pubmsg_log': False,
    'announce_delay': .5,
    'default_refresh_delay': 35.0,
    'startup_announces': False,
}

feeds = [{
    'mydealz': {
        'url': 'https://www.mydealz.de/rss/alle',
        'color': 'green',
        'channel': '#FEEDs',
        'channel_key': '',
        'enabled': True,
    },
    'monsterdealz': {
        'url': 'http://feeds.feedburner.com/MonsterDealz?format=xml',
        'color': 'green',
        'channel': '#FEEDs',
        'channel_key': '',
        'enabled': True,
    },
    'chillmo': {
        'url': 'http://chillmo.com/feed/',
        'color': 'orange',
        'channel': '#FEEDs',
        'channel_key': '',
        'enabled': True,
    },
    'hwluxx': {
        'url': 'http://www.hardwareluxx.de/index.php/rss/feed/3-hardwareluxx-rss-feed.html',
        'color': 'teal',
        'channel': '#FEEDs',
        'channel_key': '',
        'enabled': True,
    },
    'ht4u': {
        'url': 'http://ht4u.net/feeds/news.xml',
        'color': 'purple',
        'channel': '#FEEDs',
        'channel_key': '',
        'enabled': True,
    },
    'pcgames': {
        'url': 'http://www.pcgames.de/feed.cfm?menu_alias=home',
        'color': 'pink',
        'channel': '#FEEDs',
        'channel_key': '',
        'enabled': True,
    },
    'pcgames_hw': {
        'url': 'http://www.pcgameshardware.de/feed.cfm',
        'color': 'red',
        'channel': '#FEEDs',
        'channel_key': '',
        'enabled': True,
    },
    'forum': {
        'url': 'http://www.forum-raspberrypi.de/syndication2.php?limit=10',
        'color': 'red',
        'channel': '#Raspberry-Pi',
        'channel_key': '',
        'enabled': True,
        'refresh_delay': 15.0,
    },
}]


# EOF