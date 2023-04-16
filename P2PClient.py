import socket
import argparse
import threading
import hashlib
import time
import logging
import random
import sys
import os

#TODO: Implement P2PClient that connects to P2PTracker

# LOCK = threading.Lock()
logging.basicConfig(filename='logs.log', format='%(message)s', filemode='a')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# thread that listens to other clients
# sends an entire 'file' when there is a message "REQUEST_CHUNK"
def listen_thread(folder_path, clientPort):
    # this socket is important because it is going to use clientPort number
    # and the role as a server when 'GET_CHUNK_FROM' is send to clientSocket
    # then, thread switch will happen
    mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    mySocket.bind(('', clientPort))
    mySocket.listen(1)
    
    # open connection to receive information from other clients
    while True:
        try:
            connectionSocket, addr = mySocket.accept()

            request_message = connectionSocket.recv(4096).decode()
            print(request_message)

            if 'REQUEST_CHUNK' in request_message:
                request_index = request_message.split(',')[1]
                chunk_file = f'chunk_{request_index}'
                file_name = os.path.join(folder_path, chunk_file)
                # file_name = ''.join([folder_path, '/chunk_', request_index])

                # sizeof_file = os.path.getsize(file_name)
                # size_1MB = 1024 * 1024  # 1MB

                # sent_total = 0
                # with open(file_name, 'rb') as f:
                #     while sizeof_file > sent_total:
                #         file_contents = f.read(size_1MB)
                #         connectionSocket.sendall(file_contents)
                #         sent_total += len(file_contents)
                #         time.sleep(1)

                buffer_size = 262144    # 256KB
                with open(file_name, 'rb') as file:
                    while True:
                        file_contents = file.read(buffer_size)
                        if not file_contents:
                            break
                        connectionSocket.sendall(file_contents)
                        time.sleep(1)
                connectionSocket.close()

            elif request_message is None:
                print('no message')
                connectionSocket.close()
                time.sleep(1)
                continue
        except ConnectionResetError as e:
            print(e)


