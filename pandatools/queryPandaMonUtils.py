import time
import datetime
import json
import sys

try:
    from urllib.parmase import urlencode
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError


HEADERS = {'Accept': 'application/json', 'Content-Type':'application/json'}


def query_tasks(jeditaskid=None, username=None, limit=10000, taskname=None, status=None, superstatus=None,
                days=None, metadata=False, sync=False, verbose=False):
    timestamp = int(time.time())
    parmas = {  'json': 1,
                'datasets': True,
                'limit':limit,
                }
    if jeditaskid:
        parmas['jeditaskid'] = jeditaskid
    if username:
        parmas['username'] = username
    if taskname:
        parmas['taskname'] = taskname
    if status:
        parmas['status'] = status
    if superstatus:
        parmas['superstatus'] = superstatus
    if days is not None:
        parmas['days'] = days
    if metadata:
        parmas['extra'] = 'metastruct'
    if sync:
        parmas['timestamp'] = timestamp
    url = 'https://bigpanda.cern.ch/tasks/?{0}'.format(urlencode(parmas))
    if verbose:
        sys.stderr.write('query url = {0}\n'.format(url))
        sys.stderr.write('headers   = {0}\n'.format(json.dumps(HEADERS)))
    try:
        req = Request(url, headers=HEADERS)
        # res = urlopen(req).read().decode('utf-8')
        rep =  urlopen(req)
        if verbose:
            sys.stderr.write('time UTC  = {0}\n'.format(datetime.datetime.utcnow()))
        rec = rep.getcode()
        if verbose:
            sys.stderr.write('resp code = {0}\n'.format(rec))
        res = rep.read().decode('utf-8')
        ret = json.loads(res)
        return timestamp, url, ret
    except Exception as e:
        err_str = '{0} : {1}'.format(e.__class__.__name__, e)
        sys.stderr.write('{0}\n'.format(err_str))
        raise
