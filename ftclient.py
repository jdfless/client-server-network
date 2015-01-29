"""
Jonathan Flessner
flessnej@onid.oregonstate.edu
CS372
FTP Client Program
18 May 2014
"""
#References:
#https://docs.python.org/2/library/socket.html
#http://beej.us/guide/bgnet/output/html/singlepage/bgnet.html

#Extra credit attempted:
#This program can both upload and download files to/from the server. The files can be of any type.

import sys
import os
import socket

def usage():
	print "Usage: ftclient.py <flip> <server port> <port> <cmd> [file]"

def controlConnect(host, port):												#establish control connection with listening server
	try:
		p = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error as se:
		print "Socket couldn't be opened." 
		print "Socket error({0}): {1}".format(se.errno, se.strerror)
		sys.exit()
	try:
		p.connect((host, port))
	except socket.error as se:
		print "Connection couldn't be established." 
		print "Socket error({0}): {1}".format(se.errno, se.strerror)
		sys.exit()
	return p

def makeRequest(rBuf):														#send cmd over control to server
	p.sendall(cmd)				#send command line command
	check = p.recv(rBuf)		#receive response
	if check == '$invalid$':									#if cmd invalid, explain usage and shutdown
		print "Command not recognized by server."
		usage()
		print "Valid commands are: 'list', 'get', and 'send'."
		p.shutdown(2)
		p.close()
		sys.exit()
	return

def dataConnect(host, qport, backlog):										#prepare data connection with server
	try:
		dc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)		#set up listen socket
		dc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)	#set to allow reuse of address'
	except socket.error as se:
		print "Socket couldn't be opened." 
		print "Socket error({0}): {1}".format(se.errno, se.strerror)
		sys.exit()
	try:
		dc.bind((host, qport))									#bind to host and port
		dc.listen(backlog)										#listen for backlog connections
	except socket.error as se:
		dc.close()
		print "Socket couldn't bind or listen." 
		print "Socket error({0}): {1}".format(se.errno, se.strerror)
		sys.exit()
	return dc

def closedown(q, dc, p):													#close sockets/connections and exit
	q.shutdown(2)
	q.close()
	dc.close()
	p.shutdown(2)
	p.close()
	sys.exit()

def printList(q, rBuf):														#receive list from server and print
	dirList = q.recv(rBuf)
	print dirList

def getFile(q, rBuf, filename):												#get file from server
	q.sendall(filename)
	gfsize = q.recv(rBuf)
	if gfsize == '$nofile$':
		print "File does not exist on server."
		return
	gfsize = int(gfsize)						#cast str size to int
	download(filename, gfsize, q, rBuf)
	return

def download(filename, gfsize, q, rBuf):									#download file from server
	fd = os.open(filename, os.O_WRONLY|os.O_CREAT)			#open file as write only, create if doesn't exist
	if gfsize == 0:											#done if filesize is 0
		os.close(fd)
		print "Empty file " + filename + " downloaded from server."
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
	print "File " + filename + " downloaded from server."
	return

def sendFile(q, rBuf, filename):											#send file to server
	q.sendall(filename)
	fileExists = q.recv(rBuf)
	if fileExists == '$yesfile$':
		print "File exists on server."
		return
	sfsize = os.stat(filename).st_size	#get filesize
	q.sendall(str(sfsize))
	upload(filename, sfsize, q, rBuf)
	return

def upload(sendname, sfsize, q, rBuf):										#upload file to server
	if sfsize == 0:								#done if filesize is 0
		print "Empty file " + sendname + " added to server."
		return
	fd = os.open(sendname, os.O_RDONLY)			#open file as read only
	
	packets = 1									#packets to send
	if sfsize % rBuf == 0:
		packets = -1
	packets += (sfsize / rBuf)
	while packets > 0:
		stuff = os.read(fd, rBuf)
		q.send(stuff)
		packets -= 1
	os.close(fd)
	print "File " + sendname + " uploaded to server."
	return

#display error and exit for wrong cmd line use
if len(sys.argv) < 5:
	usage()
	sys.exit()

#set variables host, port, cmd, rBuf, filename
host = sys.argv[1]			#flip host
host += ".engr.oregonstate.edu"
port = int(sys.argv[2])		#port given on cmd line for control
qport = int(sys.argv[3])	#port given for data
cmd = sys.argv[4]
rBuf = 4096
backlog = 1
if len(sys.argv) == 6:		#only set filename if exists based cmd given (only get and send take filenames)
	filename = sys.argv[5]
	if cmd == 'get':
		if os.path.isfile(filename):
			print "Error, file already exists in client directory."
			sys.exit()
	elif cmd == 'send':
		if not os.path.isfile(filename):
			print "Error, file does not exist in client directory."
			sys.exit()
	else:
		print "Command '" + cmd + "' does not take a filename"
		usage()
		sys.exit()

#connect to listening server for control
p = controlConnect(host, port)				#establish control connection
makeRequest(rBuf)							#exit if bad request
dc = dataConnect(host, qport, backlog)		#setup and listen for data connection
p.sendall(str(qport))						#send qport as string to server
q, saddr = dc.accept()						#wait to accept data connection
#print "Data connection established."

#run functions based on already validated cmd
if cmd == 'list':
	printList(q, rBuf)
	closedown(q, dc, p)
elif cmd == 'get':
	getFile(q, rBuf, filename)
	closedown(q, dc, p)
elif cmd == 'send':
	sendFile(q, rBuf, filename)
	closedown(q, dc, p)
else:							#should never reach here, cmd already validated
	closedown(q, dc, p)



