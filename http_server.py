# necessary modules
from socket import *
import threading
from datetime import datetime, timezone
from email.utils import formatdate
import sys
import os
from configparser import ConfigParser
from shutil import rmtree
from uuid import uuid4
import json

# store config file data
CONFIG = None

# store client ip
CLIENTIP = None

# store response status code
STATUSCODE = None

# some of the common image file extensions
imageFileExtensions = [".png", ".jpeg", ".jpg",
                       ".ico", ".webp", ".apng", ".gif", ".bmp", ".svg"]

# Minimal response body structure
Response = {
    "Date": "",
    "Server": "Delta-Server/0.0.1 (Ubuntu)",
    "Connection": "close",
    "Content-Language": "en-US",
}


def switchStatusCode(code=None):
    # switch case table for status codes
    codeTable = {
        200: " 200 OK",
        201: " 201 Created",
        304: " 304 Not Modified",
        400: " 400 Bad Request",
        403: " 403 Forbidden",
        404: " 404 Not Found",
        411: " 411 Length Required",
        415: " 415 Unsupported Media Type",
        501: " 501 Not Implemented",
        505: " 505 HTTP Version Not Supported",
    }
    # if nothing gets matched return bad request
    return codeTable.get(code, " 400 Bad Request")


def switchContentType(contentType=None):
    # switch case table for mime types
    contentTable = {
        "txt": "text/plain",
        "html": "text/html",
        "php": "text/html",
        "pdf": "application/pdf",
        "css": "text/css",
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
        "js": "application/javascript",
        "bin": "application/octet-stream",
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "mpeg": "video/mpeg",
        "webm": "video/webm",
        "3gp": "video/3gpp"
    }
    # if nothing gets matched return text plain
    return contentTable.get(contentType, "text/plain") + "; charset=ISO-8859-1"


# function to generate HTTP/1.1 date format
def httpDateFormat(Ltime=False):
    return str(formatdate(timeval=None, localtime=Ltime, usegmt=True))


def getLastModifiedTime(path=""):
    lastModified = ""
    try:
        # get last modified time
        msecs = os.path.getmtime(path)
    except Exception as error:
        msecs = 0
        # writeErrorLog("error", error)
    # format last modified time according to HTTP/1.1 rules
    lastModified = datetime.fromtimestamp(
        msecs, timezone.utc).strftime("%a, %d %b %Y %H:%M:%S") + " GMT"
    return lastModified


def clearInvalidLog(Access=True, Error=True):
    global CONFIG
    try:
        accessPath = CONFIG['LOG']['Access']
        errorPath = CONFIG['LOG']['Error']
        if Access:
            # check if file is present
            # if present clear if size exceeds limit
            if(os.path.isfile(accessPath) and os.path.getsize(accessPath) > 1000000):
                os.unlink(accessPath)
        if Error:
            # check if file is present
            # if present clear if size exceeds limit
            if(os.path.isfile(errorPath) and os.path.getsize(errorPath) > 1000000):
                os.unlink(errorPath)
    except Exception as error:
        writeErrorLog("error", error)


def writeErrorLog(Code="", Error=""):
    global CLIENTIP, CONFIG
    # clear error log for flooded data
    clearInvalidLog(Access=False, Error=True)

    # follow defined log format

    date = httpDateFormat(True)
    pid = str(os.getpid())
    tid = str(threading.current_thread().ident)
    log = "[" + date + "]" + " "
    log += "[core: " + Code + "]" + " "
    log += "[pid " + pid + ":tid " + tid + "]" + " "
    if CLIENTIP != None:
        log += "[client " + CLIENTIP + "]" + " "
    log += str(Error) + "\n"
    try:
        if not os.path.isdir(CONFIG['LOG']['Directory']):
            os.mkdir(CONFIG['LOG']['Directory'])
        with open(CONFIG['LOG']['Error'], "a") as outputFile:
            outputFile.write(log)
    except Exception as e:
        with open("error.log", "a") as outputFile:
            outputFile.write(log)


def writeAccessLog(requestedMethod="", httpVersion="", requestedPath="", responseBodySize="-", restHeaders={}):
    global STATUSCODE, CLIENTIP, CONFIG
    # clear access log for flooded data
    clearInvalidLog(Access=True, Error=False)
    date = httpDateFormat(True)

    # follow defined log format

    if CLIENTIP != None:
        log = CLIENTIP + " "
    else:
        log = "- "
    log += "[" + date + "]" + " "
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
        if not os.path.isdir(CONFIG['LOG']['Directory']):
            os.mkdir(CONFIG['LOG']['Directory'])
        with open(CONFIG['LOG']['Access'], "a") as outputFile:
            outputFile.write(log)
    except Exception as error:
        writeErrorLog("error", error)


