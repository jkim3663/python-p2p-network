import socket
import argparse
import threading
import hashlib
import time
import logging
import random
import sys


logging.basicConfig(filename='logs.log', format='%(message)s', filemode='a')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# thread function that is used to connect client to client directly
def connection_thread(connAddr, connPort, respIndex, folder_path, clientName, clientPort):
    # close socket to do client-server operation
    # this thread acts like a client
    mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mySocket.connect((connAddr, int(connPort)))
    print(connPort)

    request = 'REQUEST_CHUNK' + ',' + respIndex
    mySocket.send(request.encode())
    time.sleep(1)
                    
    # logging
    logMessage = clientName + ',' + request + ',' + connAddr + ',' + connPort 
    logger.info(logMessage)
    
    while True:
        # savce file inside the folder
        try:
            file = mySocket.recv(1048576)
            if not file:
                break
            
            with open(folder_path + '/chunk_' + respIndex, 'wb') as f:
                f.write(file)
        except ConnectionResetError as e:
            print(e)
            break
    
    # close again
    mySocket.close()


def search_client(folder_path, clientName, clientPort, trackerSocket, local_chunk, ipaddr):
    print(local_chunk)
    num_of_chunks = int(local_chunk[len(local_chunk) - 1].split(',')[0])
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
        content = local_chunk[i].split(',') # 2,chunk_2
        chunk_idx, name = content[0], content[1]
        print(folder_path + '/' + name)
        hash = get_hash(folder_path + '/' + name)
        
        message = 'LOCAL_CHUNKS' + ',' + chunk_idx + ',' + hash + ',' + ipaddr + ',' + str(clientPort)
        trackerSocket.send(message.encode())
        time.sleep(1)
        # logging
        logMessage = clientName + ',' + message
        logger.info(logMessage)
        
        i += 1
    
    # now all local chunks are sent. now it has to ask where the missing chunk is located
    i, check = 0, 0
    while i != len(missed_chunks):
        request = 'WHERE_CHUNK' + ',' + missed_chunks[i]
        
        if not check:
            trackerSocket.send(request.encode())
            time.sleep(1)
            check = 1

            # logging
            logMessage = clientName + ',' + request
            logger.info(logMessage)

        response = trackerSocket.recv(4096).decode()
        if response:
            if 'GET_CHUNK_FROM' in response:
                # Now, another thread should be invoked to role as a temporary server that connects to another client
                print(response)
                respIndex = response.split(',')[1]
                clientList = response.split(',')[3:]

                n = len(clientList) // 2
                rand_idx = None
                if n == 1:
                    rand_idx = 0
                else:
                    rand_list = [i for i in range(n) if i % 2 == 0]
                    rand_idx = random.choice(rand_list)
                
                connAddr, connPort = clientList[rand_idx], clientList[rand_idx + 1]

                t2 = threading.Thread(target=connection_thread, args=(connAddr, connPort, respIndex, folder_path, clientName, clientPort))
                t2.start()

                # try updating the missed index
                while True:
                    try:
                        missedIndex = missed_chunks[i]
                        missedHash = get_hash(folder_path + '/' + 'chunk_' + missedIndex)
                        update = 'LOCAL_CHUNKS' + ',' + missedIndex + ',' + missedHash + ',' + ipaddr + ',' + str(clientPort)
                        trackerSocket.send(update.encode())
                        time.sleep(1)

                        break
                    except FileNotFoundError as e:
                        time.sleep(0.5)
                # logging
                logMessage = clientName + ',' + update
                logger.info(logMessage)

                # update local chunks from here 
                check = 0 
                i += 1
            elif 'CHUNK_LOCATION_UNKNOWN' in response:
                time.sleep(1)
                check = 0
        else:
            # periodically ask for chunk 
            print('CHUNK NOT FOUND YET')
            sys.stdout.flush()
            # time.sleep(0.5)


def get_hash(filename):
   """"This function returns the SHA-1 hash
   of the file passed into it"""

   # make a hash object
   h = hashlib.sha1()

   # open file for reading in binary mode
   with open(filename,'rb') as file:

       # loop till the end of the file
       chunk = 0
       while chunk != b'':
           # read only 1024 bytes at a time
           chunk = file.read(1024)
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
        local_chunk = file.read().split('\n') # ['2,chunk_2', '3,chunk_3', '3,LASTCHUNK']


    if local_chunk[-1] == '':
        local_chunk = local_chunk[:-1]
    
    print(local_chunk)
        
    # thread to send message to tracker, and find missing chunks
    t = threading.Thread(target=search_client, args=(curr_folder, clientName, clientPort, trackerSocket, local_chunk, ipaddr, ))
    t.start()

    # this socket is important because it is going to use clientPort number 
    # and role as a server when 'GET_CHUNK_FROM' is sent to clientSocket
    # then, thread switch will happen 
    mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    mySocket.bind(('', clientPort))
    mySocket.listen(1)

    # open conection to reeive information from other clients
    while True:
        connectionSocket, addr = mySocket.accept()

        request_message = connectionSocket.recv(4096).decode()
        print(request_message)

        if 'REQUEST_CHUNK' in request_message:
            request_index = request_message.split(',')[1]
            file_name = curr_folder + '/chunk_' + request_index
            with open(file_name, 'rb') as f:
                file_contents = f.read()
            
            connectionSocket.sendall(file_contents)
            time.sleep(1)
        elif request_message is None:
            print('no message')
            time.sleep(1)
            continue
