# UDP Python chat server

## Has the following commands/features:

/nick [nickname]
 - Will change the default "Nickname" to the name put in

/list 
 - will return a list of all users on the server

/message [nickname] [message]
 - will send a private message to the user with the given nickname

/quit
 - will remove the user from the list of clients on the server, and will no longer recieve any messages until they reconnect

100 user limit

## Usage
Start the server by running `python server.py 8890`

Set up clients with `nc -u 127.0.0.1 8890`

Clients add themselves to the server's client list by sending any initial message. This initial message will not be broadcast to the rest of the clients. All following messages will be broadcast, except commands.

After sending `/quit`, clients can reconnect by sending any message again. 