def validateRequest(requestedMethod="", httpVersion="", restHeaders={}):
    global STATUSCODE, Response
    finalFile = ""
    response = ""
    fileExtension = "html"
    Response["Date"] = httpDateFormat()

    # check for not valid request body

    if requestedMethod not in ["GET", "POST", "PUT", "DELETE", "HEAD"]:
        STATUSCODE = 501
        httpVersion = "HTTP/1.1"
        response = httpVersion + \
            switchStatusCode(STATUSCODE) + "\r\n"
        Response["Content-Length"] = "0"
        for key, value in Response.items():
            response += key + ": " + value + "\r\n"
        response = response.encode('ISO-8859-1')
        return response, Response["Content-Length"], False
    elif httpVersion != "HTTP/1.1":
        STATUSCODE = 505
        response = "HTTP/1.1" + switchStatusCode(STATUSCODE) + "\r\n"
        # response html file
        finalFile = "<!DOCTYPE html><html><head><title>Delta-Server</title></head><body><h1>505</h1><h2>HTTP Version Not Supported</h2></body></html>"
        Response["Content-Type"] = switchContentType(fileExtension)
        Response["Content-Length"] = str(len(finalFile))
        for key, value in Response.items():
            response += key + ": " + value + "\r\n"
        if requestedMethod != "HEAD":
            response += "\r\n" + finalFile
        response = response.encode('ISO-8859-1')
        return response, Response["Content-Length"], False
    elif ("Host" not in restHeaders) or (requestedMethod in ["POST", "PUT"] and "Content-Type" not in restHeaders):
        STATUSCODE = 400
        # response html file
        finalFile = "<!DOCTYPE html><html><head><title>Delta-Server</title></head><body><h1>400</h1><h2>Server received a Bad Request</h2></body></html>"
        response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
        Response["Content-Type"] = switchContentType(fileExtension)
        Response["Content-Length"] = str(len(finalFile))
        for key, value in Response.items():
            response += key + ": " + value + "\r\n"
        if requestedMethod != "HEAD":
            response += "\r\n" + finalFile
        response = response.encode('ISO-8859-1')
        return response, Response["Content-Length"], False
    elif requestedMethod in ["POST", "PUT"]:
        if "Content-Length" not in restHeaders:
            STATUSCODE = 411
            # response html file
            finalFile = "<!DOCTYPE html><html><head><title>Delta-Server</title></head><body><h1>411</h1><h2>Server received a request without Content Length</h2></body></html>"
            response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
            Response["Content-Type"] = switchContentType(fileExtension)
            Response["Content-Length"] = str(len(finalFile))
            for key, value in Response.items():
                response += key + ": " + value + "\r\n"
            response += "\r\n" + finalFile
            response = response.encode('ISO-8859-1')
            return response, Response["Content-Length"], False
        elif "Content-Type" in restHeaders:
            actualType = restHeaders["Content-Type"].strip().split(";")[0]
            if actualType not in ["application/x-www-form-urlencoded", "text/plain", "multipart/form-data"]:
                STATUSCODE = 415
                # response html file
                finalFile = "<!DOCTYPE html><html><head><title>Delta-Server</title></head><body><h1>415</h1><h2>Server received a request with unsupported media type</h2></body></html>"
                response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
                Response["Content-Type"] = switchContentType(fileExtension)
                Response["Content-Length"] = str(len(finalFile))
                for key, value in Response.items():
                    response += key + ": " + value + "\r\n"
                response += "\r\n" + finalFile
                response = response.encode('ISO-8859-1')
                return response, Response["Content-Length"], False
    return response, 0, True


def parseRequestValueData(value=None):
    tvalue = value.split("%")
    # necessary string manipulations
    if "+" in tvalue[0]:
        value = tvalue[0].replace("+", " ")
    else:
        value = tvalue[0]
    if len(tvalue) > 1:
        for i in range(len(tvalue)):
            if "+" in tvalue[i]:
                value += tvalue[i].replace("+", " ")
            try:
                # decode hex value present in request body for POST or PUT
                bytesData = bytes.fromhex(
                    tvalue[i][:2])
                value += bytesData.decode("ASCII") + tvalue[i][2:]
            except Exception as error:
                writeErrorLog("debug", error)
    return value


