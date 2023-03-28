"""
A sample program to send ICMP echo requests to a host to demonstrate
how to use the socket module to send and receive ICMP messages.

This requires root privileges to run. 
sudo su

Marchiori, 2023

test sites:

eg.bucknell.edu
bbc.co.uk
asahi-net.jp
google.com
yahoo.com
apple.com

"""

import argparse
import socket
import struct
import time
import random

def icmp_socket(timeout = 1, ttl = 1):
	"Create a raw socket for ICMP messages"
	s = socket.socket(
			family = socket.AF_INET, 
		    type = socket.SOCK_RAW, 
			proto = socket.getprotobyname("icmp"))
	# Set the timeout
	s.settimeout(timeout)
	# Set the TTL
	s.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
	return s

def checksum(data):
	"Calculate the checksum for the data"
	sum = 0
	# make 16 bit words out of every two adjacent 8 bit words in the packet
	for i in range(0, len(data), 2):
		if i + 1 < len(data):
			sum += (data[i] << 8) + data[i+1]
		else:
			sum += data[i] << 8
	# take only 16 bits out of the 32 bit sum and add up the carries
	sum = (sum >> 16) + (sum & 0xffff)
	sum += (sum >> 16)
	
 	# one's complement
	return ~sum & 0xffff


def ping(host, skt = None, seqno = 1, ttl = 30, quiet = False):

    ident = random.randint(0, 0xffff)
    header = struct.pack("!BBHHH", 8, 0, 0, ident, seqno)
    send_time_ns = int (1e9 * time.time())
    payload = struct.pack ("!Q", send_time_ns)

    packet = header + payload
    
    c = checksum(packet)
    header = struct.pack("!BBHHH", 8, 0, c, ident, seqno)
    packet = header + payload

    # Set the TTL
    skt.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
    skt.sendto(packet, (host, 0)) 
    resp, addr = skt.recvfrom(1024)
    timeReceived = time.time()
    
    rx_time_ns = int(1e9 * time.time())

    # parse the ICMP header received.
    icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq = \
        struct.unpack("!BBHHH", resp[20:28])

    local_check = checksum(resp)

    icmp_send_time = struct.unpack("!Q", resp[28:36])[0]

    rtt_ns = rx_time_ns - icmp_send_time
    rtt_ms = rtt_ns / 1e6

    if icmp_type == 0:
        print("Reached host " + host + " in " + str(ttl) + " hops")
        return False

    hostName = ""
    try:
        hostName = str(socket.gethostbyaddr(str(addr[0]))[0])
    except:
        hostName = str(addr[0])

    print(str(ttl) + " " + hostName + " (" + str(addr[0]) + ")")
    return True

if __name__=="__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("host", help="Host to ping")
	parser.add_argument("-t", "--ttl", help="Time to live", default=30, type=int)
	parser.add_argument('-n', '--num', help="Number of pings", default=3, type=int)
	args = parser.parse_args()
	
	# if doing multiple pings, you can reuse the same socket
	s = icmp_socket()
	rtts = []
	try:				
		# wrap this in a try block so we can close the socket if there is an error	
		i = 0	
		valid = True
		while valid:
			i += 1
			valid = ping(args.host, seqno = i, skt = s, ttl=i)
		
	except KeyboardInterrupt:
		print("^C")
	finally:
		# close the socket when done
		s.close()