def search_client(folder_path, clientName, clientPort, trackerSocket, local_chunk, ipaddr):
    t1 = threading.Thread(target=listen_thread, args=(folder_path, clientPort, ))
    t1.start()

    print("In search method: ", local_chunk)
    num_of_chunks = int(local_chunk[len(local_chunk) - 1].split(',')[0])  # local_chunk = ['2,chunk_2', '3,chunk_3', '3,LASTCHUNK']
    missed_chunks = []
    for i in range(1, num_of_chunks + 1):
        missed_chunks.append(str(i))
    
    for i in range(len(local_chunk) - 1):
        missed_chunks.remove(local_chunk[i].split(',')[0])
    
    print(missed_chunks)

    # send my folder's available chunk to the tracker
    i, check = 0, 0
    # don't consider the last chunk part
    while i < len(local_chunk) - 1:
        content = local_chunk[i].split(',') # '2, chunk_2'
        chunk_idx, name = content[0], content[1]

        chunk_path = os.path.join(folder_path, name)
        
        print(chunk_path)
        # sizeof_file = os.path.getsize(chunk_path)

        # if sizeof_file >= 1024 * 1024:
        #     hash = get_hash(chunk_path, 2)
        # else:
        #     hash = get_hash(chunk_path, 1)

        hash = get_hash(chunk_path)
        
        message = ','.join(['LOCAL_CHUNKS', chunk_idx, hash, ipaddr, str(clientPort)])
        trackerSocket.send(message.encode())
        time.sleep(1)
        # logging
        logMessage = ','.join([clientName, message])
        logger.info(logMessage)

        i += 1
    

    # now all local chunks are sent. Now, it has to ask where the missing chunk is located
    i, check = 0, 0
    while len(missed_chunks) > 0:
        request = ','.join(['WHERE_CHUNK', missed_chunks[i]])

        if check == 0:
            trackerSocket.send(request.encode())
            time.sleep(1)
            check = 1

            # logging
            logMessage = ','.join([clientName, request])
            logger.info(logMessage)
        
        response = trackerSocket.recv(4096).decode()
        if response:
            if 'GET_CHUNK_FROM' in response:
                # Now, another thread should be invoked to role as a temporary server that connects to another client
                print(response)
                respIndex = response.split(',')[1]      # chunk_idx
                clientList = response.split(',')[3:]    # (prev_ipaddr, prev_port, ipaddr, port, ...)

                n = len(clientList) // 2
                rand_idx = None
                if n == 1:
                    rand_idx = 0
                else:
                    rand_list = [i for i in range(n*2) if i % 2 == 0]
                    rand_idx = random.choice(rand_list)
                
                connAddr, connPort = clientList[rand_idx], clientList[rand_idx + 1]

                # close socket to do client-server operation
                # this thread acts like a client
                ctcSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                ctcSocket.connect((connAddr, int(connPort)))
                print(connPort)

                request = ','.join(['REQUEST_CHUNK', respIndex])
                ctcSocket.send(request.encode())
                time.sleep(1)

                # logging
                logMessage = ','.join([clientName, request, connAddr, connPort])
                logger.info(logMessage)

                chunk_file = f'chunk_{respIndex}'
                required_file_name = os.path.join(folder_path, chunk_file)
                # required_file_name = ''.join([folder_path, '/chunk_', respIndex])
                # size_1MB = 1024 * 1024

                # write_count = 0
                buffer_size = 262144    # 256KB
                with open(required_file_name, 'wb') as f:
                    # sent_total = 0
                    while True:
                        # save file inside the folder
                        try:
                            file = ctcSocket.recv(buffer_size)
                            if not file:
                                print(clientName + ': cTc socket debug1')
                                break
                            f.write(file)
                            print(clientName + ': cTc socket debug0')
                            # sent_total += len(file)
                            # write_count += 1
                        except ConnectionResetError as e:
                            print("With large file", e)
                            break
                
                time.sleep(1)
                # close again
                ctcSocket.close()

                print(clientName + ': cTc socket debug2')

                # try updating the missed index
                missedIndex = missed_chunks[i]

                chunk_file = f'chunk_{missedIndex}'
                newPath = os.path.join(folder_path, chunk_file)
                # newPath = ''.join([folder_path, '/chunk_', missedIndex])
                print(newPath)
                missedHash = get_hash(newPath)
                update = ','.join(['LOCAL_CHUNKS', str(missedIndex), missedHash, ipaddr, str(clientPort)])
                trackerSocket.send(update.encode())
                time.sleep(1)

                # logging
                logMessage = ','.join([clientName, update])
                logger.info(logMessage)

                # delete the index from missed_chunk
                missed_chunks.remove(missed_chunks[i])
                
                # update local chunks from here
                check = 0
            
            elif 'CHUNK_LOCATION_UNKNOWN' in response:
                time.sleep(1)
                check = 0

                # If the server doesn't have the chunk, then ask another one
                i += 1

            # when the index is bigger than the length of the missing chunks
            if i >= len(missed_chunks):
                i = 0

        else:
            # periodically ask for chunk
            i += 1
            if i >= len(missed_chunks):
                i = 0
            print('CHUNK NOT FOUND YET')
            sys.stdout.flush()

            

def get_hash(filename):
    """"This function returns the SHA-1 hash
   of the file passed into it"""
    
    # make a hash object
    h = hashlib.sha1()
    buffer_size = 1024 * 8 # 8kb

    # open file for reading in binary mode
    with open(filename, 'rb') as file:

        # loop till the end of the file
        chunk = 0
        while chunk != b'':
            chunk = file.read(buffer_size)
            h.update(chunk)
    
    # return the hex representation of digest
    return h.hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-folder', type=str, required=True)
    parser.add_argument('-transfer_port', type=int, required=True)
    parser.add_argument('-name', type=str, required=True)

    args = parser.parse_args()

    curr_folder = args.folder
    folder_path = args.folder + '/local_chunks.txt'
    clientPort = args.transfer_port
    clientName = args.name

    ipaddr, trackerPort = 'localhost', 5100

    trackerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    trackerSocket.connect((ipaddr, trackerPort))

    with open(folder_path, 'r') as file:
        local_chunk = file.read().split('\n')  # ['2,chunk_2', '3,chunk_3', '3,LASTCHUNK']

    if local_chunk[-1] == '':
        local_chunk = local_chunk[:-1] # Sometimes it ends with '', not with 'X, LASTCHUNK'

    print("In main:", local_chunk)

    # thread to send message to tracker, and find missing chunks
    t = threading.Thread(target=search_client, args=(curr_folder, clientName, clientPort, trackerSocket, local_chunk, ipaddr, ))   ## CHECK IF I NEED TO CHANGE curr_folder -> folder_path
    t.start()

    