def getParsedData(connectionData=None, clientConnection=None):
    global imageFileExtensions
    # get first level parsed data in form of list
    parsedData = connectionData.split("\r\n")
    headerEndCount = 0
    requestedMethod = None
    requestedPath = ""
    httpVersion = None
    requestBody = {}
    restHeaders = dict()
    firstLine = parsedData[0].split()
    # get the first request line by checking corner cases
    # requestedMethod
    # path
    # HTTP version
    if len(firstLine) == 3:
        requestedMethod, requestedPath, httpVersion = firstLine
    elif len(firstLine) == 2:
        requestedMethod = firstLine[0]
        requestedPath = firstLine[1]
    elif len(firstLine) == 1:
        requestedMethod = firstLine[0]
    # extract all headers and store in dictionary
    # keep a header count
    for data in parsedData[1:]:
        headerEndCount += 1
        try:
            # split into key value pair
            key, value = data.split(":", 1)
            restHeaders[key] = value
        except Exception as error:
            writeErrorLog("debug", error)
            break
    # handle body conditions for POST and PUT
    if requestedMethod == "POST" or requestedMethod == "PUT":
        actualLength = int(restHeaders["Content-Length"].strip())
        receivedBody = connectionData.split("\r\n\r\n")[1:]
        lengthReceivedBody = int(len("\r\n\r\n".join(receivedBody)))
        # check if full request if received or not
        # if not then loop until we receive it
        # checking done on content length header field
        if actualLength > 1024 or (actualLength - lengthReceivedBody) > 0:
            extraData = actualLength - lengthReceivedBody
            try:
                while extraData > 0:
                    extraConnectionData = clientConnection.recv(
                        1024).decode('ISO-8859-1')
                    connectionData = str(connectionData) + \
                        str(extraConnectionData)
                    extraData -= int(len(extraConnectionData))
            except Exception as error:
                writeErrorLog("debug", error)
            parsedData = list(connectionData.split("\r\n"))
        if "Content-Type" in restHeaders:
            if "application/x-www-form-urlencoded" in restHeaders["Content-Type"]:
                # handle application form body ahead of header count
                tempBody = parsedData[headerEndCount + 1].split("&")
                for tbody in tempBody:
                    try:
                        key, value = tbody.split("=")
                        # get valid value after hex decoding
                        requestBody[key] = parseRequestValueData(value)
                    except Exception as error:
                        writeErrorLog("debug", error)
            elif "text/plain" in restHeaders["Content-Type"]:
                # handle text plain body ahead of header count
                reqBody = parsedData[headerEndCount + 1:]
                index = 0
                for body in reqBody:
                    index += 1
                    try:
                        key, value = body.split("=")
                        requestBody[key] = value
                    except Exception as error:
                        writeErrorLog("debug", error)
                        requestBody["body" + str(index)] = body
            elif "multipart/form-data" in restHeaders["Content-Type"]:
                # handle multipart form body ahead of header count
                reqBody = parsedData[headerEndCount + 1:]
                for i in range(1, len(reqBody) - 4):
                    if ";" in reqBody[i]:
                        try:
                            tbody = reqBody[i].split(";")
                            if len(tbody) == 2:
                                tkey = tbody[1].split("name=")[1].strip("\"")
                                requestBody[tkey] = reqBody[i + 2]
                            elif len(tbody) == 3:
                                tkey = tbody[2].split("filename=")[
                                    1].strip("\"")
                                requestBody[tkey] = str(reqBody[i + 3])
                                if str(tkey).endswith(tuple(imageFileExtensions)):
                                    requestBody[tkey] += "\r\n" + \
                                        str(reqBody[i + 4])
                                requestBody["filename"] = tkey
                        except Exception as error:
                            writeErrorLog("debug", error)
    # return necessary variables once done parsing
    return requestedMethod, requestedPath, httpVersion, restHeaders, requestBody


