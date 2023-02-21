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
    description="Zmodem UDP receiver."
)

parser.add_argument('--addr',
                    help='Address to listen on [0.0.0.0].',
                    default='0.0.0.0')
parser.add_argument('--port',
                    help='Port to listen on [8888].',
                    default=8888,
                    type=int)
args = parser.parse_args()
addr = (args.addr, args.port)

log.info("Zrecieve waiting for files.")

# -y is for clobber existing files.
args = shlex.split('/usr/bin/rz -vv -y')
zproc = subprocess.Popen(args,
                       stdin=subprocess.PIPE,
                       stdout=subprocess.PIPE)

sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
sock.setblocking(False)
sock.bind(addr)

# set zproc stdout to nonblocking
# https://stackoverflow.com/questions/375427/non-blocking-read-on-a-subprocess-pipe-in-python
fl = fcntl.fcntl(zproc.stdout, fcntl.F_GETFL)
fcntl.fcntl(zproc.stdout, fcntl.F_SETFL, fl | os.O_NONBLOCK)
remote_addr = None
while True:
    r,w,e = select.select([zproc.stdout, sock], [],[])
    if sock in r:
        # read from the socket ---> zproc (stdin)

        d, remote_addr = sock.recvfrom(4096)
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
            zproc.wait()
            rc = zproc.returncode

            if rc == 0:
                log.info("Zrecv SUCCESS.")
            else:
                log.error("Zrecv FAILED [{}]".format(
                    rc
                ))                
                sys.exit(rc)
            break
        if remote_addr:
            #log.debug("z->s: {}".format(d))
            sock.sendto(d, remote_addr)
        #else drop the data, zmodem can deal with this.

sock.close()
