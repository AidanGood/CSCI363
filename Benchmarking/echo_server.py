import socket
import argparse

def tcp(port):
    host = ''
    port = port
    size = 1024 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    s.bind((host, port)) 
    s.listen(1) 
    client, address = s.accept() 
    while True: 
        data = client.recv(size) 
        if data: 
            client.send(data) 
#        client.close()


def udp(port):
    host = ''
    port = port
    size = 1024 
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    s.bind((host, port)) 
 
    print("UDP Server Up")
    while True: 
        data, address = s.recvfrom(size) 
        print("Got Data")
        if data: 
            s.sendto(data, address)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start a TCP or UDP server')
    parser.add_argument('--port', type=int, help='Port number for the server', required=True)
    parser.add_argument('--server', choices=['tcp', 'udp'], help='Type of server to start', required=True)
    args = parser.parse_args()

    port = args.port
    server_type = args.server

    if server_type == 'tcp':
        tcp(port)
    elif server_type == 'udp':
        udp(port)