def getValidFilePath(requestedPath=""):
    global STATUSCODE, CONFIG
    requestedPath = str(requestedPath)
    # check if config file has docuemnt root mentioned
    if 'DocumentRoot' not in CONFIG['PATH']:
        STATUSCODE = 404
        return 'ResponseFiles/not_found.html'
    # if document root is mentioned
    # process further path and return it
    else:
        # if requested resource is directory then check for index.html
        # if present return it
        if os.path.isdir(CONFIG['PATH']['DocumentRoot'] + requestedPath):
            if requestedPath.endswith(('/')):
                return CONFIG['PATH']['DocumentRoot'] + requestedPath + "index.html"
            else:
                return CONFIG['PATH']['DocumentRoot'] + requestedPath + "/index.html"
        # if requested resource is not a directory return the appended path w.r.t document root
        elif os.path.isfile(CONFIG['PATH']['DocumentRoot'] + requestedPath):
            return CONFIG['PATH']['DocumentRoot'] + requestedPath
        # if requested resource is not present w.r.t document root
        # return default not found
        else:
            STATUSCODE = 404
            return CONFIG['PATH']['DocumentRoot'] + "/not_found.html"


def getRequestedFile(requestedPath="", fileMode=""):
    global STATUSCODE, CONFIG
    finalExtension = ""
    try:
        # extract file extension if possible
        if os.path.isfile(CONFIG['PATH']['DocumentRoot'] + requestedPath):
            fileExtension = requestedPath.split(".")[-1]
        else:
            fileExtension = "html"
    except Exception as error:
        writeErrorLog("debug", error)
    try:
        # get valid file path from requested path
        newRequestedPath = getValidFilePath(requestedPath)
    except Exception as error:
        writeErrorLog("debug", error)
    # get last modified time of requested resource
    lastModified = getLastModifiedTime(newRequestedPath)
    # return necessary variables for further request handling
    return newRequestedPath, fileExtension, lastModified


# Function to set cookie
# and also check for returning user
def setCookie(clientIP=None, restHeaders={}):
    global CONFIG
    cookieFile = CONFIG['COOKIE']['File']
    # check if file where cookies are stored is
    # present or not. If not create one.
    if not os.path.isfile(cookieFile):
        with open(cookieFile, "w") as f:
            json.dump([], f, indent=4)
    try:
        cookieData = []
        # read the file where cookies are stored
        with open(cookieFile) as searchFile:
            cookieData = json.load(searchFile)
        # check if user has already visited once
        # if yes send that stored cookie
        for cookie in cookieData:
            if cookie["clientIP"] == str(clientIP) and "cookie" in cookie:
                # return once cookie found
                return "name=" + cookie['cookie'] + "; SameSite=Strict"
        # if not create a new cookie for new user
        newCookie = uuid4()
        newClient = {
            'clientIP': str(clientIP),
            'cookie': str(newCookie)
        }
        cookieData.append(newClient)
        # store this new created cookie
        with open(cookieFile, "w") as searchFile:
            json.dump(cookieData, searchFile, indent=4)
        return "name=" + newClient['cookie'] + "; SameSite=Strict"
    except Exception as error:
        writeErrorLog("debug", error)


# Prepare response message for 403 forbidden status
def getForbiddenResponse(httpVersion="", restHeaders={}):
    global STATUSCODE, CLIENTIP
    STATUSCODE = 403
    fileExtension = "html"
    # response html file
    finalFile = "<!DOCTYPE html><html><head><title>Delta-Server</title></head><body><h1>403</h1><h2>Server refuses to process request (restricted resource access)</h2></body></html>"
    response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
    Response["Content-Type"] = switchContentType(fileExtension)
    Response["Content-Length"] = str(len(finalFile))
    Response["Set-Cookie"] = setCookie(CLIENTIP, restHeaders)
    for key, value in Response.items():
        response += str(key) + ": " + str(value) + "\r\n"
    response += "\r\n" + finalFile
    # return response and body size
    return response, Response["Content-Length"]


