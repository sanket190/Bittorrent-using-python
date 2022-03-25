#  Managing Peers and Pieces

from peers import Peers
from torr_download import torr_Download
from config import CONFIG
import time

debug = False

# 
class Client_Torrent():
    def __init__(self, meta_struct, con_menu):
        self.meta_struct = meta_struct
        self.con_menu = con_menu  
        self.present_peer = []
        self.peer_list = []

        self.complete = False
        
        # creating the empty list for requested peer object
        self.piece_request = [[] for i in
                              self.meta_struct['info']['pieces']]

        self.torr_down_list = []
        self.torr_down = None

        self.conn_failed_history = []
        self.Completed_pieces = [0 for i in meta_struct['info']['pieces']]
        
        # to store the downloaded pieces
        self.chunks = [[] for i in self.meta_struct['info']['pieces']]  
        self.rare_inx = []

    # Function to connect the peers
    def torrent_conn(self):
        l = len(self.peer_list)
        peer_count = 0

        while (peer_count < CONFIG['max_peers'] and peer_count < len(self.peer_list)):
            self.peer_list[peer_count].make_conn()
            self.torr_down = self.torr_down_list[peer_count]
            peer_count += 1

    # Function to initialize torrent object
    def make_peerlist(self, peer_dict):
        # check if peer is already present
        each_peer = self.check_peer(**peer_dict)
        
        if each_peer:
            return each_peer

        # peer object
        peer = Peers(self, **peer_dict)
        # creating obj of torr_Download class for each peer
        torr_obj = torr_Download(peer, self)

        self.torr_down_list.append(torr_obj)
        self.peer_list.append(peer)

        return peer

    # check if a peer already present
    def check_peer(self, ip, port, peer_id=None):
        for peers in (self.present_peer, self.peer_list):
            for i in peers:
                # only checking ip and port bcus peer_id may be different for same ip and port
                if i.ip == ip and i.port == port:  
                    return i
        return False

    def check_torr_down_obj(self, peer):
        for i in range(len(self.peer_list)):
            if self.peer_list[i] == peer:
                self.torr_down = self.torr_down_list[i]

    # Function to re establish connection to a peer
    def peer_stopped_recovery(self):
        # if download complete --> return
        if self.complete:
            return
        # check every peer
        for i in self.peer_list:
            if not i.connect_failed:
                continue

            if i in self.conn_failed_history:
                # atmost one try to connect to that peer
                continue
            self.conn_failed_history.append(i)

            while not i.con:
                try:
                    i.make_conn()
                    i.con = 1
                    if(debug):
                        print(__name__ + ".py")
                        print('Current Peer is failed : Starting New Peer :', i)
                except:
                    time.sleep(2)

            if i.con:
                break
        return

    # storing the piece into the complete list 
    def store_piece(self, piece_inx, data):
        self.Completed_pieces[piece_inx] = data
        # the piece which is complete
        self.chunks[piece_inx] = 0

    # calculating the connected peers
    def con_count(self):
        count = 0
        for peer in self.peer_list:
            if peer.con:
                count += 1
        return count

    # assigning  the count of each index of piece
    def rarest_1st(self):
        total_pieces = len(self.meta_struct['info']['pieces'])

        for i in range(total_pieces):
            con_ct = self.con_count()
            x = 0
            temp_count = 0

            while (x < con_ct):
                if self.peer_list[x].peer_piece_list[i]:
                    temp_count += 1
                x += 1
            self.rare_inx.append((i, temp_count))

    # Set the rarest index
    def set_rar_inx(self, inx_tuple):
        if self.rare_inx and inx_tuple in self.rare_inx:
            self.rare_inx.remove(inx_tuple)