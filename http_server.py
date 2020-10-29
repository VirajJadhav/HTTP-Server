from socket import *
import threading
import sys
from datetime import datetime, timezone
from email.utils import formatdate
import os
import json
# import shutil

# default port
PORT = 4000
totalClientConnections = []
# filePath = "/home/viraj007/Semester 5/CN/Project/final/ResponseFiles/"
filePath = "ResponseFiles"
STATUSCODE = None
imageFileExtensions = [".png", ".jpeg", ".jpg",
                       ".ico", ".webp", ".apng", ".gif", ".bmp", ".svg"]
Response = {
    "Date": "",
    "Server": "Delta-Server/0.0.1 (Ubuntu)",
    "Connection": "close",
    "Content-Language": "en-US",
    "Last-Modified": ""
    # "Status": STATUSCODE str()
}


def switchStatusCode(code=None):
    codeTable = {
        200: " 200 OK",
        201: " 201 Created",
        304: " 304 Not Modified",
        400: " 400 Bad Request",
        404: " 404 Not Found",
        501: " 501 Not Implemented",
        505: " 505 HTTP Version Not Supported",
    }
    return codeTable.get(code, " 400 Bad Request")


def switchContentType(contentType=None):
    contentTable = {
        "txt": "text/plain",
        "html": "text/html",
        "php": "text/html",
        "pdf": "application/pdf",
        "csv": "text/csv",
        "apng": "image/apng",
        "bmp": "image/bmp",
        "gif": "image/gif",
        "ico": "image/x-icon",
        "png": "image/png",
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
        "webp": "image/webp",
        "svg": "image/svg+xml",
        "json": "application/json",
        "js": "application/javascript"
    }
    return contentTable.get(contentType, "image/") + "; charset=utf-8"


def httpDateFormat(Ltime=False):
    return str(formatdate(timeval=None, localtime=Ltime, usegmt=True))


def getLastModifiedTime(path=""):
    lastModified = ""
    try:
        msecs = os.path.getmtime(path)
    except Exception as error:
        msecs = 0
        # writeErrorLog("error", error)
    lastModified = datetime.fromtimestamp(
        msecs, timezone.utc).strftime("%a, %d %b %Y %H:%M:%S") + " GMT"
    return lastModified


def writeErrorLog(Code="", Error=""):
    date = httpDateFormat(True)
    pid = str(os.getpid())
    tid = str(threading.current_thread().ident)
    log = "[" + date + "]" + " "
    log += "[core: " + Code + "]" + " "
    log += "[pid " + pid + ":tid " + tid + "]" + " "
    log += str(Error) + "\n"
    try:
        with open("LogFiles/error.log", "a") as outputFile:
            outputFile.write(log)
    except Exception as e:
        with open("error.log", "a") as outputFile:
            outputFile.write(log)


def writeAccessLog(requestedMethod="", httpVersion="", requestedPath="", responseBodySize="-", restHeaders={}):
    global STATUSCODE
    date = httpDateFormat(True)
    log = "[" + date + "]" + " "
    log += "\"" + requestedMethod + " " + \
        requestedPath + " " + httpVersion + "\"" + " "
    log += str(STATUSCODE) + " "
    log += str(responseBodySize) + " "
    if "Referer" in restHeaders:
        log += "\"" + restHeaders["Referer"].lstrip() + "\"" + " "
    else:
        log += "\"-\"" + " "
    if "User-Agent" in restHeaders:
        log += "\"" + restHeaders["User-Agent"].lstrip() + "\""
    else:
        log += "\"-\"" + " "
    log += "\n"
    try:
        with open("LogFiles/access.log", "a") as outputFile:
            outputFile.write(log)
    except Exception as error:
        # writeErrorLog("error", error)
        pass


