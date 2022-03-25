# The client configuration file

import math

CONFIG = {
    # unique id for client
    'peer_id': b'QQ-0000-000000000000', 
    # portion of data that a client requests from the peer
    'block_length': int(math.pow(2,14)), 
    # numwant
    'max_peers': 10 
}