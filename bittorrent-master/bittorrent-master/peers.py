# Handling Communications with peers

# Import required modules
import struct
import random
import sys

from config import CONFIG

# For debugging
debug = False

# The peer class

class Peers():
    def __init__(self, torr, ip, port, peer_id=None):
        self.ip = ip
        self.port = port
        self.torr = torr
        # if peer id is passed as a parameter then it gets assigned otherwise its default value is None
        self.peer_id = peer_id

        # maintaining the information of each connection of remote peer
        # intial assignment.
        self.choking = 1
        self.interested = 0
        self.peer_choking = 1
        self.peer_interested = 0

        self.connect_failed = 0
        self.connect_start = 0
        
        # 'connection' Object
        self.con = None

        self.peer_piece_list = []
        self.pieces = len(torr.meta_struct['info']['pieces'])

        self.set_peer_piece_list()
        self.target_piece_inx = None

        # concanate the data if it comes in pieces
        self.buffer = b''
        self.starting_point = 0

        # making list of all msg_types according the their msg id as index
        self.msg_types = ['choke', 'unchoke', 'interested', 'not_interested', 'have', 'bitfield', 'request', 'piece',
                          'cancel', 'port']

    # Initializing peer_piece_list
    def set_peer_piece_list(self):
        for i in range(self.pieces):
            self.peer_piece_list.append(0)

    # Function to make peer connection (threaded)
    def make_conn(self):
        # Creating a new threadedconnection for the peer
        self.torr.con_menu.conn_peer(self)

    # Making a TCP handshake
    def handshake(self):
        if(debug):
            print(__name__ + ".py")
            print("Sending handshake")
        resp = self.make_handshake(
            self.torr.meta_struct['info_hash'], CONFIG['peer_id'])
        self.send_msg(resp)

    # Function to construct handshake data
    def make_handshake(self, info_hash, peer_id):
        # Protocol identifier string
        pstr = b'BitTorrent protocol'
        # <pstrlen><pstr><reserved><info_hash><peer_id>
        # %d -> len(pstr) # !-> big endian
        format = '!B%ds8x20s20s' % len(pstr)
        data = struct.pack(format, len(pstr), pstr, info_hash, peer_id)
        return data

    # Function to add data the send thread buffer
    def send_msg(self, data):
        # If connection is active --> add data to it
        if self.con:
            self.con.add_data(data)

    # Handle failed connection
    def handle_failed_con(self):
        self.connect_failed = 1
        self.con = None
        self.torr.peer_stopped_recovery()

    # Assign connection object and start downloading() 
    def con_made_handle(self, con):
        self.con = con
        if(debug):
            print(__name__ + ".py")
            print("Connection made ")
        self.downloading()

    # Function to communicate after handshake is made
    def pass_msg(self, **arguments):
        msg = self.make_msg(**arguments)
        self.send_msg(msg)

    # Function to construct message
    def make_msg(self, **arguments):  # here arg is dictionary
        if len(arguments) == 1:
            msg_type = arguments['msg_type']
        # Message is a piece
        else:
            msg_type = arguments['msg_type']
            piece_inx = arguments['piece_inx']
            block_length = arguments['block_length']
            starting_point = arguments['starting_point']

        # all remaining msg is of the type <length prefix><message ID><payload>
        msg_No = None  # message ID is single byte decimal

        payload = b''  # payload is message dependent

        if msg_type == 'choke':
            msg_No = 0  # fixed length no payload
        elif msg_type == 'unchoke':
            msg_No = 1  # fixed length no payload
        elif msg_type == 'interested':
            msg_No = 2  # fixed length no payload
        elif msg_type == 'not interested':
            msg_No = 3  # fixed length no payload
        elif msg_type == 'have':
            msg_No = 4  # fixed length
        elif msg_type == 'bitfield':
            msg_No = 5  # fixed length
        elif msg_type == 'request':
            msg_No = 6

            if(debug):
                print(__name__ + ".py")
                print("Send request", piece_inx, starting_point, block_length)

            # the payload
            payload = struct.pack(
                '!LLL', piece_inx, starting_point, block_length)

        # length prefix is four byte big-endian value
        # but observe that it is  0001 when payload is empty but changes when payload length is not empty
        length_prefix = len(payload) + 1

        # Format of message
        # B->unsigned char , l -> long , s-> char
        format = '!lB%ds' % len(payload)
        # Conversion
        msg = struct.pack(format, length_prefix, msg_No, payload)

        return msg

    # Function to parse handshake response
    def parse_hand_resp(self, data):
        # check it is in correct format  or not
        pstrlen = int(data[0])  # 19
        remaining_data = data[1:49 + pstrlen]  # 1->68 byte of data

        # this length of extra data which is comes with handshake
        extra_data = 1 + len(remaining_data)

        # Format of handshake
        format = '!%ds8x20s20s' % pstrlen
        # Unpacking the message
        res = struct.unpack(format, remaining_data)

        # Decoding the handshake response
        dec_dict = {}
        dec_dict['pstr'] = res[0].decode('utf')
        dec_dict['info_hash'] = res[1]
        dec_dict['peed_id'] = res[2]

        # handshake resp is correct so connection with peer is established
        if dec_dict['pstr'] == 'BitTorrent protocol':
            self.connect_start = 1
            if(debug):
                print(__name__,"recv handshake")
            # so handshake is ok
            self.downloading()
            return extra_data

    # Function to parse the message response
    def parse_msg_resp(self, msg):
        # dict to store
        msg_dict = {}
        # extract length prefix
        total_bytes = 0

        # invalid response
        if len(msg) < 4:
            return 0

        # taking first four byte from first tuple
        length_prefix = struct.unpack('!L', msg[:4])[0]

        msg_dict['length_prefix'] = length_prefix
        total_bytes += 4  # four byte length prefix

        # keep alive message
        if length_prefix == 0:
            return total_bytes

        # if the data that comes is not complete then we just return and add that data into the buffer
        if total_bytes + length_prefix > len(msg):
            return 0

        # from fourth byte to the length of prefix has msg id and payload
        data = msg[total_bytes:total_bytes + length_prefix]
        total_bytes += length_prefix

        msg_no = int(data[0])
        payload = data[1:]

        # msg_no and payload
        msg_dict['msg_no'] = msg_no
        msg_dict['payload'] = payload

        msg_type = self.msg_types[msg_no]
        
        if(debug):
            print(__name__ + ".py")
            print("Peer's message :", msg_no, msg_type)

        # setting peer status
        self.set_peer_status(msg_dict, msg_type)
        return total_bytes

    # 
    def Peer_resp(self, resp):
        # parsing the handshake resp according the format as we send
        # if there is remaining data which is of previous resp then we concanate that new data with the older one
        data = self.buffer + resp
        res = 0

        while data:
            # If connection is not started --> parse handshake response
            if not self.connect_start:
                res = self.parse_hand_resp(data)
            else:
                # peers is already done handshake
                res = self.parse_msg_resp(data)
            if res == 0:
                break
            # if resp from peer is correct then this data become zero and that means buffer becomes zero
            data = data[res:]
        self.buffer = data

    # Set piece index
    def set_target_piece_inx(self):
        self.target_piece_inx = None

    # Getting ready for next piece
    def downloading(self):
        # check if is handshake is done or not
        if not self.connect_start:
            self.handshake()
        elif self.peer_choking:
            if(debug):
                print(__name__ + ".py")
                print("send interested")
            # try to send the msg to peer that we are interested
            self.pass_msg(msg_type='interested')
        else:
            # Else --> client unchoked --> send request for piece
            # Take rarest piece first
            if not self.torr.rare_inx:
                self.torr.rarest_1st()

            # Piece index
            piece_inx = self.new_piece_inx()

            if piece_inx == None:
                return

            self.target_piece_inx = piece_inx

            if(debug):
                print(__name__ + ".py")
                print(piece_inx)
            
            # Link piece with peer
            self.torr.piece_request[piece_inx].append(self)

            # as piece length is so large that we cannot request whole piece at once
            # hence we requesting the piece in chunks we called as block
            self.request_Block(piece_inx, None)

    # Request a block from peer
    def request_Block(self,p_indx,start_pt):
        # Starting point
        if start_pt == None:
            starting_point = 0
        else:
          starting_point = start_pt + CONFIG['block_length']

        # Last Index
        last_inx = self.pieces - 1

        if p_indx == last_inx:
            len_piece = self.torr.meta_struct['info']['piece_length']
            total_length = self.torr.meta_struct['info']['length']
            # calculating the blocklength for last piece
            len_block = (total_length - (last_inx * len_piece))
            new_block_len = len_block - starting_point

            # if calculated block length is length is less than required block length then we asign that length to block_length
            if new_block_len < CONFIG['block_length']:
                block_len = new_block_len

            else:
                block_len = CONFIG['block_length']
        else:
             block_len = CONFIG['block_length']

        # Send request message
        self.pass_msg( msg_type = 'request',piece_inx = p_indx,starting_point = starting_point, block_length = block_len)

    # Finding rarest index
    def find_rar_inx(self):
        min_val = 99999
        rar_inx = 0
        rar_arr_inx = None

        # Checking the torrent rare index
        for i in (self.torr.rare_inx):
            if i:
                if i[1] < min_val and i[1] != 0:
                    min_val = i[1]
                    rar_inx = i[0]
                    rar_arr_inx = i
        # Return rarest index
        return (rar_inx, rar_arr_inx)

    # return an appropriate piece to be requested
    # check that if a current peer has the piece or not and also if that piece is already requested to another peer --> go for next piece
    def new_piece_inx(self):
        for loop in range(self.pieces):
            piece_inx, rar_arr_tuple = self.find_rar_inx()
            
            # checking the piece is complete or not
            if (self.peer_piece_list[piece_inx] and not self.torr.piece_request[piece_inx]):

                if rar_arr_tuple in self.torr.rare_inx or self.torr.rare_inx:
                    # even if all all tuples are removed from the rare_inx list we need not remove it bcoz we already complete rarest first strategy
                    self.torr.set_rar_inx(rar_arr_tuple)
                
                return piece_inx

            elif self.torr.piece_request[piece_inx]:
                self.torr.set_rar_inx(rar_arr_tuple)
            elif not self.peer_piece_list[piece_inx]:
                self.torr.set_rar_inx(rar_arr_tuple)

        # now request a piece which is not complete and which is available to this peer
        for piece_i in range(self.pieces):
            if not self.torr.torr_down.complete[piece_i] and self.peer_piece_list[piece_inx]:
                return piece_i
        #print("None", self.peer_piece_list, piece_inx)
        return

    # Setting peer status according to responses
    def set_peer_status(self, msg_dict, msg_type):
        # checking msg resp
        if msg_type == 'choke':
            self.peer_choking = 1
            self.downloading()
        elif msg_type == 'unchoke':
            self.peer_choking = 0
            # peer unchock --> go to downloading
            self.downloading()  
        elif msg_type == 'interested':
            self.peer_interested = 1
        elif msg_type == 'not_interested':
            self.peer_interested = 0
        elif msg_type == 'have':
            # taking the index of the pieces the peers have
            (indx,) = struct.unpack('!L', msg_dict['payload'])
            # setting the index of pieces that peer have
            self.peer_piece_list[indx] = 1

        elif msg_type == 'bitfield':
            # The payload is a bitfield representing the pieces that peer has that piece
            payload = msg_dict['payload']

            # converting bytes to binary
            res = bin(int.from_bytes(payload, byteorder=sys.byteorder))

            if len(res) < self.pieces:
                for x in range(2,len(res)):
                    self.peer_piece_list[x - 2] = res[x]
            else:
                for i in range(2,self.pieces + 2):
                    # here 1 indicates the pieces the peer has
                    if i < len(self.peer_piece_list)+2 and i < len(res):
                        self.peer_piece_list[i-2] = int(res[i])

        elif msg_type == 'piece':
            # Payload
            full_payload = msg_dict['payload']
            # taking first two byte
            (piece_inx,block_start) = struct.unpack('!LL',full_payload[:8])
            payload = msg_dict['payload'][8:]

            if(debug):
                print(__name__ + ".py")
                print("st_tuple->",piece_inx,block_start)
            
            # Checking torrent download
            self.torr.check_torr_down_obj(self)
            self.torr.torr_down.check_block(piece_inx, block_start, payload)
        
        elif msg_type == 'cancel':
            print('cancel')
        elif msg_type == 'port':
            print("port")