def validateRequest(requestedMethod="", httpVersion="", restHeaders={}):
    global STATUSCODE, Response
    finalFile = ""
    response = ""
    fileExtension = "html"
    Response["Date"] = httpDateFormat()
    if requestedMethod == None:
        return response, False
    if requestedMethod not in ["GET", "POST", "PUT", "DELETE", "HEAD"]:
        STATUSCODE = 501
        httpVersion = "HTTP/1.1"
        response = httpVersion + \
            switchStatusCode(STATUSCODE) + "\r\n"
        Response["Content-Length"] = "0"
        for key, value in Response.items():
            response += key + ": " + value + "\r\n"
        response = response.encode()
        return response, False
    elif httpVersion != "HTTP/1.1":
        STATUSCODE = 505
        response = "HTTP/1.1" + switchStatusCode(STATUSCODE) + "\r\n"
        finalFile = "<!DOCTYPE html><html><head><title>Delta-Server</title></head><body><h1>505</h1><h2>HTTP Version Not Supported</h2></body></html>"
        Response["Content-Type"] = switchContentType(fileExtension)
        Response["Content-Length"] = str(len(finalFile))
        for key, value in Response.items():
            response += key + ": " + value + "\r\n"
        if requestedMethod != "HEAD":
            response += "\r\n" + finalFile
        response = response.encode()
        return response, False
    elif "Host" not in restHeaders:
        STATUSCODE = 400
        finalFile = "<!DOCTYPE html><html><head><title>Delta-Server</title></head><body><h1>400</h1><h2>Server received a Bad Request</h2></body></html>"
        response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
        Response["Content-Type"] = switchContentType(fileExtension)
        Response["Content-Length"] = str(len(finalFile))
        for key, value in Response.items():
            response += key + ": " + value + "\r\n"
        if requestedMethod != "HEAD":
            response += "\r\n" + finalFile
        response = response.encode()
        return response, False
    return response, True


def parseRequestValueData(value=None):
    tvalue = value.split("%")
    if "+" in tvalue[0]:
        value = tvalue[0].replace("+", " ")
    else:
        value = tvalue[0]
    if len(tvalue) > 1:
        for i in range(len(tvalue)):
            if "+" in tvalue[i]:
                value += tvalue[i].replace("+", " ")
            try:
                bytesData = bytes.fromhex(
                    tvalue[i][:2])
                value += bytesData.decode("ASCII") + tvalue[i][2:]
            except Exception as error:
                # writeErrorLog("debug", error)
                pass
    return value


def getParsedData(connectionData=None):
    parsedData = connectionData.split("\r\n")
    headerEndCount = 0
    requestedMethod = None
    requestedPath = ""
    httpVersion = None
    requestBody = {}
    restHeaders = dict()
    firstLine = parsedData[0].split()
    if len(firstLine) == 3:
        requestedMethod, requestedPath, httpVersion = firstLine
    elif len(firstLine) == 2:
        requestedMethod = firstLine[0]
        requestedPath = firstLine[1]
    elif len(firstLine) == 1:
        requestedMethod = firstLine[0]
    for data in parsedData[1:]:
        headerEndCount += 1
        try:
            key, value = data.split(":", 1)
            restHeaders[key] = value
        except Exception as error:
            # writeErrorLog("debug", error)
            break
    if requestedMethod == "GET" or requestedMethod == "HEAD":
        pass
    elif requestedMethod == "POST" or requestedMethod == "PUT":
        if "application/x-www-form-urlencoded" in restHeaders["Content-Type"]:
            tempBody = parsedData[headerEndCount + 1].split("&")
            for tbody in tempBody:
                try:
                    key, value = tbody.split("=")
                    requestBody[key] = parseRequestValueData(value)
                except Exception as error:
                    # writeErrorLog("debug", error)
                    pass
        elif "text/plain" in restHeaders["Content-Type"]:
            reqBody = parsedData[headerEndCount + 1:]
            for body in reqBody:
                try:
                    key, value = body.split("=")
                    requestBody[key] = value
                except Exception as error:
                    # writeErrorLog("debug", error)
                    pass
        elif "multipart/form-data" in restHeaders["Content-Type"]:
            # reqBoundary = restHeaders["Content-Type"].split("boundary=")[1]
            reqBody = parsedData[headerEndCount + 1:]
            for i in range(1, len(reqBody) - 4):
                if ";" in reqBody[i]:
                    try:
                        tbody = reqBody[i].split(";")
                        if len(tbody) == 2:
                            tkey = tbody[1].split("name=")[
                                1].strip("\"")
                            requestBody[tkey] = reqBody[i + 2]
                        elif len(tbody) == 3:
                            tkey = tbody[2].split("filename=")[1].strip("\"")
                            requestBody[tkey] = str(reqBody[i + 3])
                            requestBody["filename"] = tkey
                    except Exception as error:
                        # writeErrorLog("debug", error)
                        pass
    return requestedMethod, requestedPath, httpVersion, restHeaders, requestBody


