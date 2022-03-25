# Classes for making and handling peer connections

# Import required modules
import socket
import threading
import queue
import struct
import time

# Debugging
debug = False

# Class which creates multiple connections and keeps them active via threads
class connectionManager():
    def __init__(self):
        # List of active connections
        self.connection = []
        self.running_con = 0

    # Function to create an active connection
    # ConnectPeer
    def conn_peer(self, peers):
        conn_res = connectionThread(peers)
        self.connection.append(conn_res)

    # Start the connection loop
    def start_loop(self):
        self.running_con = 1
        # While connections are active -->
        # Check each connection for data
        while self.running_con:
            for each_con in self.connection:
                if not each_con.thread.is_alive():
                    continue
                # time.sleep(2.0)
                # if the connection of current thread is alive we call the func check on it
                each_con.check()

    # Function to close every connection thread
    def end_loop(self):
        # Status to 0
        self.running_con = 0
        if(debug):
            print("Closing all threads ")
        # Stopping all active threads
        for each_con in self.connection:
            each_con.stop_thread()
            # Block any running thread
            if each_con.thread.is_alive():
                each_con.thread.join()


# The main class for creating connection
class peerConnection():
    # Constructor of the class
    def __init__(self, thread_con):
        # Peer object
        self.peer = thread_con.peer
        # isConnectionDone
        self.con_done = 0

        self.send = thread_con.send_data
        self.recv = thread_con.recv_data

        # Connection statuses
        self.connet_lost = 0
        self.timeout = 0
        self.connection_failed = 0

    # Function make a connection
    def menu(self):
        try:
            # connect using TCP
            self.Tcp_connect()
        # else --> close the connection
        except ConnectionError:
            if(debug):
                print(__name__ + ".py")
                print("connection failed")
            self.connection_failed = 1

            # Close the socket
            self.S.close()
            self.S = None
            return

        # While connection not lost --> send and receive messages
        while not self.connet_lost:
            time.sleep(1)
            self.send_msg()
            self.recv_msg()

        # connection is lost --> close that connetion
        self.S.close()
        self.S = None

    # Function to connect using TCP
    def Tcp_connect(self):
        # Creating a TCP socket
        self.S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # setting default timeout
        self.S.settimeout(3.0)
        # Trying to connect to peer
        try:
            self.S.connect((self.peer.ip, self.peer.port))
        except OSError:
            if(debug):
                print(__name__ + ".py")
                print("connection failed")
            # self.Conn_failed_handle()

        # connection is done and complete
        self.con_done = 1
        self.conn_complete()

    # When connection made --> assign a peer that connection
    def conn_complete(self):
        self.peer.con_made_handle(self)

    # Function to add data to the thread send buffer
    def add_data(self, data):
        self.send.append(data)

    # Funcion to send message via TCP
    def send_msg(self):
        while True:
            try:
                # Get the data to be sent from thread buffer
                data = self.send.pop()
                # If data is available --> send data to the socket
                if data:
                    # if(debug):
                    #     print("send - ip port", self.peer.ip, self.peer.port)
                    try:
                        self.S.send(data)
                    except OSError:
                        self.connet_lost = 1
                        if(debug):
                            print(__name__ + ".py")
                            print("Connection lost")
                    if self.connet_lost:
                        return
            except:
                # thread buffer is empty so return
                return

    # Function to receive message via TCP
    def recv_msg(self):
        # If socket is null --> connection is lost
        if not self.S:
            self.connet_lost = 1
            return

        # Try receiving data from socket
        try:
            data = self.S.recv(4096)
        except ConnectionError:
            print("connection lost")
            self.connet_lost = 1
            return
        except socket.timeout:
            # if(debug):
            #     print("timeout")
            return

        # Store the received data in thread buffer
        else:
            # if(debug):
            #     print(print(".->",len(data)))
            if data:
                # taking the data in recv list
                self.recv.append(data)
                return
            return

    # Function to handle connection fail and connection lost cases
    def connection_check(self):
        if self.connection_failed:
            self.connection_failed = 0
            self.Conn_failed_handle()
        if self.connet_lost:
            self.connet_lost = 0
            self.Conn_failed_handle()

    # Function to handle connection failed
    def Conn_failed_handle(self):
        self.peer.handle_failed_con()

    # Closing connection
    def Close_connection(self):
        self.connet_lost = 1


# The class which makes threads that handle connections
class connectionThread():
    def __init__(self, peer):
        self.peer = peer
        # for checking data is continously
        # Data buffers
        self.recv_data = []
        self.send_data = []

        # connection status
        self.connection_failed = 0
        self.connection_lost = 0
        self.thread_stop = False

        # 'connection' object
        self.main_conn = peerConnection(self)

        # Create thread for each peer connection and fire it
        # Function which runs inside is peerConnection.menu()
        self.thread = threading.Thread(target=self.main_conn.menu)
        self.thread.start()

    # Function to check received data, send it peer class for processing
    # and to reset connection variables
    def check(self):
        # Check for data
        if self.recv_data:
            self.recv_data.reverse()
            while self.recv_data:
                data = self.recv_data.pop()
                # Send it peer class for processing
                if data:
                    self.peer.Peer_resp(data)
        # Reset connection variables
        if not self.thread_stop:
            self.main_conn.connection_check()

    # Stop the TCP connection Thread
    def stop_thread(self):
        self.thread_stop = True
        self.main_conn.Close_connection()


# Export con_menu
con_menu = connectionManager()