def handleGETRequest(httpVersion="", restHeaders={}, requestedPath=""):
    global STATUSCODE, imageFileExtensions, Response, CLIENTIP
    finalFile = response = ""
    fileExtension = "html"
    responseBodySize = "-"
    Response["Date"] = httpDateFormat()
    STATUSCODE = 200
    # check if file is image
    if requestedPath.endswith(tuple(imageFileExtensions)):
        # get necessary variables from requested path
        newRequestedPath, fileExtension, lastModified = getRequestedFile(
            requestedPath, "rb")
        # check if user has necessary file permissions
        if not os.access(newRequestedPath, os.R_OK):
            response, bodySize = getForbiddenResponse(httpVersion, restHeaders)
            responseBodySize = bodySize
            response = response.encode('ISO-8859-1')
        else:
            # check if request is conditional GET and check last modified time and requested time
            if STATUSCODE != 404 and "If-Modified-Since" in restHeaders and restHeaders["If-Modified-Since"].lstrip() == lastModified:
                STATUSCODE = 304
                response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
                if "Content-Type" in Response:
                    del Response["Content-Type"]
                if "Content-Length" in Response:
                    del Response["Content-Length"]
                if "Last-Modified" in Response:
                    del Response["Last-Modified"]
                # set cookie
                Response["Set-Cookie"] = setCookie(CLIENTIP, restHeaders)
                # prepare appropriate response message
                for key, value in Response.items():
                    response += str(key) + ": " + str(value) + "\r\n"
                response = response.encode('ISO-8859-1')
            # if not conditional GET
            else:
                try:
                    # open and read requested resource
                    requestedFile = open(newRequestedPath, "rb")
                    with requestedFile:
                        finalFile = requestedFile.read()
                except Exception as error:
                    writeErrorLog("error", error)
                    # Once all necessary conditions satisfied
                # form a proper response message
                # combine necessary lines and send after encoding
                response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
                Response["Content-Type"] = switchContentType(fileExtension)
                Response["Content-Length"] = str(len(finalFile))
                Response["Last-Modified"] = lastModified
                Response["Set-Cookie"] = setCookie(CLIENTIP, restHeaders)
                for key, value in Response.items():
                    response += str(key) + ": " + str(value) + "\r\n"
                response += "\r\n"
                responseBodySize = Response["Content-Length"]
                response = response.encode('ISO-8859-1') + finalFile
    # if file is not image
    else:
        # get necessary variables from requested path
        newRequestedPath, fileExtension, lastModified = getRequestedFile(
            requestedPath, "r")
        # check if user has necessary file permissions
        if not os.access(newRequestedPath, os.R_OK):
            # if not then send forbidden
            response, bodySize = getForbiddenResponse(httpVersion, restHeaders)
            responseBodySize = bodySize
        else:
            # check if request is conditional GET and check last modified time and requested time
            if STATUSCODE != 404 and "If-Modified-Since" in restHeaders and restHeaders["If-Modified-Since"].lstrip() == lastModified:
                STATUSCODE = 304
                response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
                if "Content-Type" in Response:
                    del Response["Content-Type"]
                if "Content-Length" in Response:
                    del Response["Content-Length"]
                if "Last-Modified" in Response:
                    del Response["Last-Modified"]
                # set cookie
                Response["Set-Cookie"] = setCookie(CLIENTIP, restHeaders)
                # prepare appropriate response message
                for key, value in Response.items():
                    response += str(key) + ": " + str(value) + "\r\n"
            # if not conditional GET
            else:
                try:
                    # open and read requested resource
                    requestedFile = open(newRequestedPath, "r")
                    with requestedFile:
                        finalFile = requestedFile.read()
                except Exception as error:
                    writeErrorLog("error", error)
                # Once all necessary conditions satisfied
                # form a proper response message
                # combine necessary lines and send after encoding
                response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
                Response["Content-Type"] = switchContentType(fileExtension)
                Response["Content-Length"] = str(len(finalFile))
                Response["Last-Modified"] = lastModified
                Response["Set-Cookie"] = setCookie(CLIENTIP, restHeaders)
                for key, value in Response.items():
                    response += str(key) + ": " + str(value) + "\r\n"
                response += "\r\n" + finalFile
                responseBodySize = Response["Content-Length"]

        response = response.encode('ISO-8859-1')
    # log request
    writeAccessLog("GET", httpVersion, requestedPath,
                   responseBodySize, restHeaders)
    return response


