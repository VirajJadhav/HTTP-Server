from socket import *
import sys

serverSocket = socket(AF_INET, SOCK_STREAM)
serverPort = int(sys.argv[1])
serverSocket.bind(('', serverPort))
serverSocket.listen(1)
print("The Server is ready to receive")
while True:
    connectionSocket, addr = serverSocket.accept()
    # print("New request from ", addr)
    # print("Connection socket is ", connectionSocket)
    sentence = connectionSocket.recv(1024).decode()
    words = sentence.split()
    print("These are the words ", words)
    if(words[0] == "GET"):
        string = "HTTP/1.1 200 OK\n"
        string += "Date: Wed, 30 Sep 2020 09:35:34 GMT \n"
        string += "Server: Viraj's server/0.0.1 (Ubuntu)\n"
        string += "Content-Length: 303\n"
        string += "Connection: close\n"
        string += "Content-Type: text/html; charset=iso-8859-1\n\n"
        f = open("index.html")
        text = f.read()
        output = string + text
        connectionSocket.send(output.encode())
    connectionSocket.close()