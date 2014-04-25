#!/usr/bin/env python
'''
This program is licensed under the GPL v3.0, which is found at the URL below:
http://opensource.org/licenses/gpl-3.0.html

Copyright (c) 2013-2014 9Rivers.net. All rights reserved.
'''

import json
import xml.etree.ElementTree as xmlet
from cisco.pi import APIv1 as PIAPI

class Devices(PIAPI):
    def parse(self, response):
        '''Parse given response and return a list of devices, in the
        'entity' data object in response, which corresponds to the
        '.full' request.
        '''
        devs = list()
        for dev in PIAPI.parse(self, response)['entity']:
            dto = dev['devicesDTO']
            xtime = dto.get('collectionTime')
            if xtime is None: continue
            # Parse 'collectionDetail' which comes in XML:
            if 'collectionDetail' in dto:
                detail = dto['collectionDetail']
                try:
                    doc = xmlet.fromstring(detail)
                    status = dict()
                    for xml in doc:
                        status[xml.tag] = xml.attrib if xml.text is None else xml.text
                    detail = dict({doc.tag: status})
                except xmlet.ParseError:
                    pass
                dto['collectionDetail'] = detail
            devs.append(dto)
        return devs

    def __call__(self):
        '''Return the devices table, with '.full' descriptions.
        '''
        devs = self.devices
        if len(devs) == 0:
            while self.more_page():
                r = self.resource('Devices', filters={'.full': 'true'})
                if r.status_code == 200:
                    devs += self.parse(r)
            self.devices = devs
        return devs

    def __init__(self):
        self.devices = list()
        PIAPI.__init__(self)


if __name__ == '__main__':
    devices = Devices()()
    print(json.dumps(devices, indent=4))
