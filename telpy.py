import socket
import struct
import sys

class TelnetConnection():
    def __init__(self, addr, port=23, timeout=None):
        '''
            Instantiates a new TelnetConnection object and connects to
            the foreign host 'addr'. Sets up telnet commands and
            prompts that will be used between the server and client.
            By default, the debug flag is set to false. In order to
            activate it, the user must call 'set_debug()'.

            * addr - address of foreign host
            * port - port number to use on target machine. This is
                     particularly useful if telnet is listening on a
                     port other than 23 on the foreign host. Defaults
                     to 23.
            * timeout - the timeout period to wait for an operation to
                        complete. Defaults to None.
        '''

        self.prompts = ':>$#%'
        self.commands = {
            'SE': 240,
            'NOP': 241,
            'DM': 242,
            'BRK': 243,
            'IP': 244,
            'AO': 245,
            'AYT': 246,
            'EC': 247,
            'EL': 248,
            'GA': 249,
            'SB': 250,
            'WILL': 251,
            'WONT': 252,
            'DO': 253,
            'DONT': 254,
            'IAC': 255
        }

        self.debug = False
        self.logged_in = False
        self.conn = self.establish_connection(addr, port, timeout)

        hostname = socket.gethostname()
        self.client = socket.gethostbyname(hostname)
        self.serv = addr

    def set_debug(self):
        '''
            Turns on debug mode for the telnet client. This will output
            a log of data that is sent and received between the server
            and client, including the specific IACs encountered as
            well as any data returned from executing remote commands.
        '''

        self.debug = True
        print('DEBUG MODE ON\n')

    def match_code(self, code):
        '''
            Attempts to match the given code to an existing one in
            the list of commands. If no command is found, returns None.
        '''

        for cmd in self.commands:
            if self.commands[cmd] == code:
                return cmd

        return None

    def print_commands(self, data):
        '''
            Prints any IACs that appear in the data

            * data - the data being sent/received
        '''

        for i in range(len(data)):
            if data[i] == self.commands['IAC']:
                code = data[i+1]
                code = self.match_code(code)
                val = data[i+2]
                if code:
                    print('IAC %s %d' % (code, val))
                else:
                    print('Unknown IAC encountered!')

    def print_debug(self, host, data):
        '''
            Prints debug messages to the user. This includes data
            traveling between the hosts as well as the specific IACs
            being sent. If debug mode is not set, this will return
            immediately without printing anything.

            * host - the host sending the data
            * data - the data being sent
        '''

        if not self.debug:
            return

        print('%s: %s' % (host, data))
        self.print_commands(data)
        print()

    def establish_connection(self, addr, port=23, timeout=None):
        '''
            Establishes a connection to the given host. This is done
            automatically in the constructor.

            * addr - IP address of foreign host
            * port - port number to use on target machine. This is
                     particularly useful if telnet is listening on a
                     port other than 23 on the foreign host. Defaults
                     to 23.
            * timeout - the timeout period to wait for an operation to
                        complete. Defaults to None.

            Returns a socket object referring to the connection made
            to the foreign host
        '''

        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.setdefaulttimeout(timeout)

        try:
            conn.connect((addr, port))
        except OSError:
            print('[-] Unable to connect to %s:%d' % (addr, port))
            sys.exit(1)

        return conn

    def handle_command(self, code, val):
        '''
            Creates a response to the IAC given by code and val. This
            method is limited in the sense that it only knows how to
            handle two particular codes: WILL and DO. In order to
            emulate the simplest client possible, we respond to these
            codes accordingly:

            WILL -> DONT
            DO -> WONT

            If an IAC code appears that cannot be handled, the program
            will exit

            * code - the type of IAC command
            * val - the new value for the code

            Returns bytes representing the response that can be sent
            to the remote host
        '''

        resp = [self.commands['IAC']]

        if code == self.commands['WILL']:
            resp.append(self.commands['DONT'])
        elif code == self.commands['DO']:
            resp.append(self.commands['WONT'])
        else:
            print('No method to handle IAC code: %d' % code)
            sys.exit()

        resp.append(val)

        resp = bytes(resp)

        return resp

    def negotiate(self, data):
        '''
            Handles negotiations between the client and server
            regarding issues including echo and window size. If the
            data does not resemble negotiation data, the method will
            exit early.

            * data - negotiation data to be parsed and acknowledged
        '''

        pos = 0
        while pos < len(data):
            if data[pos] != self.commands['IAC']:
                # No negotiation to be done/gibberish
                pos += 1
                continue

            code = data[pos+1]
            if code == self.commands['IAC']:
                # Extra IAC, whoops
                pos += 1
                continue

            val = data[pos+2]

            resp = self.handle_command(code, val)
            self.print_debug(self.client, resp)
            self.conn.send(resp)
            pos += 2

    def read_until(self, phrase):
        '''
            Consumes data from the server until a particular phrase is
            recognized. The client will attempt to make negotiations if
            it recognizes any.

            * phrase - the phrase to be matched and recognized
        '''

        phrase = bytes(phrase, 'ascii')

        while True:
            data = self.conn.recv(1024)
            self.print_debug(self.serv, data)
            if not data:
                print('[-] Unable to complete negotiation process')
                sys.exit(1)

            if phrase in data:
                break

            self.negotiate(data)

    def expect(self, phrases):
        '''
            Consumes data from the server until an item in 'phrases' is
            recognized. The client will attempt to make negotiations if
            it recognizes any.

            * phrases - a list of phrases to be matched and recognized

            Returns a tuple which includes the index and corresponding
            phrase that matches. If no phrase was found, returns
            (-1, None).
        '''

        while True:
            data = self.conn.recv(1024)
            self.print_debug(self.serv, data)
            if not data:
                print('[-] Unable to complete negotiation process')
                sys.exit(1)

            result = self.match_phrase(phrases, data)
            if result[0] != -1:
                return result

            self.negotiate(data)

        return (-1, None)

    def match_phrase(self, phrases, data):
        '''
            Attempts to find a matching phrase in the next stream of
            data

            * phrases - an iterable of phrases to be matched
            * data - the data to be searched

            Returns the index and corresponding phrase that matches.
            If no phrase was found, returns (-1, None)
        '''

        for i, phrase in enumerate(phrases):
            phrase = bytes(phrase, 'ascii')
            if phrase in data:
                return (i, phrase)

        return (-1, None)

    def login(self, username, password):
        '''
            Attempts to log into the remote host using the given
            username and password. The phrases 'ogin' and 'assword'
            are used as a catch-all solution, since some boxes may use
            lowercase letters and some may use uppercase. If the login
            information is incorrect, the program will throw an error
            and exit. Otherwise, the user is indicated to have logged
            in and they now may remotely send commands.

            * username - username to attempt
            * password - password to attempt
        '''

        username = bytes(username + '\n', 'ascii')
        self.read_until('ogin')
        self.conn.send(username)
        self.print_debug(self.client, username)

        password = bytes(password + '\n', 'ascii')
        self.read_until('assword')
        self.conn.send(password)
        self.print_debug(self.client, password)

        expected = ['ncorrect']
        expected.extend(list(self.prompts))
        result = self.expect(expected)
        if result[0] > 0:
            self.logged_in = True
        else:
            print('[-] Unable to log in')
            if result[0] == 0:
                print('    Incorrect username or password')
            else:
                print('    Unknown error')

    def write(self, cmd):
        '''
            Issues a command to the remote host. If debug mode is on,
            the user may see the output of these commands. If the user
            is not logged in, this method will throw an error and exit.

            * cmd - the command to be issued to the remote host
        '''

        if self.logged_in:
            self.expect(self.prompts)
            cmd = bytes(cmd + '\n', 'ascii')
            self.conn.send(cmd)
            self.print_debug(self.client, cmd)
            output = self.conn.recv(1024)
            self.print_debug(self.serv, output)
        else:
            print('[-] Unable to write: `%s` to terminal' % cmd)
            print('    You are not logged in')

    def close(self):
        '''
            Gracefully closes the connection to the remote host and
            logs the user out.
        '''

        self.logged_in = False
        self.conn.close()

