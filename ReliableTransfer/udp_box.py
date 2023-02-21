"""
UDP_box is a black box network simulator for UDP.

It simulates network throttling, packet loss, and reordering over UDP.

Use it between you client/server UDP application to simulate possibly,
really bad, connections.

Due to the limitations of UDP, it is only possible to have one client talking
to one server. All received packets are forwarded to the last client
to connect to the UDP_bbox.

client <---> UDP_bbox <---> server

(c) 2019 Alan Marchiori

"""

import argparse
import socket
import logging
import json
import logging.config
from algs.udp_wrapper import UdpWrapper
import select
from datetime import datetime, timedelta
import random

def en_logging():
    "setup loggers"
    #https://docs.python.org/3/howto/logging-cookbook.html
    logging.config.dictConfig(json.load(open('log_cfg.json', 'r')))

def parse_args():
    "Sets up the argument parser"
    parser = argparse.ArgumentParser(
        description="Reliable Server (starter code)."
    )
    parser.add_argument('--mtu',
                        default = '65536', type=int,
                        help='MTU (buffer size).')
    parser.add_argument('--ber', default = 0.0,
                        type=float,
                        help='BYTE error rate, the probability of each byte being corrupted [0.0].')
    parser.add_argument('--ooo_rate', default = 0.0,
                        type=float,
                        help='Probability of delivering packets Out of Order [0.0].')
    parser.add_argument('--dupe_rate', default = 0.0,
                        type=float,
                        help='Probability of delivering duplicate packets [0.0].')
    parser.add_argument('--loss_rate',
                        default = '0.0', type=float,
                        help='Packet loss rate as a float [0-1].')
    parser.add_argument('--kbps',
                        default = '50',
                        help='Bandwidth in K BYTES per second [50].')
    parser.add_argument('--addr',
                        default = '0.0.0.0',
                        help='Local addres to listen on [0.0.0.0].')
    parser.add_argument('--port',
                        help='Local port to listen on [8880].',
                        default=8880,
                        type=int)
    parser.add_argument('--remote_addr',
                        default = '0.0.0.0',
                        help='Remote addres to send received packets to [localhost].')
    parser.add_argument('--remote_port',
                        help='Remote port to send packets to [8888].',
                        default=8888,
                        type=int)
    return parser.parse_args()

def corrupt(d, ber=0):
    "corrupt the packet d with BYTE error rate ber"
    if ber == 0:
        return d
    log = logging.getLogger()
    newd = []
    for k in d:
        if random.random() < ber:
            # simulate a one-bit error
            bitpos = random.randrange(0, 8)
            mask = 2**bitpos
            # 0->1 else 1->0
            newval = k & ~mask if k & mask else k ^ mask
            log.debug("Corrupt byte in packet {}->{}".format(
                      k, newval))
        else:
            newval = k
        newd.append(newval)
    return bytes(newd)

if __name__ == "__main__":
    en_logging()
    # turn down logging.
    logging.getLogger("algs.udp_wrapper").setLevel(logging.WARN)
    args = parse_args()
    assert(args.loss_rate < 1.0 and args.loss_rate >= 0)
    assert(args.ooo_rate < 1.0 and args.ooo_rate >= 0)
    assert(args.dupe_rate < 1.0 and args.dupe_rate >= 0)
    assert(args.ber < 1.0 and args.ber >= 0)
    log = logging.getLogger()

    log.info(args)
    input_sock = UdpWrapper((args.addr, args.port))
    output_sock = UdpWrapper((args.remote_addr, args.remote_port))

    input_sock.bind((args.addr, args.port))

    input_next_read = datetime.now()
    output_next_read = datetime.now()

    input_next_send = datetime.now()
    output_next_send = datetime.now()
    sec_per_byte = 1.0 / (1024*float(args.kbps))
    input_buffer = []
    output_buffer = []

    client_addr = 0

    while True:
        n = datetime.now()
        canselect = []
        if n >= input_next_read:
            canselect.append(input_sock)
        if n >= output_next_read:
            canselect.append(output_sock)

        if len(canselect) > 0:
            # only select on read, assume we can always write to the sockets
            r,w,e = select.select([input_sock, output_sock],
                                  [],
                                  [], 0.01)

            # read inputs
            for rs in r:
                data, addr = rs.recvfrom(args.mtu)

                # drop the packet?
                if random.random() < args.loss_rate:
                    log.info("Drop packet from {}".format(addr))
                    continue

                if rs == input_sock:
                    input_buffer.append( (rs, data, addr) )
                    client_addr = addr
                elif rs == output_sock:
                    output_buffer.append( (rs, data, addr) )

        n = datetime.now()

        if n > input_next_send and len(output_buffer) > 0:
            # FIFO or possibly create out of order packets.
            i = 0 if random.random() < 1.0-args.ooo_rate else random.choice(range(len(output_buffer)))
            s, d, a = output_buffer.pop(i)

            input_sock.sendto(corrupt(d, ber=args.ber), client_addr)
            #input_sock.sendto(corrupt(d, ber=args.ber), a) # fix amm042
            input_next_send = n + timedelta(seconds=len(d)*sec_per_byte)

            # re-add to cause dupes.
            if random.random() < args.dupe_rate:
                log.info("Dupe packet from {}".format(a))
                output_buffer.append((s,d,a))

        if n > output_next_send and len(input_buffer) > 0:
            i = 0 if random.random() < 1.0-args.ooo_rate else random.choice(range(len(input_buffer)))
            s, d, a = input_buffer.pop(i)

            output_sock.sendto(corrupt(d, ber=args.ber), (args.remote_addr, args.remote_port))
            output_next_send = n + timedelta(seconds=len(d)*sec_per_byte)

            # re-add to cause dupes.
            if random.random() < args.dupe_rate:
                log.info("Dupe packet from {}".format(a))
                input_buffer.append((s,d,a))

        evts = [input_next_read, output_next_read, input_next_send, output_next_send]
        # wait for the next event
        if n < min(evts):
            # nothing ready for a  while, sleep
            time.sleep(min(evts).total_seconds())
