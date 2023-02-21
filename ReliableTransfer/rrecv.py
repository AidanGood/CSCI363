"""
Reliable Receiver
The goal is to create a reliable transport protocol. This file is the side
that waits for a client to transfer files (server).
Data is transmitted over UDP. A separate udp_box can enforce data rate
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
        description="Reliable Server (starter code)."
    )
    parser.add_argument('--outdir',
                        default='./tmp',
                        help="Directory to store recieved files [./tmp].")
    parser.add_argument('--mtu',
                        default=100,
                        type=int,
                        help='Maximum transmition unit (MTU) (bytes) [100].')
    parser.add_argument('--addr',
                        default = '0.0.0.0',
                        help='Local addres to listen on [0.0.0.0].')
    parser.add_argument('--port',
                        help='Port to listen on [8888].',
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
    args = parse_args()

    # look at those args
    logging.debug("Got args {}".format(args))

    if args.alg == 'sw': # stop and wait protocol
        # the server should never stop...
        try:
            algs.sw.run_server(
                    outdir=args.outdir,
                    addr=(args.addr, args.port),
                    mtu=args.mtu)
        except Exception as x:
            logging.error("Server died: {}".format(x))
            raise(x)
            sys.exit(-15)
    # add additional algorithms here.
    if args.alg == 'tc': # stop and wait protocol
        # the server should never stop...
        try:
            algs.tc.run_server(
                    outdir=args.outdir,
                    addr=(args.addr, args.port),
                    mtu=args.mtu)
        except Exception as x:
            logging.error("Server died: {}".format(x))
            raise(x)
            sys.exit(-15)
    else:
        raise AlgorithmNotImplementedError()
    
