"""
Jonathan Flessner
flessnej@onid.oregonstate.edu
CS372
FTP Server Program
18 May 2014
"""
#References:
#https://docs.python.org/2/library/socket.html
#http://beej.us/guide/bgnet/output/html/singlepage/bgnet.html
#http://ilab.cs.byu.edu/python/socket/echoserver.html  - for backlog idea

#Extra credit attempted:
#This program can both upload and download files to/from the client. The files can be of any type.

import sys
import os
import socket

def usage():
	print "Usage: ftserve.py <flip> <port>"								#explain usage

def flipExplain():														#explain flip formatting
	print "Enter only <flip>, do not enter .engr.oregonstate.edu."

def startServer(host, port, backlog):
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)			#set up listen socket
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)			#set to allow reuse of address'
	except socket.error as se:
		print "Socket couldn't be opened." 
		print "Socket error({0}): {1}".format(se.errno, se.strerror)
		sys.exit()
	try:
		s.bind((host, port))											#bind to host and port
		s.listen(backlog)												#listen for backlog connections
	except socket.error as se:
		s.close()
		print "Socket couldn't bind or listen." 
		print "Socket error({0}): {1}".format(se.errno, se.strerror)
		sys.exit()
	return s

def dataConnect(host, qport):											#establish data connection with client
	try:
		q = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error as se:
		print "Socket couldn't be opened." 
		print "Socket error({0}): {1}".format(se.errno, se.strerror)
		sys.exit()
	try:
		q.connect((host, qport))
	except socket.error as se:
		print "Connection couldn't be established." 
		print "Socket error({0}): {1}".format(se.errno, se.strerror)
		sys.exit()
	return q

def validCommand(cmd, p):												#test if client sent valid command
	cmdList = ['list', 'get', 'send']
	for i in cmdList:
		if cmd == i:
			p.sendall('$valid$')
			return True
	p.sendall('$invalid$')
	return False

def sendList(q):														#send directory listing to client
	cwd = os.getcwd()			#get current directory
	listDir = os.listdir(cwd)	#list files in current directory
	listDir.sort()				#sort alphabetically for convenience
	toSend = '\n'.join(listDir) #convert list to string seperated by newline
	print "Sent directory listing of " + str(sys.getsizeof(toSend)) + " bytes."
	q.sendall(toSend)

def sendFile(q, rBuf):													#send file to client
	sendname = q.recv(rBuf)
	if os.path.isfile(sendname):
		sfsize = os.stat(sendname).st_size		#get filesize
		q.sendall(str(sfsize))					#send filesize as string
		upload(sendname, sfsize, q, rBuf)
		print "File " + sendname + " downloaded by client."
		return
	else:
		q.sendall('$nofile$')					#send keyword since file doesn't exist on server
		return

def upload(sendname, sfsize, q, rBuf):									#helper function to send file to client
	if sfsize == 0:								#done if filesize is 0
		return
	fd = os.open(sendname, os.O_RDONLY)			#open file as read only
	
	packets = 1									#packets to send
	if sfsize % rBuf == 0:						#exception for full packet
		packets = -1 							#decrement size
	packets += (sfsize / rBuf)					#get number of packets needed
	while packets > 0:							#send all packets with loop
		stuff = os.read(fd, rBuf)
		q.send(stuff)
		packets -= 1
	os.close(fd)								#close file descriptor
	return

def getFile(q, rBuf):													#get file from client
	getname = q.recv(rBuf)
	if os.path.isfile(getname):
		q.sendall('$yesfile$')					#file already exists on server, can't be uploaded
		return
	else:
		q.sendall('$sendsize$')					#file not on server, get size
		gfsize = q.recv(rBuf)
		gfsize = int(gfsize)
		download(getname, gfsize, q, rBuf)
		print "File " + getname + " uploaded to server directory."
		return

def download(getname, gfsize, q, rBuf):									#helper function to get file from client
	fd = os.open(getname, os.O_WRONLY|os.O_CREAT)			#open file as write only, create if doesn't exist
	if gfsize == 0:											#done if filesize is 0
		os.close(fd)
		return
	packets = 1												#packets to receive
	if gfsize % rBuf == 0:
		packets = -1
	packets += (gfsize / rBuf)
	while packets > 0:
		stuff = q.recv(rBuf)
		os.write(fd, stuff)
		packets -= 1
	os.close(fd)
	return

#display error and exit for wrong cmd line use
if len(sys.argv) != 3:
	usage()
	sys.exit()
if len(sys.argv[1]) < 4 or len(sys.argv[1]) > 5:
	usage()
	flipExplain()
	sys.exit()

host = sys.argv[1]			#flip host
host += ".engr.oregonstate.edu"
port = int(sys.argv[2])		#port given by user on cmd line
rBuf = 4096					#size of packet too receive
backlog = 1 				#number of connections to keep waiting

#start server connection
s = startServer(host, port, backlog)

while 1:
	try:	
		p, caddr = s.accept()				#accept connect, returns new connection for data (q) and client address
		#print caddr, " control connection established"
		cmd = p.recv(rBuf)
		if not validCommand(cmd, p):
			p.shutdown(2)
			p.close()
			continue
		qport = p.recv(rBuf)
		try:
			qport = int(qport)
		except ValueError:
			p.shutdown(2)
			p.close()
			print "Invalid port sent by client. Control connection closed."
			continue
		q = dataConnect(host, qport)
		#print "Data connection established."
		#run functions based on cmd
		if cmd == 'list':
			sendList(q)
		elif cmd == 'get':
			sendFile(q, rBuf)
		elif cmd == 'send':
			getFile(q, rBuf)
		
		#close sockets
		q.shutdown(2)
		q.close()							
		p.shutdown(2)
		p.close()							
	
	except KeyboardInterrupt:				#close server on keyboard interrupt
		s.shutdown(2)
		s.close()
		print " <-- captured keyboard interrupt..."
		print "Sockets closed, server will close."
		sys.exit()