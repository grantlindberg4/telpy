# Overview

This is a telnet client that is written entirely in python. Telnet is a protocol used to connect to a remote host. Due to its lack of security, most users use the more secure SSH protocol for encrypted communication. This program succeeds in parsing and negotiating IACs, accepting login information, and writing commands to the terminal. Please note that this is not a robust solution. I recommend instead that you use the official and well-tested library that the language itself offers: telnetlib. Read more about it here: https://docs.python.org/3.7/library/telnetlib.html.

# Requirements

* python 3 installed on your system (this program is not compatible with python 2)

# How it works

After establishing a full TCP connection to the remote host, the host will send back a sequence of bytes called IACs. This begins the negotiation phase between the host and the client. Telnet uses these IACs in order for the client and host to agree upon a set of conditions in which they may talk to one another. If the two machines can agree on how they wish to communicate with one another, the client can move to the login phase. Currently this program only handles the following IACs:

* WILL -> DONT
* DO -> WONT

This is the simplest and laziest method available to emulate a telnet client. It does not handle other IACs, which is why I indicated before that you should not rely on this in production. After negotiations are completed, the client consumes data until the login prompt is available. From there the user sends its username and password credentials. If the information is incorrect, the client will exit the login phase and indicate the error; this means that in order to log in again, the negotiation phase must be repeated. If the user successfully logs in, he may issue commands on the remote host using the `write()` method. That's about all there is to it. The methods have all been documented, and an example is included for better understanding. Just run `python3 example.py` in the proper directory and follow the usage instructions in the program. For more information on telnet, have a look at the following document: https://tools.ietf.org/html/rfc855.
