from socket import *
import threading
import sys

totalClientConnections = []


def eachClientThread(clientConnection=None):
    global totalClientConnections
    totalClientConnections.append(clientConnection)
    while True:
        try:
            connectionData = clientConnection.recv(1024).decode()

            connectionData = connectionData.split("\n")
            print(dict(connectionData))
            string = "HTTP/1.1 200 OK\n"
            string += "Date: Wed, 30 Sep 2020 09:35:34 GMT \n"
            string += "Server: Viraj's server/0.0.1 (Ubuntu)\n"
            string += "Content-Length: 303\n"
            string += "Connection: close\n"
            string += "Content-Type: text/html; charset=iso-8859-1\n\n"
            # for data in connectionData:
            #     if data == "GET":
            #         f = open("index.html")
            #         text = f.read()
            #         output = string + text + "\n"
            output = string
            clientConnection.send(output.encode())
            break

        except:
            # index = totalClientConnections.index(clientConnection)
            # print("This is the index ", index)
            totalClientConnections.remove(clientConnection)
            clientConnection.close()
            break


def startServer(serverSocket=None):
    while True:
        clientConnection, addr = serverSocket.accept()
        # print("New request from ", addr)
        # print("Connection socket is ", connectionSocket)
        forEachConnection = threading.Thread(
            target=eachClientThread, args=(clientConnection, ))
        forEachConnection.start()
    # serverSocket.close()


def establishConnection(argv=None):
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverPort = int(argv[1])
    serverSocket.bind(('', serverPort))
    serverSocket.listen()
    return serverSocket


if __name__ == "__main__":
    serverSocket = establishConnection(sys.argv)
    print("The Server is ready to receive")
    startServer(serverSocket)
