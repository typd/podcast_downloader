#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import sys 
import logging
import json
import time
from datetime import datetime 
import xml.dom.minidom
from dateutil.parser import parse

import argparse
import ConfigParser
from requests import get

reload(sys) 
sys.setdefaultencoding('utf-8') 
DEFAULT_PATH = "log/{0}.log".format(datetime.utcnow().strftime('%Y-%m-%d'))  

def ensure_dir(path):
    if os.path.exists(path):
        return
    directory = os.path.dirname(path)
    if not os.path.exists(directory):   
        os.makedirs(directory)

def is_dir_path(path):
    if not path:
        return False
    return path.endswith(os.path.sep)

def ensure_path(path):     
    if os.path.exists(path):
        return             
    ensure_dir(path)       
    if not is_dir_path(path):
        open(path, 'a').close()

def create_default_logger(path=DEFAULT_PATH):
    logger = logging.getLogger("")
    logger.setLevel(logging.DEBUG)
    logging.Formatter.converter = time.gmtime
    ensure_path(path)
    formatter = logging.Formatter("%(asctime)s %(message)s", '[%m-%d %H:%M:%S]')
    fhandler = logging.FileHandler(path)
    fhandler.setFormatter(formatter)
    logger.addHandler(fhandler)
    chandler = logging.StreamHandler()
    chandler.setFormatter(formatter)  
    logger.addHandler(chandler)
    return logger

def save(data, path):      
    ensure_dir(path)       
    flag = 'w'             
    if bytes == type(data):
        flag = 'wb'        
    with open(path, flag) as savedfile:
        savedfile.write(data)

def get_size(path):
    if os.path.isdir(path):
        total = 0
        for _file in os.listdir(path):
            total += get_size(os.path.join(path, _file))
        return total
    else:
        return os.path.getsize(path)

def purge_filename(name):
    assert name != None
    return name.replace('/', ' ').replace(':', ' ')

def get_size_str(path):
    size = get_size(path)
    return get_size_str_from_size(size)

def get_size_str_from_size(size):
    if size > 1000000000:
        return "%.2fG" % (float(size) / 1000000000)
    elif size > 1000000:
        return "%.2fM" % (float(size) / 1000000)
    elif size > 1000:
        return "%.2fK" % (float(size) / 1000)
    else:
        return "%dB" % size

DATA_DIR = 'data'
logger = create_default_logger() 

def safe_execute(func, *args, **kargs):
    try:
        return func(*args, **kargs), True
    except:
        return None, False 

def get_text(node):
    nodelist = node.childNodes
    datalist = \
        [node.data for node in nodelist if node.nodeType == node.TEXT_NODE]
    return ''.join(datalist)

def get_subscribed_channels():
    config = ConfigParser.ConfigParser() 
    config.read("subscription.config")
    return config.items("channel")

def purge_url(url):
    return url.replace('%20', ' ')

def conv_date(date):
    #Wed, 13 Feb 2013 15:24:46 +0000
    #1 Jan 2012 16:04:30 GMT
    conv = parse(date)
    return conv.strftime("%Y-%m-%d_%H%M%S")

def update():
    logger.info("update subscriptions")
    channels = get_subscribed_channels()
    for channel in channels:
        jsobj = json.loads(channel[1])
        name = jsobj['name']
        last_n = jsobj['count']
        url = jsobj['url']
        logger.info(name + ' @ ' + url)
        directory = os.path.join(DATA_DIR, name)
        if not os.path.exists(directory):
            logger.info('  creating dir: {}'.format(directory))
            os.mkdir(directory)
        logger.info('  downloading rss ' + url)
        resp, _ = safe_execute(get, url)
        if not resp or not resp.ok:
            logger.info('  fail to download rss %s', url)
            continue
        doc = xml.dom.minidom.parseString(resp.text)
        count = 0
        downloaded = 0
        items = doc.getElementsByTagName('item')
        for item in items:
            mns = item.getElementsByTagName('enclosure')
            if len(mns) <= 0:
                continue
            url = item.getElementsByTagName('enclosure')[0].getAttribute('url')
            date = conv_date(get_text(item.getElementsByTagName('pubDate')[0]))
            title = purge_filename(
                    get_text(item.getElementsByTagName('title')[0]))
            filename = date + '-' + title + '.mp3'
            path = os.path.join(directory, filename)
            if not os.path.exists(path):
                logger.info('  downloading %s', filename[:50])
                resp, _ = safe_execute(get, url)
                if resp and resp.ok:
                    save(resp.content, path)
                    downloaded += 1
                    logger.info('    size: %s', get_size_str(path))
                else:
                    logger.info('  error while downloading %s', url)
            else:
                logger.info('  skip        %s', filename[:50])
            count += 1
            if count >= last_n:
                break
        logger.info('  downloaded %d, checked %d , rss has %d items', \
                downloaded, count, len(items))

def main():
    logger.info("Start===============")
    parser = argparse.ArgumentParser()
    parser.add_argument('cmd', nargs='+')
    parser.add_argument('-d', nargs='?', const=True, default=False)
    args = parser.parse_args()
    logger.info(args)
    if args.cmd[0] == 'update':
        update()
    logger.info("End=================")
    logger.info("")


if __name__ == '__main__':
    main()
