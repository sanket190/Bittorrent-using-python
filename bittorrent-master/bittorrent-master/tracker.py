# Script to send request to tracker and record the response

# Import required modules
import struct
import requests
import bencodepy
import socket

# Configuration file
from config import CONFIG

# For debugging
debug = False

# Connecting to tracker

# Function to send announce request to the tracker
def clientRequest(torrent, metainfo, announce):
    # If torrent contains multiple announce urls --> get the first one
    if 'announce_list' in metainfo:
        str_ann = str(announce[0])
    else:
        str_ann = str(announce)

    # Protocol name,url,flag and port
    protocol = str_ann[2:5]
    url = ''
    port = ''
    # Status for identifying parts of url
    url_status = 0

    # Extracting the URL and Port from announce string
    for char in str_ann:
        if char == '/' and url_status != 2:
            url_status = 1
        elif char == ':' and url_status == 1:
            url_status = 2
        elif url_status == 2 and char.isdigit():
            port += char
        elif url_status == 1:
            url += char

    if(debug):
        print(__name__ + ".py")
        print("Port: ", port)
        print("Announce url:", url)
        print("Protocol: ",protocol)
        print()

    # If protocol is udp --> use UDP
    if protocol == 'udp':
        # UDP Socket
        S = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Get Ip address by hostname
        host = socket.gethostbyname(url)
        # the extracted port
        port = int(port)

        connection_id = 0x41727101980
        action = 0

        # Any random transcation ID
        transaction_id = 5400
        
        # Constructing the connection request
        connect_request = struct.pack(">QLL",connection_id,action,transaction_id)
        # Making request
        S.sendto(connect_request,(host,port))

        # Recording the response
        resp1 = S.recv(16)
        action, transaction_Id, connection_id = struct.unpack(">LLQ",resp1)

        if(debug):
            print(__name__ + ".py")
            print("action: ",action)
            print("transaction id: ",transaction_Id)
            print("connection_id: ",connection_id)
            print()

        # Info Hash and peer id from metainfo
        info_hash= metainfo['info_hash']
        peer_id =CONFIG['peer_id']
        
        port_p = 64173  # range (6881,6889)
        uploaded = 0    # total amount of upload
        downloaded = 0  # total amount of download
        
        # Initially all bytes are left to be downloaded
        left = int(metainfo['info']['length'])

        # Event --> started,stopped or completed
        event = 2
        ip = 0
        key = 0
        num_want = 10
        action = 1
        
        # Constructing the tracker request
        send_data = struct.pack(">QLL20s20sQQQLLLLH", connection_id, action,transaction_Id,info_hash, peer_id, downloaded,left,uploaded,event,ip,key,num_want,port_p)
        
        # Sending request
        S.sendto(send_data, (host, port))
        
        # Recording the response
        resp2 = S.recv(1024)

        # Decoding the response
        resp_dict = {}
        action, transaction_id, intervel, leechers, seeders = struct.unpack("!LLLLL", resp2[:20])

        if(debug):
            print(__name__ + ".py")
            print("action: ",action)
            print("transaction_id: ",transaction_id)
            print("interval: ",intervel)
            print("leechers: ",leechers)
            print("seeders: ",seeders)
            print()

        # extract ip and port addresses and call make_peerlist
        udpTrackerResp(torrent,resp2)
        resp_dict['action'] = action
        resp_dict['transaction_id'] = transaction_id
        resp_dict['interval'] = intervel
        resp_dict['leechers'] = leechers
        resp_dict['seeders'] = seeders

        # if(debug):
        #     print(resp_dict)

    # else --> use http
    else:
        resp = requests.get(announce, {
            'info_hash': metainfo['info_hash'],
            'peer_id': CONFIG['peer_id'],
            'port': 6883,  # range (6881,6889)
            'uploaded': '0',  # total amount of upload
            'downloaded': '0',  # total amount of downloud
            'left': str(metainfo['info']['length']),
        })
        # extract ip and port addresses and call make_peerlist
        httpTrackerResp(torrent, resp)
    return

################# Utility functions for httpTrackerResp and updTrackerResp ##############

# Function to construct IP from UDP response
def constructIp(ip_tuple):
    s=''
    for i in ip_tuple:
        s+=str(i)
        s+='.'
    return s[:len(s)-1]

# Function to construct port from UDP response
def constructPort(port_tuple):
    s=''
    for i in port_tuple:
        s+=str(i)
    return int(s)

