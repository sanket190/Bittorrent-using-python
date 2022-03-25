# Script to decode the torrent metainfo file.

# Import required modules
import os
import copy
import hashlib
import bencodepy
import random

# The final metainfo passed to tracker request
metaInfo = {}

# for debugging
debug = False
megabyteFactor = 1048576

# Function to get raw bencoded metadata
def getRawFile(filename):
    if(debug):
        print(filename)
    with open(filename,'rb') as file:
        contents = file.read()
        return contents

# Function to process the raw torrent file
def getTorrentMetaInfo(bencodeData):
    # Check if the file is empty or not
    if not bencodeData:
        print("Error: File is empty")
    # Start decoding the data
    else:
        # decoding the bencoded data into an Ordered Dictionary
        metaData = bencodepy.decode(bencodeData)

        if(debug):
            print(type(metaData))

        # Get the string encoding format
        encoding = metaData.get(b'encoding')
        metaInfo['encoding'] = encoding

        if(debug):
            print(metaInfo['encoding'])

        # metaData contains announce variable of the dictionary 
        # which is the assigned the url of trackers
        announce = metaData.get(b'announce')
        metaInfo['announce'] = announce

        # If announceList present --> extract announce list
        if not announce:
            announceList = metaData.get(b'announce-list')
            metaInfo['announce_list'] = announceList
            metaInfo['announce'] = announceList[3]

        if(debug):
            print(metaInfo['announce'])

        # metaData also contains the fields creation date , comment , created by
        # and announced_list but we are ignoring this field because these are optional
        
        # the info dictionary of metainfo file
        info = metaData.get(b'info')

        # if(debug):
        #     print(info)

        # if(debug):
        #     print(bencodepy.encode(info))

        # encrypting the info using secure hash algorithm  
        # and were digest return encoded data in bytes
        infoHash = hashlib.sha1(bencodepy.encode(info)).digest()

        # Processing the information of the actual file
        infoData = processFileInfo(info)

        # Appending info data and hash
        metaInfo['info'] = infoData
        metaInfo['info_hash'] = infoHash

        return metaInfo

# Function to process the info dictionary
def processFileInfo(info):
    # The final info dictionary
    infoDict = {}

    # piece length is number of bytes in each piece
    infoDict['piece_length'] = info[b'piece length']

    if(debug):
        print(str(infoDict['piece_length']/megabyteFactor) + " MB")

    # String consisting of the concatenation of all 20-byte sha1 hash values
    # one per piece 
    Sha1_len = 20
    pieces = info[b'pieces']

    if(debug):
        print(type(pieces))

    # Splitting the "pieces" into the individual hashes of each piece
    piecesList = []
    for offset in range(0, len(pieces), Sha1_len):
        piecesList.append(pieces[offset:offset + Sha1_len]) 

    # Appending the pieces_list 
    infoDict['pieces'] = piecesList

    # if(debug):
    #     print(info_dict['pieces'])

    # Appending the name of the file
    name = info[b'name'].decode('utf-8')
    infoDict['name'] = name

    if(debug):
        print(infoDict['name'])

    # files is field which contains the keys .i.e length , md5sum, path
    # It is only non void if there are multiple files
    filesDict = info.get(b'files')

    # if(debug):
    #     print(files_dict)  

    # checking if the file single or there are multiple files
    if not filesDict:
        # Appending data for a single file
        infoDict['format'] = 'single file'
        infoDict['files'] = None  # Single File
        infoDict['length'] = info[b'length']

        if(debug):
            print(str(infoDict['length']/megabyteFactor) + " MB")

    else:
        # Appending data for multiple files
        infoDict['format'] = 'multiple file'
        infoDict['files'] = []
        
        # Extracting multiple files' data
        for file in filesDict:
            # path field containing one or more string which
            # represents path and filename which in bencoded
            Path = []

            # if(debug):
            #     print(file)
            #     print()
            #     print()
            #     print()

            # Joining the path
            for location in file[b'path']:
                Path.append(location.decode('utf-8'))

                # if(debug):
                #     print(location)

            # Creating the files dictionary
            infoDict['files'].append(
                {
                    'length': file[b'length'],
                    'path': os.path.join(*Path)
                }
            )

        if(debug):
            print(infoDict["files"])

        # Over all size of all files
        length = sum(file["length"] for file in infoDict['files'])
        infoDict['length'] = length

        if(debug):
            print(str(infoDict['length']/megabyteFactor) + " MB")

    return infoDict
