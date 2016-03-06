#!/usr/bin/env python
import sys
import time
import urllib, json
import riemann_client.client
from riemann_client.transport import TCPTransport

riemann_port = '5555'
locust_stats_url = 'http://localhost:8089/stats/requests'
sleep_t = 5

th_min = 5000.0
th_max = 7000.0

resource = '/load'
m_name = 'avg_response_time'
host_name = 'httpclient'
tags = ['webapp']


def m_to_state(m):
    if m <= th_min:
        return 'ok'
    elif th_min < m <= th_max:
        return 'warning'
    else:
        return 'critical'


def get_stats(url):
    response = urllib.urlopen(url)
    return json.loads(response.read())


def publish(stats, client):
    for s in stats['stats']:
        if resource == s.get('name', ''):
            m = s.get(m_name)
            event = {'host': host_name,
                     'service': m_name,
                     'metric_f': m,
                     'tags': tags,
                     'state': m_to_state(m),
                     'time': int(time.time()),
                     'ttl': 2 * sleep_t}
            print event
            client.event(**event)


def publish_to_riemann(ip, port=riemann_port, locust=locust_stats_url):
    t = TCPTransport(ip, port)
    t.connect()
    try:
        with riemann_client.client.Client(t) as client:
            while True:
                stats = get_stats(locust)
                publish(stats, client)
                time.sleep(sleep_t)
    finally:
        t.disconnect()

def main():
    nargs = len(sys.argv)
    if nargs < 2:
        print "usage: riemann_ip[:port] [locust stats url]"
        raise SystemExit(1)
    ip_port = sys.argv[1].split(':')
    ip = ip_port[0]
    port = len(ip_port) == 2 and ip_port[1] or riemann_port
    locust = nargs > 2 and sys.argv[2] or locust_stats_url
    publish_to_riemann(ip, port, locust)


if __name__ == '__main__':
   main()
