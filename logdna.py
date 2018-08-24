# -*- coding: utf-8 -*-
'''
     LogDNA Engine -- sends information on salt events to LogDNA
'''
from __future__ import absolute_import
from fnmatch import fnmatch
from threading import Timer

import sys
import json
import time
import logging
import requests
import salt.utils.event

log = logging.getLogger(__name__)
_max_bytes = 10000

class event_batcher(object):

    def __init__(self, ingestion_key, extra_events=[], max_bytes=_max_bytes):

        self.events = []
        self.key = ingestion_key
        self.extra_events = extra_events
        self.timer = None
        self.currentByteLength = 0
        self.maxByteLength = max_bytes
        self.headers = {'content-type': 'application/json'}
        self.logdna_endpoint = 'https://logs.logdna.com/webhooks/salt'

    def flush(self):

        if self.timer:
            self.timer.cancel()
            self.timer = None

        r = requests.post(self.logdna_endpoint, data=json.dumps(self.events), auth=('logdna', self.key), headers=self.headers)
        self.events = []
        self.currentByteLength = 0

    def sendEvent(self, event, timestamp=''):
        if not timestamp:
            timestamp = int(time.time())

        tag = event.pop('tag')
        payload = event.pop('data')

        func = payload.get('fun')
        if func in ['state.highstate', 'state.apply', 'state.sls']:
            data = {'time': timestamp}
            data.update({'func': payload['fun']})
            data.update({'payload': payload})
            self.events.append(data)

            self.currentByteLength += sys.getsizeof(data)
        else:
            for event_str in self.extra_events:
                if fnmatch(tag, event_str):
                    log.debug('forwarding extra event %s to ingestor', tag)

                    data = {'time': timestamp}
                    data.update({'event': tag})
                    data.update({'payload': payload})
                    self.events.append(data)

                    self.currentByteLength += sys.getsizeof(data)
                else:
                    continue

        if self.timer is None:
            self.timer = Timer(10, self.flush)
            self.timer.start()

        if self.currentByteLength > self.maxByteLength:
            self.flush()


def start(ingestion_key=None, extra_events=[]):
    if ingestion_key is None:
        log.warning('Please specify your LogDNA Ingestion Key in your LogDNA engine config.')

    logdna_batcher = event_batcher(ingestion_key, extra_events=extra_events)

    if __opts__['__role'] == 'master':
        event_bus = salt.utils.event.get_master_event(
                __opts__,
                __opts__['sock_dir'],
                listen=True)
    else:
        event_bus = salt.utils.event.get_event(
            'minion',
            transport=__opts__['transport'],
            opts=__opts__,
            sock_dir=__opts__['sock_dir'],
            listen=True)
        log.debug('LogDNA engine started')

    while True:
        event = event_bus.get_event(full=True)
        if event:
            logdna_batcher.sendEvent(event)