# Function to construct the response dictionary from http response
def decodeResponse(trackResp):
    respDict = {}

    # Extracting failure reason,interval,complete,tracker_id and peers from resp

    # checking if there is failure in resp
    if b'failure reason' in trackResp:
        print(trackResp[b'failure reason'].decode('utf-8'))

    # interval that the client should wait before 
    # sending the next request to the tracker
    respDict['interval'] = int(trackResp[b'interval'])

    if(debug):
        print(__name__ + ".py")
        print(respDict['interval'])
        print()

    # number of peers i.e  seeders (integer)
    if b'complete' in trackResp:
        respDict['complete'] = int(trackResp[b'complete'])
    else:
        respDict['complete'] = None
    
    if(debug):
        print(__name__ + ".py")
        print(respDict['complete'])
        print()

    # numbers of non seeder peers
    if b'incomplete' in trackResp:
        respDict['incomplete'] = int(trackResp[b'incomplete'])
    else:
        respDict['complete'] = None
    
    if(debug):
        print(__name__ + ".py")
        print(respDict['incomplete'])
        print()

    # A string tha the client should send back to its next announcement
    if b'tracker_id' in trackResp:
        respDict['tracker_id'] = int(trackResp[b'tracker_id'])
    else:
        respDict['tracker_id'] = None
    
    if(debug):
        print(__name__ + ".py")
        print(respDict['tracker_id'])
        print()

    # The peers (contain ip address and port no.)
    peers = trackResp[b'peers']

    if(debug):
        print(__name__ + ".py")
        print("Peers are:",peers)

    # Appending the peer list
    respDict['peers'] = decodePeerList(peers)

    return respDict

# Function to decode peer list for http response
def decodePeerList(peers):
    peerList = {}
    # checking if peer list uses dict model or binary model 
    # and decoding them accordingly
    if isinstance(peers, list):
        peerList = decode_for_dict_model(peers)
    elif isinstance(peers, bytes):
        peerList = decode_for_binary_model(peers)
    else:
        print('Error: peerList Not formatable ')
    return peerList

# Function extract IP,port and peer_id for dictionary model 
# Returns formatted peer list
def decode_for_dict_model(list_peers):
    peer_list = []
    for peer in list_peers:
        peer_dict = {}
        peer_dict['ip'] = peer[b'ip'].decode('utf-8')
        peer_dict['port'] = peer[b'port']
        peer_dict['peer_id'] = peer[b'peer id']
        peer_list.append(peer_dict)

    return peer_list

# Function extract IP,port and peer_id for binary model 
# Returns formatted peer list
def decode_for_binary_model(bytes_peers):
    # binary model size
    # IP --> 4 chars
    # Port --> one Int
    no_of_bytes = '!BBBBH'
    byte_size = struct.calcsize(no_of_bytes)

    if(debug):
        print(__name__ + ".py")
        print(byte_size)
        print()

    # checking the resp binary model contain 6 bytes or not
    if len(bytes_peers) % byte_size != 0:
        print('Error: Invalid length')
    
    peers = []
    # extracting the peers
    for i in range(0, len(bytes_peers), byte_size):
        peers.append(struct.unpack_from(no_of_bytes, bytes_peers, offset=i))

    list_peers = []
    # basically peer has 4 byte ip addr and 2 byte of port number
    for k in peers:
        peer_dict = {}
        peer_dict['ip'] = '%d.%d.%d.%d' % k[:4]
        peer_dict['port'] = int(k[4])
        list_peers.append(peer_dict)

    if(debug):
        print(__name__ + ".py")
        print(list_peers)
        print()
    return list_peers

##########################################################################################

# Function to record tracker response in udp
def udpTrackerResp(torrent,resp):
    # Starting from Ip address
    res = resp[20:]
    peer_list = []
    i = 0

    # Getting Ip and Ports
    while i < len(res):
        peer_dict ={}
        # Extracting Ip and port
        _ip = struct.unpack("!BBBB",res[i:i+4])
        _port = struct.unpack("!H",res[i+4:i+6])

        peer_dict['ip'] = constructIp(_ip)
        peer_dict['port'] = constructPort(_port)
        
        peer_list.append(peer_dict)
        i += 6

    if(debug):
        print(__name__ + ".py")
        print(peer_list)
        print()

    # calling torrent.make_peerlist
    for peer_d in peer_list:
        if peer_d['ip'] and peer_d['port'] > 0:
            torrent.make_peerlist(peer_d)

# Function to record tracker's response
def httpTrackerResp(torrent, http_resp):
    # The tracker responds with "text/plain" document 
    # consisting of a bencoded dictionary
    trackResp = bencodepy.decode(http_resp.text.encode('latin-1'))

    if(debug):
        print(__name__ + ".py")
        print(trackResp)
        print()

    # Constructing the response in form of dictionary
    respDict = decodeResponse(trackResp)
    peer_list = respDict['peers']

    # calling torrent.make_peerlist for single peers
    if len(peer_list) == 2:  
        torrent.make_peerlist(peer_list)
        return

    # calling torrent.make_peerlistfor multiple peers
    for peer_d in peer_list:
        if peer_d['ip'] and peer_d['port']>0:
            torrent.make_peerlist(peer_d)
    return