def handlePOSTRequest(httpVersion="", restHeaders={}, requestedPath="", requestBody={}):
    global Response, STATUSCODE, imageFileExtensions, CONFIG, CLIENTIP
    # response html file
    finalFile = "<!DOCTYPE html><html><head><title>POST</title></head><body><h1>POST Success</h1></body></html>"
    response = ""
    fileExtension = "html"
    responseBodySize = "-"
    Response["Date"] = httpDateFormat()
    STATUSCODE = 201
    # condition to save file
    # present in request
    if "filename" in requestBody:
        # get request file name
        resultFile = requestBody["filename"]
        try:
            fileMode = "a"
            fileContent = requestBody[requestBody["filename"]]
            # checking if file is image or not
            # if image set appropriate file mode
            if str(requestBody["filename"]).endswith(tuple(imageFileExtensions)):
                fileMode = "wb"
                fileContent = fileContent.encode('ISO-8859-1')
            # check if POST directory if present or not
            # if not create one
            if not os.path.isdir(CONFIG['CLIENT']['Directory']):
                os.mkdir(CONFIG['CLIENT']['Directory'])
            # write file into POST location
            with open(CONFIG['CLIENT']['Directory'] + "/" + resultFile, fileMode) as writeFile:
                writeFile.write(fileContent)
        except Exception as error:
            writeErrorLog("error", error)
        if requestBody["filename"] in requestBody:
            del requestBody[requestBody["filename"]]
    newPostData = "POST Date: " + Response["Date"] + "\n" + "POST DATA:\n"
    for key, value in requestBody.items():
        newPostData += "\t" + str(key) + " = " + str(value) + "\n"
    newPostData += "\n" + "#"*60 + "\n\n"
    try:
        # check if POST directory if present or not
        # if not create one
        if not os.path.isdir(CONFIG['CLIENT']['Directory']):
            os.mkdir(CONFIG['CLIENT']['Directory'])
        # write data into POST location
        with open(CONFIG['CLIENT']['POST'], "a") as outputFile:
            outputFile.write(newPostData)
    except Exception as error:
        writeErrorLog("error", error)
    # Once all necessary conditions satisfied
    # form a proper response message
    # combine necessary lines and send after encoding
    response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
    Response["Content-Type"] = switchContentType(fileExtension)
    Response["Content-Length"] = str(len(finalFile))
    Response["Set-Cookie"] = setCookie(CLIENTIP, restHeaders)
    for key, value in Response.items():
        response += key + ": " + value + "\r\n"
    response += "\r\n" + finalFile
    response = response.encode('ISO-8859-1')
    responseBodySize = Response["Content-Length"]
    # log request
    writeAccessLog("POST", httpVersion, requestedPath,
                   responseBodySize, restHeaders)
    return response


def handleHEADRequest(httpVersion="", restHeaders={}, requestedPath=""):
    global STATUSCODE, imageFileExtensions, Response, CONFIG, CLIENTIP
    response = ""
    fileExtension = "html"
    responseBodySize = "-"
    try:
        # extract file extension
        if os.path.isfile(CONFIG['PATH']['DocumentRoot'] + requestedPath):
            fileExtension = requestedPath.split(".")[-1]
    except Exception as error:
        writeErrorLog("debug", error)
    Response["Date"] = httpDateFormat()
    # set content type according to file extension
    Response["Content-Type"] = switchContentType(fileExtension)
    STATUSCODE = 200
    # get valid file path from the one that was requested
    path = getValidFilePath(requestedPath)
    # checking file permissions
    if not os.access(path, os.R_OK):
        STATUSCODE = 403
        # response html file for forbidden
        finalFile = "<!DOCTYPE html><html><head><title>Delta-Server</title></head><body><h1>403</h1><h2>Server refuses to process request (restricted resource access)</h2></body></html>"
        Response["Content-Length"] = str(len(finalFile))
    else:
        # check for resource not found condition
        if path.endswith(('not_found.html')):
            STATUSCODE = 404
        Response["Content-Length"] = str(os.path.getsize(path))
    # Once all necessary conditions satisfied
    # form a proper response message
    # combine necessary lines and send after encoding
    response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
    Response["Set-Cookie"] = setCookie(CLIENTIP, restHeaders)
    for key, value in Response.items():
        response += str(key) + ": " + str(value) + "\r\n"
    response += "\r\n"
    response = response.encode('ISO-8859-1')
    responseBodySize = Response["Content-Length"]
    # log request
    writeAccessLog("HEAD", httpVersion, requestedPath,
                   responseBodySize, restHeaders)
    return response


