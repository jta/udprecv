""" Test Configuration
"""
from nose.tools import raises, timed
import socket
import time
import unittest

import udprecv

class TestUdpRecv(unittest.TestCase):

    def setUp(self):
        self.args = []
        self.recv = udprecv.UdpRecv([1666, ])
        self.recv.start()

        self.teststr = 'test'.encode('UTF-8')
        self.testnum = '10'.encode('UTF-8')

    def tearDown(self):
        self.recv.stop()

    def sendto(self, msg, addr, family):
        """ Send packet and allow for some time for thread to process. """
        sock = socket.socket(family, socket.SOCK_DGRAM)
        sock.sendto(msg, addr)
        time.sleep(0.05)

    def register_cb(self, *args):
        """ Register function call arguments. """
        self.args.append(args)
        raise StopIteration

    def reraise(self, exc, data, addr, port):
        raise exc

    def test_recv_ipv4(self):
        """ Send and receive single packet over IPv4. """
        assert not self.args
        self.recv.add_callback(self.register_cb)
        self.sendto(self.teststr, ('127.0.0.1', 1666), socket.AF_INET)
        assert self.args == [('127.0.0.1', self.teststr)]

    def test_recv_ipv6(self):
        """ Send and receive single packet over IPv4. """
        assert not self.args
        self.recv.add_callback(self.register_cb)
        self.sendto(self.teststr, ('::1', 1666, 0, 0), socket.AF_INET6)
        assert self.args == [('::1', self.teststr)]

    def test_reader(self):
        self.recv.set_reader(int)
        self.recv.add_callback(self.register_cb)
        self.sendto(self.testnum, ('::1', 1666, 0, 0), socket.AF_INET6)
        assert self.args == [('::1', int(self.testnum))]

