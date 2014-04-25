'''
This program is licensed under the GPL v3.0, which is found at the URL below:
http://opensource.org/licenses/gpl-3.0.html

Copyright (c) 2013-2014 9Rivers.net. All rights reserved.
'''

import requests
from c9r.app import Command

class APIv1(Command):
    def_conf = '/opt/nss/etc/pi-conf.json'
    root_uri = '/webacs/api/v1/'

    def filtering(self, filters):
        '''Build and return a dictionary of filter variables.
        '''
        params = dict(filters) if filters else dict()
        if self.filters:
            params.update(self.filters)
        return params

    def get(self, uri, filters=None):
        '''Get requested resource at give /uri/ on the configured server.

        TODO:           Use the filters and .filters, .paging and .sorting.

        /uri/           URI to the resource/service on the server.
        /filters/       Extra filters as a dict, optional.         
        '''
        params = dict()
        if self.paging:
            params.update(self.next_page())
        if filters or self.filters:
            params.update(self.filtering(filters))
        conf = self.CONF
        url = conf.server+self.root_uri+uri+'.json'
        self.log_debug('URL=%s, params=%s'%(url, format(params)))
        return requests.get(url, auth=(conf.auth.user, conf.auth.pw),
                            params=params,
                            verify=conf.get('verify', True))

    def more_page(self):
        '''Returns True if there are more data to be paged thru.
        '''
        paging = self.paging
        return paging is None or paging['last']+1 < paging['count']

    def next_page(self):
        '''Build and return paging parameters for the API call.
        '''
        paging = self.paging
        if paging is None or paging['last']+1 >= paging['count']:
            return dict()
        return dict({
                '.firstResult': paging['last']+1,
                '.maxResults': paging['last']-paging['first']+1 })

    def parse(self, response):
        '''Parse a given /response/ and return the data. At the same time, setup
        paging parameters by recording the current page.
        '''
        if response.status_code != 200:
            return dict()
        data = response.json()['queryResponse']
        count = int(data.get('@count'))
        if not count is None:
            self.paging = dict(count=count,
                               first=int(data.get('@first')) or 0,
                               last=int(data.get('@last')) or count)
        return data

    def report(self, title, action='getReport'):
        '''Create or fetch report with given /title/.

        /title/   Report title of a report template saved in PI.
        /action/  Synchronous report creation: 'report';
                  Asynchronous report fetch: 'getReport', which returns the latest report found on server.
        '''
        return self.service("reportService", action, filters={ 'reportTitle': title })

    def resource(self, name, id=None, filters=None):
        '''Request data for a resource with given /name/ on the server.

        {.root_uri}/data/{RESOURCE-NAME}/{RESOURCE-ID}

        /id/            Optional resource entry id.
        /filter/        Optional extra filters for searching the resource.
        '''
        uri = name
        if id:
            uri += '/'+id
        return self.get('data/'+uri, filters)

    def service(self, domain, resource, filters=None):
        '''Request a service on the configured server.

        {.root_uri}/op/{service-domain}/{service-resource}

        /domain/        Name of the service domain.
        /resource/      Name of the resource.
        /filters/       Optional filters.
        '''
        return self.get('op/%s/%s'%(domain, resource), filters=filters)

    def __init__(self):
        '''Cisco Prime Infrastructure Python+JSON API.

        /paging/        Two optional integers: 'first' and 'last' results in response.
        /sorting/       Two optional lists of attribute names, for sorting results in
                        'asc'ending and 'desc'ending order.
        '''
        Command.__init__(self)
        self.sorting = None
        self.paging = None
        self.filters = None


if __name__ == '__main__':
    api = APIv1()
