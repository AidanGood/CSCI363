
import logging
import socket
import math
import os.path
import os
import binascii
import time

from algs.utils import load_file
from algs.udp_wrapper import UdpWrapper
from algs.texcept import TransferFailed


from datetime import datetime, timedelta

log = logging.getLogger(__name__)

class ThreeAndCheck:
    def __init__(self, retries=10):
        self.retries = retries
        self.timeout = timedelta(seconds=20)

    def run_server(self, outdir, addr, mtu):
        "run the server on the given addr/port/mtu, files are stored in outdir"
        # make sure directory exists
        os.makedirs(outdir, exist_ok=True)

        # create the socket to listen on
        sock = UdpWrapper(addr)

        # use blocking on the server.
        sock.setblocking(True)

        # bind the socket to the (address, port)
        sock.bind(addr)
        in_xfr = False
        outfile = None
        last = datetime.now() - self.timeout

        log.info("Server started on {}".format(addr))

        cur_packet = 0

        while True:
            # wait for some data to arrive
            data,remote_addr = sock.recvfrom(mtu)

            if in_xfr and datetime.now() - last > self.timeout:
                # we got something but it's been too long, abort
                log.info("Abort transfer due to timeout.".format())
                in_xfr = False
                if outfile:
                    outfile.close()
                    outfile = None

            if in_xfr:
                # we are in a transfer, check for end of file
                if data[:9] == B"///END\\\\\\":
                    log.info("Done receiving file from {}.".format(
                        filepath, remote_addr))
                    in_xfr = False
                    outfile.close()
                    outfile = None
                    # let the client know we are done (ack the END message)
                    time.sleep(0.5)
                    sock.sendto(B"OKEND", remote_addr)
                else:
                    # else we got a chunk of data
                    #log.debug("Got a chunk!")

                    '''
                    Implimenting Go-Back-4 with no buffer
                    '''
                    number = int.from_bytes(data[:8], byteorder='big', signed=False)
                    

                    # Ignore out of order packets
                    if number != cur_packet:
                        sock.sendto(B'ACK' + str(cur_packet).encode(), remote_addr)
                        continue

                    rec_checksum = int.from_bytes(data[8:40], byteorder='big', signed=False)
                    checksum = binascii.crc32(data[40:])

                    # Check checksum for packet corruption
                    if rec_checksum != checksum:
                        sock.sendto(B'ACK' + str(cur_packet).encode() , remote_addr)
                        continue

                        
                    # Write data if in-order and checksum matches
                    outfile.write(data[40:])

                    #  send an ack and increment current packet number
                    
                    sock.sendto(B'ACK' + str(cur_packet).encode(), remote_addr)
                    log.info("Packet Recieved {}".format(cur_packet))
                    cur_packet += 1

                    
                    
            else:
                # we are not in a transfer, check for begin
                if data[:5] == B'BEGIN':

                    # parse the message to get mtu and filename
                    smsg = data.decode('utf-8').split('\n')
                    beginmsg = smsg[0]
                    filename = smsg[1]
                    filepath = os.path.join(outdir, filename)

                    # check mtu
                    remote_mtu= int(beginmsg.split("/")[1])
                    if remote_mtu > mtu:
                        log.error("Cannot receive {} from {}, MTU({}) is too large.".format(
                            filepath, remote_addr, remote_mtu))
                        # send an error to the client
                        sock.sentdo(B'ERROR_MTU', remote_addr)
                    else:
                        log.info("Begin receiving file {} from {}.".format(
                            filepath, remote_addr))
                        outfile = open(filepath, 'wb')
                        in_xfr = True
                        # ack the begin message to the client
                        sock.sendto(B'OKBEGIN', remote_addr)
                else:
                    # we got something unexpected, ignore it.
                    log.info("Ignoreing junk, not in xfer.")
            last = datetime.now()

    def begin_xfr(self, dest, filename, mtu):
        # create a socket to the destination (addr, port)
        sock = UdpWrapper(dest)

        #strip any path chars from filename for security
        filename = os.path.basename(filename)

        # timeout on recv after 1 second.
        sock.settimeout(1)
        tries = 0

        # retry until we get a response or run out of retries.
        while tries < self.retries:
            # construct the BEGIN message with MTU and filename
            msg = "BEGIN/{}\n{}".format(mtu, filename).encode('utf-8')

            # send the message
            sock.sendto(msg, dest)
            try:
                # wait for a response
                data, addr = sock.recvfrom(mtu)
            except socket.timeout:
                log.info("No response to BEGIN message, RETRY")
                tries += 1
                continue
            break
        # if we ran out of retries, raise an exception.
        if (tries >= self.retries):
            raise TransferFailed("No response to BEGIN message.")

        # if we got a response, make sure it's the right one.
        if data != B"OKBEGIN":
            raise TransferFailed("Bad BEGIN response from server, got {}".format(
                data
            ))

        # return the socket so we can use it for the rest of the transfer.
        return sock

    def end_xfr(self, sock, dest, mtu):
        # send the END message
        tries = 0
        while tries < self.retries:
            # send the message
            sock.sendto(B"///END\\\\\\", dest)
            try:
                # wait for a response
                data, addr = sock.recvfrom(mtu)
            except socket.timeout:
                log.info("No response to END message, RETRY")
                tries += 1
                continue
            if data != B"OKEND":
                continue
            break
        if (tries >= self.retries):
            raise TransferFailed("No response to END message.")
        # if we got a response, make sure it's the right one.
        if data != B"OKEND":
            raise TransferFailed("Bad END response from server, got {}".format(
                data
            ))


        '''
        Modified below here to send out a bunch of chunks at once for n-sending
        '''

    def xfr(self, sock, payload, dest, mtu):


        num_chunks = len(payload) - 1
        packet_ack = 0
        packet_offset = 0
        max_packet = 0
        tries = 0

        while packet_offset <= num_chunks:  
            packet_offset = packet_ack        
            log.info("Send chunks {} of {}".format(packet_offset, len(payload)-1))
            try:
                sock.sendto(payload[packet_offset], dest)
                sock.sendto(payload[packet_offset+1], dest)
                sock.sendto(payload[packet_offset+2], dest)
            except IndexError:
                log.info("Message Sent")
                break
            max_packet = packet_offset + 2
            
            sta_time = time.monotonic()
            while True:

                ela_time = time.monotonic() - sta_time
                if ela_time >= 0.03:
                    break


                if (tries >= self.retries):
                    raise TransferFailed("No response to CHUNK message.")
                
                try:
                    # wait for an ACK
                    sock.settimeout(0.5)

                    data, addr = sock.recvfrom(mtu)
                    
                except socket.timeout:
                    log.info("No response to CHUNK message, RETRY")
                    tries += 1
                    continue

                # if we got a good ACK, increment current packet (chucnk was received)
                if data == B"ACK"+ str(packet_ack).encode():
                    packet_ack += 1
                    tries = 0
                    if packet_ack == max_packet:
                        break
                    continue
                else:
                    log.info("Bad response from server, got {} instead of ACK{}, RETRY".format(
                            data, packet_offset))
                    try:
                        rec_ack = int(data.decode()[3:])
                        if rec_ack > packet_ack:
                            packet_ack = rec_ack
                        elif rec_ack < packet_ack:
                            packet_ack = rec_ack
                    except: # corrupted ack most likely, retry
                        continue
                    
                    
                    

    def chunk(self, payload, mtu):
        "break a payload into mtu sized chunks"
        # chunking by MTU + checksum + counter size
        offset = mtu-(8+32)
        chunks = math.ceil(len(payload) / offset)
        
        return [i.to_bytes(8, 'big')+ binascii.crc32(payload[i*offset:(i+1)*offset]).to_bytes(32, 'big') + payload[i*offset:(i+1)*offset] for i in range(chunks)], len(payload) + 40 * chunks
        

    def send_file(self, filename, dest, mtu):
        "Entrypoint for three-and-check sending"
        st = datetime.now()
        log.info("Sending with three-and-check {} --> {}:{} [MTU={}].".format(
            filename, dest[0], dest[1], mtu))

        # break the file into mtu sized pieces
        payload, total_bytes = self.chunk(load_file(filename), mtu)

        # begin the transfer
        s = self.begin_xfr(dest, filename, mtu)

        # send the chunks
        self.xfr(s, payload, dest, mtu)

        # end the transfer
        self.end_xfr(s, dest, mtu)

        # print stats
        et = datetime.now()
        seconds = (et-st).total_seconds()
        log.info("Sent with three-and-check {} in {} seconds = {:.0f} bps.".format(
            filename, seconds,
            total_bytes / seconds))

        return True

# singleton
tc = ThreeAndCheck()
