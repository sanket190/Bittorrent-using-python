# Checking downloaded contents and percentage of download

import hashlib
from Write_data import Write_data

# For debugging
debug = False

# torr_Download class
class torr_Download():
    def __init__(self, peer, torr):
        self.peer = peer
        self.torr = torr

        # for collecting the all downlaoded piece
        self.complete = self.torr.Completed_pieces  
        self.chunks = self.torr.chunks

    # checking if recv block is already present or not
    def check_block(self, piece_inx, chunk_start, payload):
        if self.complete[piece_inx]:
            print("this chunks is finished")
            return
        
        for i in self.chunks[piece_inx]:
            # if starting point of recv block is already present then we request next block
            if i[0] == chunk_start:
                print("Already present")
                self.peer.request_Block(piece_inx, chunk_start)
                return

        # storing the tuple of starting point pf payload with payload at that indx
        self.chunks[piece_inx].append(
            (chunk_start, payload))
        last_inx = self.peer.pieces - 1

        # piece index is last then we need to update the required length
        if piece_inx == last_inx:
            len_piece = self.torr.meta_struct['info']['piece_length']
            total_length = self.torr.meta_struct['info']['length']
            len_block = (total_length - (last_inx * len_piece))
            required_len = len_block
        else:
            required_len = self.torr.meta_struct['info']['piece_length']
        
        curre_len = self.sum_piecelen(piece_inx)
        if(debug):
            print(__name__ + ".py")
            print(required_len, curre_len)
        
        # checking if the piece length of .torrent file is same as total received block length
        if curre_len == required_len:
            # check hashvalue
            self.check_hashvalue(piece_inx)
        else:
            # here we change starting point of block
            # requesting the next block as we requesting the pieces in blocks
            self.peer.request_Block(piece_inx,chunk_start) 
            pass

    # adding the each blocks length
    def sum_piecelen(self, curr_piece_inx):
        sum = 0
        for x in self.chunks[curr_piece_inx]:
            sum += len(x[1])
        return sum

    # Function to check for hash value
    def check_hashvalue(self, piece_inx):
        # sorting the collected piece so that it is in ordered
        self.chunks[piece_inx].sort(key=lambda x: x[0])
        blocks = []

        # getting the piece
        for k in self.chunks[piece_inx]:
            blocks.append(k[1])
        
        # Current piece
        current_piece = bytes(y for x in blocks for y in x)
        
        # SHA hash of current piece
        curr_piece_sha = hashlib.sha1(current_piece).digest()

        # List of SHAs of pieces
        file_shas = self.torr.meta_struct['info']['pieces']
        file_inx_sha = file_shas[piece_inx]

        # CHeck if SHA Value matches
        if file_inx_sha != curr_piece_sha:
            print("SHA hash doesn't  match")
            return
        else:
            # Else complete the current piece
            self.curr_piece_Complete(piece_inx, current_piece)

    # 
    def curr_piece_Complete(self, piece_inx, current_piece):

        # assigning zero to the index whose piece 
        # we received succesfully and storing the current piece
        self.torr.store_piece(piece_inx,current_piece)

        # Clearing peer's piece index
        for peer in self.torr.piece_request[piece_inx]:
            if peer.target_piece_inx == piece_inx:
                peer.set_target_piece_inx()

        # we are done with this piece
        self.torr.piece_request[piece_inx] = 1
        # Displaying download percentage
        self.display_download()
        self.peer.downloading()

        # If download complete --> end all connectiond
        if self.check_download_complete():
            self.torr.con_menu.end_loop()
            # Write the Data  
            self.write_data()
        else:
            return

    # Function to display download percentage
    def display_download(self):
        pieces_sum = 0
        for piece in self.complete:
            if piece:
                pieces_sum += 1
        pieces_len = len(self.complete)
        upto_complete = 100.0 * pieces_sum / pieces_len
        print('%02.1f%% complete' % upto_complete)

    # Function to check if download is completed
    def check_download_complete(self):
        for piece in self.complete:
            if piece:
                continue
            else:
                return 0
        return 1

    # Function to store data locally
    def write_data(self):
        # File is complete
        self.torr.complete = 1
        # now closing all peer connection
        self.close_peer_conn()

        # Write_data object
        WD = Write_data(self.torr, self.complete)

        # Write according to given file format
        if self.torr.meta_struct['info']['format'] == 'single file':
            WD.for_single_file()
        else:
            WD.for_multiple_file()

    # Function to close all peer connections
    def close_peer_conn(self):
        for peer in self.torr.peer_list:
            if peer.con:
                peer.con.Close_connection()
        return