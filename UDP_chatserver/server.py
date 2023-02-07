import sys
import socket

def main(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(('127.0.0.1', port))

    clients = {}

    while True:
        # Get message
        data, address = server.recvfrom(1024)
        
        # If message comes from someone new add to client list
        if address not in [c for c in clients.keys()]:
            if len(clients) < 100:
                print(f'New connection from {address}')
                name = "Nickname"
                clients[address] = name

        # Else message came from someone already in client list
        else:
            # /nick command to change nickname
            if data.decode("utf-8").startswith("/nick"):
                newName = data.decode("utf-8").split()[1]
                clients[address] = newName
                continue

            # /list command to list all nicknames
            if data.decode("utf-8").startswith("/list"):
                server.sendto(str(clients.values()).encode("utf-8"), address)
                continue

            # /quit command to remove address from list of clients
            if data.decode("utf-8").startswith("/quit"):
                clients.pop(address)
                continue

            # /message command to send private message
            if data.decode("utf-8").startswith("/message"):
                reciever = data.decode("utf-8").split()[1]
                sendAddress = [addr for addr in clients.keys() if clients[addr] == reciever][0]
                data = data.decode("utf-8").split()[2:]
                data = ''.join(data)
                server.sendto(f'{clients[address]}: {data}'.encode('utf-8'), sendAddress)
                continue

            # Not a command, so echo the message to other clients
            for c in clients.keys():
                if c != address:
                    server.sendto(f'{clients[address]}: {data.decode("utf-8")}'.encode('utf-8'), c)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(int(sys.argv[1]))
    else:
        print("server.py [port]")

