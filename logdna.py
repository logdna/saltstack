# -*- coding: utf-8 -*-
'''
     LogDNA Engine -- sends information on salt events to LogDNA
'''
from __future__ import absolute_import
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
    def __init__(self, ingestion_key, max_bytes=_max_bytes):
        self.events = []
        self.key = ingestion_key
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

    def sendEvent(self, payload, timestamp=""):
        if not timestamp:
            timestamp = int(time.time())

        payload = json.loads(payload)

        if 'fun' not in payload:
            return

        if payload['fun'] == 'state.highstate' or payload['fun'] == 'state.apply' or payload['fun'] == 'state.sls':
            data = {"time": timestamp}
            data.update([("func", payload['fun'])])
            data.update([("payload", payload)])
            self.events.append(data)

            self.currentByteLength += sys.getsizeof(data)

            if self.timer == None:
                self.timer = Timer(10, self.flush)
                self.timer.start()

            if self.currentByteLength > self.maxByteLength:
                self.flush()



def start(ingestion_key=None):
    if ingestion_key == None:
        log.warning('Please specify your LogDNA Ingestion Key in your LogDNA engine config.')

    logdna_batcher = event_batcher(ingestion_key)

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
        event = event_bus.get_event()
        jevent = json.dumps(event)
        if event:
            logdna_batcher.sendEvent(jevent)