def handlePUTRequest(httpVersion="", restHeaders={}, requestedPath="", requestBody={}):
    global Response, STATUSCODE, imageFileExtensions, CLIENTIP
    # response html file
    finalFile = "<!DOCTYPE html><html><head><title>PUT</title></head><body><h1>PUT Success</h1></body></html>"
    response = ""
    fileExtension = "html"
    responseBodySize = "-"
    # set date in response with valid format
    Response["Date"] = httpDateFormat()
    STATUSCODE = 200
    path = "dump.txt"
    fileDataOutput = ""
    exists = True
    # check if file exists
    if not os.path.exists(requestedPath[1:]) and requestedPath != "/":
        STATUSCODE = 201
        # necessary string path handling
        sep = requestedPath.split("/")
        expectedFile = sep[-1].split(".")
        if len(expectedFile) > 1:
            if sep[0] == "":
                path = "/".join(sep[1:-1])
            else:
                path = "/".join(sep[:-1])
            try:
                # create resource if absent
                os.makedirs(path)
            except Exception as error:
                writeErrorLog("error", error)
            path += "/" + sep[-1]
        else:
            # create resource if path doesn't have any file
            # and folder is our resource
            try:
                if sep[0] == "" and len(sep) > 1:
                    newReqPath = "/".join(sep[1:])
                else:
                    newReqPath = "/".join(sep)
                os.makedirs(newReqPath)
            except Exception as error:
                writeErrorLog("error", error)
            path = newReqPath + "/dump.txt"
        exists = False
    # if path exists and user doesn't have appropriate file permission
    if os.path.exists(requestedPath[1:]) and not os.access(requestedPath[1:], os.W_OK):
        # send forbidden
        response, bodySize = getForbiddenResponse(httpVersion, restHeaders)
        responseBodySize = bodySize
        response = response.encode('ISO-8859-1')
        writeAccessLog("PUT", httpVersion, requestedPath,
                       responseBodySize, restHeaders)
        return response
    # handle if request contains a file to be PUT
    if "filename" in requestBody:
        resultFile = requestBody["filename"]
        newPath = ""
        # necessary path manipulations in form of string
        if not exists:
            newPath = "/".join(path.rsplit("/", 1)) + "/"
        elif requestedPath[1:] != "":
            newPath = "/".join(requestedPath[1:].rsplit("/", 1)) + "/"
        try:
            fileMode = "a"
            fileContent = requestBody[requestBody["filename"]]
            # check if file is image or not and change read mode accordingly
            if str(requestBody["filename"]).endswith(tuple(imageFileExtensions)):
                fileMode = "wb"
                fileContent = fileContent.encode('ISO-8859-1')
            # write into file contents
            with open(newPath + resultFile, fileMode) as writeFile:
                writeFile.write(fileContent)
        except Exception as error:
            writeErrorLog("error", error)

        if requestBody["filename"] in requestBody:
            del requestBody[requestBody["filename"]]

    for key, value in requestBody.items():
        fileDataOutput += str(key) + " = " + str(value) + "\n"

    try:
        # if requested resource is not a file or is a folder
        # dump data into a dummy server created file
        if exists and requestedPath[1:] != "" and not os.path.isfile(requestedPath[1:]):
            path = requestedPath[1:] + "/dump.txt"
        with open(path, "w") as outputFile:
            outputFile.write(fileDataOutput)
    except Exception as error:
        writeErrorLog("error", error)
    # Once all necessary conditions satisfied
    # form a proper response message
    # combine necessary lines and send after encoding
    response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
    Response["Content-Type"] = switchContentType(fileExtension)
    Response["Content-Length"] = str(len(finalFile))
    Response["Set-Cookie"] = setCookie(CLIENTIP, restHeaders)
    for key, value in Response.items():
        response += key + ": " + value + "\r\n"
    response += "\r\n" + finalFile
    response = response.encode('ISO-8859-1')
    responseBodySize = Response["Content-Length"]
    # log request
    writeAccessLog("PUT", httpVersion, requestedPath,
                   responseBodySize, restHeaders)
    return response