def getValidFilePath(requestedPath=""):
    global filePath, STATUSCODE
    requestedPath = str(requestedPath)
    if os.path.isdir(filePath + requestedPath):
        if requestedPath.endswith(('/')):
            return filePath + requestedPath + "index.html"
        else:
            return filePath + requestedPath + "/index.html"
    elif os.path.isfile(filePath + requestedPath):
        return filePath + requestedPath
    else:
        STATUSCODE = 404
        return filePath + "/not_found.html"


def getRequestedFile(requestedPath="", fileMode=""):
    global filePath, STATUSCODE
    finalExtension = ""
    try:
        if os.path.isfile(filePath + requestedPath):
            fileExtension = requestedPath.split(".")[-1]
        else:
            fileExtension = "html"
    except Exception as error:
        # writeErrorLog("debug", error)
        pass
    try:
        newRequestedPath = getValidFilePath(requestedPath)
    except Exception as error:
        # writeErrorLog("debug", error)
        pass
    lastModified = getLastModifiedTime(newRequestedPath)
    # print("FILE REPRESENTATIONS BEFORE RETURNING: ",
    #       newRequestedPath, fileExtension, lastModified)
    return newRequestedPath, fileExtension, lastModified


def handleGETRequest(httpVersion="", restHeaders={}, requestedPath=""):
    global STATUSCODE, imageFileExtensions, filePath, Response
    finalFile = response = ""
    fileExtension = "html"
    responseBodySize = "-"
    Response["Date"] = httpDateFormat()
    STATUSCODE = 200
    # print("REST HEADERS: ", restHeaders)
    if requestedPath.endswith(tuple(imageFileExtensions)):
        newRequestedPath, fileExtension, lastModified = getRequestedFile(
            requestedPath, "rb")
        if STATUSCODE != 404 and "If-Modified-Since" in restHeaders and restHeaders["If-Modified-Since"].lstrip() == lastModified:
            STATUSCODE = 304
            response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
            if "Content-Type" in Response:
                del Response["Content-Type"]
            if "Content-Length" in Response:
                del Response["Content-Length"]
            if "Last-Modified" in Response:
                del Response["Last-Modified"]
            for key, value in Response.items():
                response += str(key) + ": " + str(value) + "\r\n"
            response = response.encode()
        else:
            try:
                requestedFile = open(newRequestedPath, "rb")
                with requestedFile:
                    finalFile = requestedFile.read()
            except Exception as error:
                # writeErrorLog("error", error)
                pass
            response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
            Response["Content-Type"] = switchContentType(fileExtension)
            Response["Content-Length"] = str(len(finalFile))
            Response["Last-Modified"] = lastModified
            for key, value in Response.items():
                response += str(key) + ": " + str(value) + "\r\n"
            response += "\r\n"
            response = response.encode() + finalFile
    else:
        newRequestedPath, fileExtension, lastModified = getRequestedFile(
            requestedPath, "r")
        if STATUSCODE != 404 and "If-Modified-Since" in restHeaders and restHeaders["If-Modified-Since"].lstrip() == lastModified:
            STATUSCODE = 304
            response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
            if "Content-Type" in Response:
                del Response["Content-Type"]
            if "Content-Length" in Response:
                del Response["Content-Length"]
            if "Last-Modified" in Response:
                del Response["Last-Modified"]
            for key, value in Response.items():
                response += str(key) + ": " + str(value) + "\r\n"
        else:
            try:
                requestedFile = open(newRequestedPath, "r")
                with requestedFile:
                    finalFile = requestedFile.read()
            except Exception as error:
                # writeErrorLog("error", error)
                pass
            response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
            Response["Content-Type"] = switchContentType(fileExtension)
            Response["Content-Length"] = str(len(finalFile))
            Response["Last-Modified"] = lastModified
            for key, value in Response.items():
                response += str(key) + ": " + str(value) + "\r\n"
            response += "\r\n" + finalFile
            responseBodySize = Response["Content-Length"]

        # print("RESPONSE BEFORE ENCODING: ", response)

        response = response.encode()

    writeAccessLog("GET", httpVersion, requestedPath,
                   responseBodySize, restHeaders)
    return response


