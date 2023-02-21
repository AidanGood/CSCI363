"""
Recieve over UDP with zmodem
"""
import argparse
import subprocess
import shlex
import socket
import select
import logging
import logging.config
import json
import fcntl
import sys
import os

logging.config.dictConfig(json.load(open('log_cfg.json', 'r')))
log = logging.getLogger()
parser = argparse.ArgumentParser(
    description="Zmodem UDP sender."
)
parser.add_argument('files', nargs="+",
                    help='files to send.')
parser.add_argument('--dst',
                    default = 'localhost',
                    help='Destination host, eg. hostname or 192.168.3.101 [localhost].')
parser.add_argument('--port',
                    help='Port on destination host [8888].',
                    default=8888,
                    type=int)
args = parser.parse_args()

dest = (args.dst, args.port)
for fname in args.files:
    log.info("ZSending {} to {}.".format(fname, dest))

    args = shlex.split('/usr/bin/sz -vv {}'.format(fname))
    zproc = subprocess.Popen(args,
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE)

    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    sock.setblocking(False)

    # set zproc stdout to nonblocking
    # https://stackoverflow.com/questions/375427/non-blocking-read-on-a-subprocess-pipe-in-python
    fl = fcntl.fcntl(zproc.stdout, fcntl.F_GETFL)
    fcntl.fcntl(zproc.stdout, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    while True:
        r,w,e = select.select([zproc.stdout, sock], [],[])
        if sock in r:
            # read from the socket ---> zproc (stdin)
            d = sock.recv(4096)
            #log.debug("s->z: {}".format(d))
            wr = zproc.stdin.write(d)
            if (wr != len(d)):
                log.error("Failed to write all bytes to zproc.stdin! [{}/{}]".format(
                        wr, len(d)
                    ))
            zproc.stdin.flush()
        if zproc.stdout in r:
            # read from zproc (stdout) ---> socket
            d = zproc.stdout.read(4096)
            if len(d) == 0: # is eof?
                # need to wait for the process to end
                # communicate does this.
                #zproc.communicate()
                zproc.wait()
                rc = zproc.returncode

                if rc == 0:
                    log.info("ZSend SUCCESS, {} sent to {}".format(
                        fname, dest
                    ))
                else:
                    log.error("ZSend FAILED [{}], {} likely NOT sent to {}.".format(
                        rc, fname, dest
                    ))
                    sys.exit(rc)
                break
            #log.debug("z->s: {}".format(d))
            sock.sendto(d, dest)

    sock.close()
