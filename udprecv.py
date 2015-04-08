# -*- coding: utf-8 -*-
""" Provides a thread class to process UDP packets. """
from __future__ import print_function

__author__ = 'João Taveira Araújo'
__version__ = '0.0.8'
__license__ = 'MIT'

from collections import defaultdict
from binascii import hexlify
import IN
try:
    from itertools import filterfalse
except ImportError:
    # Python 2
    from itertools import ifilterfalse as filterfalse
import logging
import select
import socket
import struct
import threading

log = logging.getLogger(__name__) # pylint: disable=invalid-name

class UdpRecvError(Exception):
    """ Raised on internal errors. """
    pass

class UdpRecv(threading.Thread):
    """ A helper class to read UDP packets from provided list of ports.
        Deals with v6 natively, and treats legacy v4 case by mapping to
        and from appropriate v6 address range.
    """
    def __init__(self, ports, localaddr='::', bufsize=1500, maxcount=None, intfs=None):
        """
        :param ports: list of ports to listen on
        :param localaddr: IP address to bind to
        :param bufsize: max buffer size when reading from socket
        :param maxcount: total number of packets to process before stopping
        """
        self.addr = self._map_v6(localaddr)
        self.sockets = []
        self.sockpair = {}
        self.pairsock = {}

        self.bufsize = bufsize
        self.callbacks = defaultdict(list)
        self.maxcount = maxcount
        self._count = 0
        self.excs = ()
        self.errhandler = None
        self.reader = None
        self.stopped = False

        threading.Thread.__init__(self)
        self.daemon = True

    def add_socket(self, *args):
        if args in self.pairsock:
            return False

        sock = self.get_socket(self.addr, *args)
        self.sockets.append(sock)
        self.sockpair[sock] = args
        self.pairsock[args] = sock
        self.sockets = list(self.sockpair.keys())
        return True

    def del_socket(self, *args):
        if args not in self.pairsock:
            return False

        sock = self.get_socket(self.addr, *args)
        sock = self.pairsock.pop(args)
        del self.sockpair[sock]
        sock.close()
        self.sockets = list(self.sockpair.keys())
        return True

    @property
    def count(self):
        """ Number of messages seen so far. """
        return self._count

    @count.setter
    def count(self, value):
        """ Used to increment count. If count exceeds maxcount, stop loop. """
        self._count += value
        if self.maxcount and self._count >= self.maxcount:
            raise StopIteration

    @classmethod
    def _map_v6(cls, addr):
        """ Map IP address to IPv6.
        :param addr: string representation of IPv4 or IPv6 address
        :param returns: string representation of IPv6 address.
        """
        try:
            ipnum = int(hexlify(socket.inet_aton(addr)), 16)
            ipbin = struct.pack("!QQ", 0, ipnum + (0xFFFF << 32))
            return socket.inet_ntop(socket.AF_INET6, ipbin)
        except socket.error:
            pass

        try:
            _ = socket.inet_pton(socket.AF_INET6, addr)
            return addr
        except socket.error as err:
            raise UdpRecvError(err)

    @classmethod
    def _unmap_v6(cls, addr):
        """ Convert v6 address to native representation (v4 or v6).
        :param addr: string representation of IPv6 address
        :returns: string representation of IPv4 or IPv6 address
        """
        ipnum = int(hexlify(socket.inet_pton(socket.AF_INET6, addr)), 16)
        if (ipnum >> 32) == 0xFFFF:
            addr = socket.inet_ntoa(struct.pack("!I", ipnum & 0xFFFFFFFF))
        return addr

    @classmethod
    def get_socket(cls, localaddr, port, intf, reuse=True):
        """ Open socket and bind to port.
        :param localaddr: string representation of IPv6 address
        :param port: port to bind socket to
        :param intf: interface to bind on
        :param reuse: boolean as to whether to allow socket reuse.
        """
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        if reuse:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((localaddr, port))
            sock.setblocking(0)
            if intf:
                sock.setsockopt(socket.SOL_SOCKET, IN.SO_BINDTODEVICE, intf)
        except socket.error as err:
            sock.close()
            raise UdpRecvError(err)
        return sock

    def add_callback(self, func, filt=None):
        """ Add function and filter function to list of callbacks. """
        self.callbacks[func].append(filt)

    def set_error_handler(self, excs, handler):
        """ Add list of exceptions to catch and function to call.
        :param excs: tuple of exceptions to handle
        :param handler: function to call when handling listed exceptions

        Handler function has signature: (exc, data, addr, port)
        """
        self.excs = excs
        self.errhandler = handler

    def set_reader(self, func, encoding='utf-8'):
        """ Provide a function to parse raw packet data.
            :param func: function which parses raw packet data as string
            :param encoding: encoding to use when decoding packet data to string
        """
        self.reader = lambda x: func(x.decode(encoding))

    def read(self, sock):
        """ Process data from socket.
        :param sock: socket to read data from
        """
        data, (addr, port, _, _) = sock.recvfrom(self.bufsize)
        addr = self._unmap_v6(addr)
        try:
            message = self.reader(data) if self.reader else data
            source = [addr, port] + list(self.sockpair[sock])
            for func, filts in self.callbacks.items():
                if any(f is None or f(message) for f in filts):
                    func(source, message)
        except self.excs as exc:
            if self.errhandler:
                self.errhandler(exc, data, addr, port)
            else:
                raise

    def run(self):
        """ Read packets from socket list. """
        while not self.stopped:
            try:
                ready, _, _ = select.select(self.sockets, [], [], 0.1)
                for sock in ready:
                    self.read(sock)
                    self.count += 1
            except select.error:
                if self.sockets and not self.stopped:
                    raise
            except StopIteration:
                self.stop()

    def stop(self):
        """ Close list of sockets, halting run loop. """
        while self.sockets:
            self.sockets.pop().close()
        self.stopped = True

