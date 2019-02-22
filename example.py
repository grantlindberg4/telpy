import telpy

if __name__ == '__main__':
    addr = input('Enter IP address of foreign host: ')
    username = input('Enter username: ')
    password = input('Enter password: ')

    telconn = telpy.TelnetConnection(addr)
    # See client/server interactions in detail
    telconn.set_debug()

    telconn.login(username, password)
    telconn.write('pwd')
    telconn.write('exit')
    telconn.close()
