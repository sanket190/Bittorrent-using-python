# bittorrent
Members  
[Rushikesh Kundkar](https://gitlab.com/RRkundkar777)  
[Sanket Chaudhary](https://gitlab.com/sanketchaudhari.in20)

**Description:**

1. A Python base BitTorrent client supporting concurrent peer connections and multiple simultaneous torrent downloads.
2. This project was an exercise of networking protocol called peer to peer protocol 

**Overview :**

- **1.main.py :** this file is like menu which will access functionallity

- **2.metainfo.py :** which is used to decode the bencoded .torrent file

- **3.tracker.py :** This file basically used for sending the http and udp request and getting the list of peers 

- **4.Config :** peer configurations

- **5.peer.py:** making handshake and requesting the peers for piece maintaining the all data  

- **6.Connection.py :**  making connections with multiple peers at same timee (for multiple connection using threading)

- **7.torrent.py :**  maintaining peers objects also use for rarest first statergy

- **8.torr_download.py :**  for handling the requested piece and chunks.

- **9.Write_data.py :**  after completing the whole data, to write that data into the files  




**Installation Set up:**

pip install -r requirements.txt

**To Run:**

python main.py FilePath