def handleDELETERequest(httpVersion="", restHeaders={}, requestedPath="", requestBody={}):
    global Response, STATUSCODE, CLIENTIP
    # response html file
    finalFile = "<!DOCTYPE html><html><head><title>DELETE</title></head><body><h1>Resource Deleted !</h1></body></html>"
    response = ""
    fileExtension = "html"
    responseBodySize = "-"
    try:
        # check if file exists
        if os.path.isfile(requestedPath[1:]) or os.path.islink(requestedPath[1:]):
            # check if user has file access before deleting
            if not os.access(requestedPath[1:], os.W_OK):
                # if user doesn't has access
                # return forbidden
                response, bodySize = getForbiddenResponse(
                    httpVersion, restHeaders)
                responseBodySize = bodySize
                response = response.encode('ISO-8859-1')
                writeAccessLog("DELETE", httpVersion,
                               requestedPath, responseBodySize, restHeaders)
                return response
            else:
                # else delete the resource
                STATUSCODE = 200
                os.unlink(requestedPath[1:])
        # same algo as above
        elif os.path.isdir(requestedPath):
            if not os.access(requestedPath[1:], os.W_OK):
                response, bodySize = getForbiddenResponse(
                    httpVersion, restHeaders)
                responseBodySize = bodySize
                response = response.encode('ISO-8859-1')
                writeAccessLog("DELETE", httpVersion,
                               requestedPath, responseBodySize, restHeaders)
                return response
            else:
                rmtree(requestedPath)
        else:
            STATUSCODE = 404
            finalFile = "<!DOCTYPE html><html><head><title>DELETE</title></head><body><h1>Resource was not present !</h1></body></html>"
    except Exception as error:
        writeErrorLog("error", error)
    # Once all necessary conditions satisfied
    # form a proper response message
    # combine necessary lines and send after encoding
    response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
    Response["Content-Type"] = switchContentType(fileExtension)
    Response["Content-Length"] = str(len(finalFile))
    Response["Set-Cookie"] = setCookie(CLIENTIP, restHeaders)
    for key, value in Response.items():
        response += key + ": " + value + "\r\n"
    response += "\r\n" + finalFile
    responseBodySize = Response["Content-Length"]
    response = response.encode('ISO-8859-1')
    # log request
    writeAccessLog("DELETE", httpVersion, requestedPath,
                   responseBodySize, restHeaders)
    return response


def eachClientThread(clientConnection=None):
    global STATUSCODE
    try:
        # receive 1kb data through socket from client
        connectionData = clientConnection.recv(1024).decode('ISO-8859-1')
        # extract necessary variables from request after parsing
        requestedMethod, requestedPath, httpVersion, restHeaders, requestBody = getParsedData(
            connectionData, clientConnection)
        # check if request is valid
        response, responseBodySize, isValid = validateRequest(
            requestedMethod, httpVersion, restHeaders)
        if isValid:
            # handle requests according to their methods
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
        else:
            # if request is not valid
            writeAccessLog(requestedMethod, httpVersion,
                           requestedPath, responseBodySize, restHeaders)
        # send valid formed response
        clientConnection.send(response)
        # close connections once response sent
        clientConnection.close()

    except Exception as error:
        writeErrorLog("error", error)


def startServer(serverSocket=None):
    global CLIENTIP, CONFIG
    maxConnections = int(CONFIG["CONNECTIONS"]["Allowed"])
    # run forever to accept connections from clients and their request
    while True:
        try:
            # if connections exceded from maxconnections,
            # discared them
            if threading.activeCount() <= maxConnections:
                # accepting client connections
                clientConnection, addr = serverSocket.accept()
                # getting client ip
                CLIENTIP = str(addr[0])
                # initialising and starting thread for each connected client
                forEachConnection = threading.Thread(
                    target=eachClientThread, args=(clientConnection, ))
                forEachConnection.start()
        except Exception as error:
            writeErrorLog("error", error)


def establishConnection():
    global CONFIG
    serverSocket = socket(AF_INET, SOCK_STREAM)
    try:
        # setting server port from config file
        serverPort = int(CONFIG.get("DEFAULT", "PORT"))
    except Exception as error:
        # if port invalid exit the program
        print(error, 'of config file.')
        print("Please specify a valid listen port in default section of config file.")
        writeErrorLog("error", error)
        sys.exit(1)
    try:
        # setting condition for port reusability whenever server restarted
        serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        serverSocket.bind(('', serverPort))
        serverSocket.listen(1)
    except Exception as error:
        writeErrorLog("error", error)
    return serverSocket


def readConfig():
    global CONFIG
    # initialising config parser
    CONFIG = ConfigParser()
    try:
        # checking if directory present or not
        if not os.path.isdir('ConfigFiles'):
            os.mkdir("ConfigFiles")
        CONFIG.read('ConfigFiles/config.ini')
        # clearing flooded config files
        # while for fresh server start
        clearInvalidLog()
    except Exception as error:
        writeErrorLog("error", error)
        sys.exit(1)


if __name__ == "__main__":
    try:
        # reading config file
        readConfig()
        # establishing connection with defined port
        serverSocket = establishConnection()
        # starting server
        startServer(serverSocket)
    except KeyboardInterrupt:
        sys.exit(1)