def handlePOSTRequest(httpVersion="", restHeaders={}, requestedPath="", requestBody={}):
    global Response, STATUSCODE, filePath
    finalFile = "<!DOCTYPE html><html><head><title>POST</title></head><body><h1>POST Success</h1></body></html>"
    response = ""
    fileExtension = "html"
    responseBodySize = "-"
    Response["Date"] = httpDateFormat()
    STATUSCODE = 201
    if "filename" in requestBody:
        # tName = requestBody["filename"].split(".")
        resultFile = requestBody["filename"]
        # resultFile = ".".join(tName[0:-1]) + "(Server)." + tName[-1]
        try:
            with open("ClientFiles/" + resultFile, "a") as writeFile:
                writeFile.write(requestBody[requestBody["filename"]])
        except Exception as error:
            # writeErrorLog("error", error)
            pass
        del requestBody[requestBody["filename"]]
    newPostData = "POST Date: " + Response["Date"] + "\n" + "POST DATA:\n"
    for key, value in requestBody.items():
        newPostData += "\t" + str(key) + " = " + str(value) + "\n"
    newPostData += "\n" + "#"*60 + "\n\n"
    # Response["Content-Location"] = requestedPath
    try:
        with open(filePath + "/server_data.txt", "a") as outputFile:
            outputFile.write(newPostData)
    except Exception as error:
        # writeErrorLog("error", error)
        pass
    response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
    Response["Content-Type"] = switchContentType(fileExtension)
    Response["Content-Length"] = str(len(finalFile))
    for key, value in Response.items():
        response += key + ": " + value + "\r\n"
    response += "\r\n" + finalFile
    response = response.encode()
    responseBodySize = Response["Content-Length"]
    writeAccessLog("POST", httpVersion, requestedPath,
                   responseBodySize, restHeaders)
    return response


def handleHEADRequest(httpVersion="", restHeaders={}, requestedPath=""):
    global STATUSCODE, imageFileExtensions, filePath, Response
    response = ""
    fileExtension = "html"
    responseBodySize = "-"
    try:
        if os.path.isfile(filePath + requestedPath):
            fileExtension = requestedPath.split(".")[-1]
    except Exception as error:
        # writeErrorLog("debug", error)
        pass
    Response["Date"] = httpDateFormat()
    Response["Content-Type"] = switchContentType(fileExtension)
    STATUSCODE = 200
    if requestedPath.endswith(tuple(imageFileExtensions)):
        path = getValidFilePath(requestedPath)
        if path.endswith(('not_found.html')):
            STATUSCODE = 404
        response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
        Response["Content-Length"] = str(os.path.getsize(path))
    else:
        path = getValidFilePath(requestedPath)
        if path.endswith(('not_found.html')):
            STATUSCODE = 404
        response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
        Response["Content-Length"] = str(os.path.getsize(path))
    for key, value in Response.items():
        response += key + ": " + value + "\r\n"
    response += "\r\n"
    response = response.encode()
    responseBodySize = Response["Content-Length"]
    writeAccessLog("HEAD", httpVersion, requestedPath,
                   responseBodySize, restHeaders)
    return response


def handlePUTRequest(httpVersion="", restHeaders={}, requestedPath="", requestBody={}):
    global Response, STATUSCODE
    finalFile = "<!DOCTYPE html><html><head><title>PUT</title></head><body><h1>PUT Success</h1></body></html>"
    response = ""
    fileExtension = "html"
    responseBodySize = "-"
    Response["Date"] = httpDateFormat()
    STATUSCODE = 200
    path = "dump.txt"
    fileDataOutput = ""
    if not os.path.exists(requestedPath) and requestedPath != "/":
        STATUSCODE = 201
        sep = requestedPath.split("/")
        expectedFile = sep[-1].split(".")
        if len(expectedFile) > 1:
            if sep[0] == "":
                path = "/".join(sep[1:-1])
            else:
                path = "/".join(sep[:-1])
            try:
                os.makedirs(path)
            except Exception as error:
                # writeErrorLog("error", error)
                pass
            path += "/" + sep[-1]
        else:
            try:
                os.makedirs("/".join(sep))
            except Exception as error:
                # writeErrorLog("error", error)
                pass
            path += "/dump.txt"
    if "filename" in requestBody:
        resultFile = requestBody["filename"]
        newPath = "/".join(path.rsplit("/", 1)) + "/"
        try:
            with open(newPath + resultFile, "a") as writeFile:
                writeFile.write(requestBody[requestBody["filename"]])
        except Exception as error:
            # writeErrorLog("error", error)
            pass
        # fileDataOutput = requestBody[requestBody["filename"]]
        del requestBody[requestBody["filename"]]
    # fileDataOutput += "\n"
    for key, value in requestBody.items():
        fileDataOutput += str(key) + " = " + str(value) + "\n"
    fileDataOutput += "\n"
    try:
        with open(path, "w") as outputFile:
            outputFile.write(fileDataOutput)
    except Exception as error:
        # writeErrorLog("error", error)
        pass
    response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
    Response["Content-Type"] = switchContentType(fileExtension)
    Response["Content-Length"] = str(len(finalFile))
    for key, value in Response.items():
        response += key + ": " + value + "\r\n"
    response += "\r\n" + finalFile
    response = response.encode()
    responseBodySize = Response["Content-Length"]
    writeAccessLog("PUT", httpVersion, requestedPath,
                   responseBodySize, restHeaders)
    return response


