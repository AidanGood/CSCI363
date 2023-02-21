import socket
import logging
#from binascii import hexlify
log = logging.getLogger(__name__)
class UdpWrapper:
    "A wrapper to a UDP socket that adds logging."
    def __init__(self, dest):
        self.name = 'UDPWrap{}'.format(dest)
        self.dest = dest
        log.debug("{} created.".format(self.name))
        self.socket = socket.socket(family=socket.AF_INET,
                                    type=socket.SOCK_DGRAM)
    def fileno(self):
        return self.socket.fileno()
    def sendto(self, payload, dest):
        log.debug("->{}: {}".format(dest, payload))
        self.socket.sendto(payload, dest)
    def recvfrom(self, mtu):
        data,addr = self.socket.recvfrom(mtu)
        log.debug("<-{}: {}".format(addr, data))
        return data,addr
    def bind(self, addr):
        return self.socket.bind(addr)
    def setblocking(self, flag):
        return self.socket.setblocking(flag)
    def settimeout(self, value):
        return self.socket.settimeout(value)
