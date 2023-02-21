"""
Reliable Sender
The goal is to create a reliable transport protocol. This file is the side
that initiates a transfer (client). The rrecv.py file has the server codeself.
Data is transmitted over UDP. A separate udproxy server can enforce data rate
limits and/or packet loss or corruption.
(c) Alan Marchiori 2019
"""

import argparse
import socket
import logging
import logging.config
import sys
import json
import algs
from algs.texcept import TransferFailed

# custom exception
class AlgorithmNotImplementedError(NotImplementedError): pass

def en_logging():
    "setup loggers"
    #https://docs.python.org/3/howto/logging-cookbook.html
    logging.config.dictConfig(json.load(open('log_cfg.json', 'r')))

def parse_args():
    "Sets up the argument parser"
    parser = argparse.ArgumentParser(
        description="Reliable Sender (starter code)."
    )
    parser.add_argument('files',
                        default='alice.txt', nargs="+",
                        help="File(s) to send [alice.txt].")
    parser.add_argument('--mtu',
                        default=100,
                        type=int,
                        help='Maximum transmition unit (MTU) (bytes) [100].')
    parser.add_argument('--dst',
                        default = 'localhost',
                        help='Destination host, eg. hostname or 192.168.3.101 [localhost].')
    parser.add_argument('--port',
                        help='Port on destination host [8888].',
                        default=8888,
                        type=int)

    # add additional algorithms here.
    parser.add_argument('--alg',
                        help='The algorithm to use [sw].',
                        default='tc',
                        choices=['sw', 'tc', 'yours'])
    return parser.parse_args()

if __name__ == "__main__":
    en_logging()
    # uncomment this to see every packet.
    #logging.getLogger("algs.udp_wrapper").setLevel(logging.DEBUG)
    args = parse_args()

    # look at those args
    logging.debug("Got args {}".format(args))

    if args.alg == 'sw': # stop and wait protocol
        # map files list into multiple calls
        try:
            result = list(map(lambda x: algs.sw.send_file(
                    filename=x,
                    dest=(args.dst, args.port),
                    mtu=args.mtu),
                args.files))
        except TransferFailed as x:
            logging.error("Transfer failed: {}".format(x))
            raise(x)
            sys.exit(-5)
    if args.alg == 'tc': # Custom
        # map files list into multiple calls
        try:
            result = list(map(lambda x: algs.tc.send_file(
                    filename=x,
                    dest=(args.dst, args.port),
                    mtu=args.mtu),
                args.files))
        except TransferFailed as x:
            logging.error("Transfer failed: {}".format(x))
            raise(x)
            sys.exit(-5)

    else:
        raise AlgorithmNotImplementedError()
