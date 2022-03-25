# Driver code for Bittorrent client.

# Import Modules
import sys
from metainfo import getTorrentMetaInfo,getRawFile
from tracker import clientRequest
from connection import con_menu
from torrent import Client_Torrent

# The Driver Code
if __name__ == '__main__':
    
    # Select filename and extract torrent info
    filename = sys.argv[1]
    contents = getRawFile(filename)
    metainfo = getTorrentMetaInfo(contents)

    # Create 'torr' object
    torr = Client_Torrent(metainfo,con_menu)

    # Send request to tracker
    clientRequest(torr,metainfo,metainfo['announce'])
    
    # Connecting to the peers for data transfer
    torr.torrent_conn()
    con_menu.start_loop()