def handleDELETERequest(httpVersion="", restHeaders={}, requestedPath="", requestBody={}):
    global Response, STATUSCODE
    finalFile = "<!DOCTYPE html><html><head><title>DELETE</title></head><body><h1>Resource Deleted !</h1></body></html>"
    response = ""
    fileExtension = "html"
    responseBodySize = "-"
    try:
        if os.path.isfile(requestedPath[1:]) or os.path.islink(requestedPath[1:]):
            STATUSCODE = 200
            os.unlink(requestedPath[1:])
        # elif os.path.isdir(requestedPath):
        #     shutil.rmtree(requestedPath)
        else:
            STATUSCODE = 404
    except Exception as error:
        # writeErrorLog("error", error)
        pass
    response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
    Response["Content-Type"] = switchContentType(fileExtension)
    Response["Content-Length"] = str(len(finalFile))
    for key, value in Response.items():
        response += key + ": " + value + "\r\n"
    response += "\r\n" + finalFile
    response = response.encode()
    responseBodySize = Response["Content-Length"]
    writeAccessLog("DELETE", httpVersion, requestedPath,
                   responseBodySize, restHeaders)
    return response


def eachClientThread(clientConnection=None):
    global totalClientConnections, STATUSCODE
    totalClientConnections.append(clientConnection)
    try:
        connectionData = clientConnection.recv(1024).decode('utf-8')
        # print("Received Connection Data: ", connectionData)
        requestedMethod, requestedPath, httpVersion, restHeaders, requestBody = getParsedData(
            connectionData)
        # response = b'HTTP/1.1 200 OK\r\n'
        response, isValid = validateRequest(
            requestedMethod, httpVersion, restHeaders)
        # print("Response after validation: ", response)
        if isValid:
            if requestedMethod == "GET":
                response = handleGETRequest(
                    httpVersion, restHeaders, requestedPath)
            elif requestedMethod == "POST":
                response = handlePOSTRequest(
                    httpVersion, restHeaders, requestedPath, requestBody)
            elif requestedMethod == "PUT":
                response = handlePUTRequest(
                    httpVersion, restHeaders, requestedPath, requestBody)
            elif requestedMethod == "DELETE":
                response = handleDELETERequest(
                    httpVersion, restHeaders, requestedPath, requestBody)
            elif requestedMethod == "HEAD":
                response = handleHEADRequest(
                    httpVersion, restHeaders, requestedPath)

        clientConnection.send(response)
        if clientConnection in totalClientConnections:
            totalClientConnections.remove(clientConnection)
        clientConnection.close()

    except Exception as error:
        # writeErrorLog("error", error)
        # break
        pass


def startServer(serverSocket=None):
    while True:
        clientConnection, addr = serverSocket.accept()
        forEachConnection = threading.Thread(
            target=eachClientThread, args=(clientConnection, ))
        forEachConnection.start()


def establishConnection(argv=[]):
    global PORT
    serverSocket = socket(AF_INET, SOCK_STREAM)
    try:
        serverPort = int(argv[1])
    except:
        serverPort = PORT
    serverSocket.bind(('', serverPort))
    serverSocket.listen()
    return serverSocket


if __name__ == "__main__":
    serverSocket = establishConnection(sys.argv)
    print("The Server is ready to receive requests")
    startServer(serverSocket)
