import argparse
import socket
import time
import random
import threading
import struct

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate network traffic packets')
parser.add_argument('--protocol', choices=['tcp', 'udp'], default='udp', help='Protocol to use')
parser.add_argument('--size', type=int, default=1024, help='Packet size in bytes')
parser.add_argument('--bandwidth', type=int, default=100, help='Bandwidth in packets per second')
parser.add_argument('--distribution', choices=['burst', 'uniform'], default='uniform', help='Distribution of packets to generate')
parser.add_argument('--duration', type=int, default=10, help='Duration to run in seconds')
args = parser.parse_args()

# Initialize variables
global list_of_sent_packets, list_of_recieved_packets, packets_sent, total_packets_sent, total_packets_received, packets_received
packet_loss = 0
out_of_order_packets = 0
total_packets_sent = 0
total_packets_received = 0
packets_sent = 0 
packets_received = 0
rtt = 0
run_time = time.time()
list_of_sent_packets = []
list_of_recieved_packets = []


class Packet:
    def __init__(self, data, time_start):
        self.data = data
        self.time = time_start


# Create a socket based on protocol and connect to socket 12345
if args.protocol == 'tcp':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
else:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.connect(('134.82.9.147', 12345))
sock.settimeout(1)

# Sends packets with increasing data
def send_packets():
    global total_packets_sent, packets_sent, list_of_sent_packets, run_time
    while (time.time() - run_time) < args.duration:
        total_packets_sent += 1
        packet_data = struct.pack("i", packets_sent)

        # Send packet in burst mode
        if args.distribution == 'burst':
            send_time = time.time()
            sock.send(packet_data)
            print('Packet sent successfully')
            list_of_sent_packets.append(Packet(packets_sent, send_time))
            packets_sent += 1
            
            time.sleep(1/args.bandwidth - (time.time() - send_time))

        # Send packet in uniform mode
        else:
            send_time = time.time()
            sock.send(packet_data)
            print('Packet sent successfully')
            list_of_sent_packets.append(Packet(packets_sent, send_time))
            packets_sent += 1

            send_interval = 1/args.bandwidth - (time.time() - send_time)
            if send_interval > 0:
                time.sleep(send_interval)


# Function to track incoming packets and increment total_packets_received
def receive_packets():
    global packets_received, total_packets_received, list_of_recieved_packets, run_time
    while (time.time() - run_time) < args.duration:
        try:
            response = sock.recv(args.size)
            
            packets_received += 1
            total_packets_received += 1
            int_resp = struct.unpack("i", response)
            recv_time = time.time()
            
            list_of_recieved_packets.append(Packet(int_resp, recv_time))
        except socket.timeout:
            print("####################")
            pass


# Start threads to send and receive packets
send_thread = threading.Thread(target=send_packets)
send_thread.start()

recv_thread = threading.Thread(target=receive_packets)
recv_thread.start()

# Wait for duration to elapse
time.sleep(args.duration)

# Get list of recieved packet order
def get_recv(list_recv):
    list_nums = []
    for packet in list_recv:
        list_nums.append(packet.data[0])
    return list_nums
# Calculate packet OOO and lost numbers
def calculate_packet(rec_packets):
    seen = []
    oooCount, missingCount = 0, 0
    for i, v in enumerate(rec_packets):
        if(i == len(rec_packets) - 1):
            break
        elif rec_packets[i] > rec_packets[i+1]:
            oooCount += 1
            seen.append(v)
        elif v != rec_packets[i+1] - 1:
            for j in range(v+1, rec_packets[i+1]):
                if ((j not in seen) and (j not in rec_packets)):
                    missingCount += 1
    print("Out Of Order: " + str(oooCount))
    print("Missing: " + str(missingCount))
    return(oooCount, missingCount)
list_nums = get_recv(list_of_recieved_packets)
ooo, missing = calculate_packet(list_nums)

# Sort the list of recieved packets
# technically doesn't get 100% if a packet is dropped but is close enough
def clean_recv(list_of_recieved_packets):
    sorted_list = []
    #print(list_of_recieved_packets)
    # Loop through each number in the original list
    for i in range(len(list_of_recieved_packets)):
        for packet in list_of_recieved_packets:
            if packet.data[0] == i:
                sorted_list.append(packet)
                break
            else:
                continue

    return sorted_list

# Calculate the RTT for all packets recieved
def calc_rtt(sent_list, sorted_list):
    _rtt = 0
    for i in range(min(len(sent_list), len(sorted_list))):
        for packet in sent_list:
            if packet.data == i:
                sent_rtt = packet.time
                break
        for packet in sorted_list:
            if packet.data[0] == i:
                recv_rtt = packet.time
                break
        try:
            _rtt += recv_rtt - sent_rtt
        except:
            continue
    return _rtt


list_of_sorted = clean_recv(list_of_recieved_packets)
rtt = calc_rtt(list_of_sent_packets, list_of_sorted)

# Collect statistics
try:   
    packet_loss = missing / total_packets_sent
except:
    packet_loss = 0
try: 
    out_of_order_packets = ooo / total_packets_sent 
except:
    out_of_order_packets = 0

avg_rtt = rtt / total_packets_sent

# Display collected statistics
print('Packet loss rate: {:.4f}%'.format(packet_loss))
print('Out of order packet rate: {:.4f}%'.format(out_of_order_packets))
print('Average RTT: {:.2f} ms'.format(avg_rtt * 1000))


