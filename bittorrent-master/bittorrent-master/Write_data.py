# Writing file Locally

import os

class Write_data():
    def __init__(self,torr,piece_list):
        self.torr = torr
        self.piece_list = piece_list
        self.data = []
        self.piece_list_to_data()
        self.data = bytes(self.data)


    def piece_list_to_data(self):
        for x in self.piece_list:
            for y in x:
                self.data.append(y)



    def for_single_file(self):
        # spliting the path into head and tail
        head_tail = os.path.split(self.torr.meta_struct['info']['name'])
        filename = head_tail[1] # here tail is our filename
        curr_dir = os.getcwd()
        file_path = os.path.join(curr_dir,filename)
        with open(file_path,'wb') as file:
            file.write(self.data)
        print("File downloaded at location %s" %file_path)


    def for_multiple_file(self):
        curr_dir = os.getcwd()
        head_tail = os.path.split(self.torr.meta_struct['info']['name'])
        filename = head_tail[1]
        start =0
        for files in self.torr.meta_struct['info']['files']:
            file_path = os.path.join(curr_dir,files['path'])
            if not os.path.exists(file_path):
                os.makedirs(file_path)
            data = self.data[start:start+files['length']] # spliting the file data according to length
            file = open(file_path,'wb')
            file.write(data)
            start += files['length']

        print("files saved")



