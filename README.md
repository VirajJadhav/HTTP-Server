# HTTP Server

A **HTTP** or a web **server** is a software that processes requests via **HTTP** , i.e. a network protocol used to exchange information on the World Wide Web (WWW). It's main function is to store, process and deliver web pages / responses / answers to the requests offered / made by a client and fulfill it accordingly.

This project is a rudimentary implementation of how a **HTTP** (**HTTP/1.1** with non - persistent connections with client) server performs / answers to **HTTP** requests from client.
(Here, client:- Anyone who can establish a **TCP** connection with the server and is capabable of sending **HTTP** requests as well receiving a **HTTP** response)

## To run this project

**Requirements:**

i. python installed (version >= 3.8)
i. python packages - (socket, threading, datetime, email.utils, sys, os, configparser, shutil, uuid, json, requests)

**Steps To Run:**

- Server:
  `sudo python3 main.py <options>`
  i. \<options>
  i. To start server: start | START
  i. `sudo python3 main.py start`
  or
  i. `sudo python3 main.py START`
  i. To stop server: stop | STOP
  i. `sudo python3 main.py stop`
  or
  i. `sudo python3 main.py STOP`
  i. To restart server: restart | RESTART
  i. `sudo python3 main.py restart`
  or
  i. `sudo python3 main.py RESTART`

- Client Tester:
  i. Load Testing - `python3 client_test.py -l <number-of-requests>`
  i. Options - -l, --load - --debug=True (For logging response codes on terminal for respective request methods)
  i. \<number-of-requests> (optional) : Integer value for multiple same requests present in **LTest.json** file.
  Default value: Number of request objest present in **LTest.json**.
  i. Confirmation Testing - `python3 client_test.py -c <method-name>`
  i. Options - -c, --confirmation - --debug=True (For logging response codes on terminal for respective request methods)
  i. \<method-name> : **GET** | **POST** | **PUT** | **DELETE** | **HEAD** (requests present / to be added in **CTest.json** file)

### Important file Syntax

i. CTest.json or LTest.json (For testing purpose) - Key, value pairs expected per object (file is in json format) - possible keys: - "method": which states HTTP method ("GET", "POST", "PUT", "DELETE", "HEAD") - "url": url to which the request is sent ("/index.html", "/something", etc); (Default is "/") - "data" (Applicable for POST and PUT):
Again in key, value pairs, eg,
"data" = {
"name": "Delta-server",
"location": "pune",
.
.
.
} - "file" (Applicable for POST and PUT):
Again in key, value pais, possible keys: - "name": filename that is expected to be stored on server - "path": file path from where the client is expected to pick the file (Absolute path is expected) - "fileType" (options): eg - ("text", "image"); (Default is "_/_")
eg,
"file" = {
"name": "serverToBeuploaded.txt",
"path": "/home/USER/Desktop/somefile.txt",
"fileType": "text"
} - possible values: - Anything with well defined and valid characters.
i. config.ini (Config file) - Present in ConfigFiles/config.ini or (\<absolute-path>/ConfigFiles/config.ini) - **Syntax** - \[SECTION]
key = value
eg,
\[DEFAULT]
PORT = 4000