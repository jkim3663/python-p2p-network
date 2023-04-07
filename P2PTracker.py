import socket
import threading
import sys
import logging
import time


#TODO: Implement P2PTracker
CLIENTS = []
CHECK_LIST = {}
CHUNK_LIST = {}
DATA = {}
ENTITIY_NAME = 'P2PTracker'

logging.basicConfig(filename='logs.log', format='%(message)s', filemode='a')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# 1. moves entries from the check_list to the chunk_list only when two or more P2PClients agree on the hash of the file chunk
# 2. when 2nd Client joins, tracker checks if both hash matches
# 3. if matches, move entry to chunklist
def store_chunk_info(content):
	content = content.split(',')

	chunk_idx = content[1]
	hash = content[2]
	ipaddr = content[3]
	port = content[4]

	if hash in CHECK_LIST:
		if chunk_idx in CHUNK_LIST:
			if hash == CHUNK_LIST[chunk_idx].split(',')[0]:
				value = CHUNK_LIST[chunk_idx] + ',' + ipaddr + port
				CHUNK_LIST[chunk_idx] = value
			else:
				CHECK_LIST[hash] += [chunk_idx, ipaddr, port]
		else:
			idx = None
			for i, x in enumerate(CHECK_LIST[hash]):
				if x == chunk_idx:
					idx = i
					break
			
			if idx is not None:
				check_idx = CHECK_LIST[hash][idx]
				print(check_idx == chunk_idx)
				prev_ipaddr, prev_port = CHECK_LIST[hash][idx + 1], CHECK_LIST[hash][idx + 2]
				value = hash + ',' + prev_ipaddr + ',' + prev_port + ',' + ipaddr + ',' + port
				CHUNK_LIST[chunk_idx] = value
			else:
				CHECK_LIST[hash] += [chunk_idx, ipaddr, port]
			# check_idx = CHECK_LIST[hash][0]
			# if chunk_idx == check_idx:
			# 	prev_ipaddr, prev_port = CHECK_LIST[hash][1], CHECK_LIST[hash][2]
			# 	value = hash + ',' + prev_ipaddr + ',' + prev_port + ',' + ipaddr + ',' + port
			# 	CHUNK_LIST[chunk_idx] = value
			# else:
			# 	CHECK_LIST[hash] += [chunk_idx, ipaddr, port]
	else:
		CHECK_LIST[hash] = [chunk_idx, ipaddr, port]

def client_thread(connectionSocket):
	while True: 
		try:
			sentence = connectionSocket.recv(4096).decode()
			contents = sentence.split(',')
			cmd = contents[0]
			if cmd == 'LOCAL_CHUNKS':
				store_chunk_info(sentence)
				# msg = 'chunk received'
				# connectionSocket.send(msg.encode())
				# time.sleep(1)
			elif cmd == 'WHERE_CHUNK':
				print('check list when where chunk called')
				print(CHECK_LIST)
				print('chunk list when where chunk called')
				print(CHUNK_LIST)

				chk_idx = contents[1]

				# when there is only one client, hash verification is impossible
				if len(CLIENTS) <= 1:
					msg = 'CHUNK_LOCATION_UNKNOWN' + ',' + chk_idx
					connectionSocket.send(msg.encode())
					time.sleep(1)

					# logging
					logMessage = ENTITIY_NAME + ',' + msg
					logger.info(logMessage)

					continue

				if chk_idx in CHUNK_LIST:
					# there should be additional verification checklist=>chunklist 
					# only values can be obtained from chunklist
					msg = 'GET_CHUNK_FROM' + ',' + chk_idx + ',' + CHUNK_LIST[chk_idx]
				else:
					msg = 'CHUNK_LOCATION_UNKNOWN' + ',' + chk_idx
				connectionSocket.send(msg.encode())
				time.sleep(1)
				
				# logging
				logMessage = ENTITIY_NAME + ',' + msg
				logger.info(logMessage)
				
			if not sentence:
				print('No sentence')
				sys.stdout.flush()
				# use continue to not kill the thread
				time.sleep(1)
				continue
		except ConnectionResetError as e:
			print('Client connection closed ' + e)
			break 
		except OSError as e:
			print(e)
			sys.stdout.flush()
			break
		

if __name__ == "__main__":
	host, port = 'localhost', 5100
	trackerPort = port

	trackerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	trackerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	# establish welcoming door
	trackerSocket.bind(('', trackerPort))
	# specifies the maximum number of queued connections
	trackerSocket.listen()

	while True:
		connectionSocket, addr = trackerSocket.accept()
		CLIENTS.append(connectionSocket)

		print(CLIENTS)

		# use a thread to handle multiple clients
		t = threading.Thread(target=client_thread, args=(connectionSocket,))
		t.start()
		print('running thread: ' + t.name)





