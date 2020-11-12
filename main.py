import os
import signal
import sys
import time


def stopServer():
    pname = "http_server.py"
    try:
        # extract process id of http_server.py and kill all running instances
        for line in os.popen(f"ps ax | grep {pname} | grep -v grep"):
            data = line.split()
            pid = data[0]
            os.kill(int(pid), signal.SIGKILL)
    except Exception as error:
        # print("Error: ", error)
        print("Failed to stop server, try using sudo !")
        sys.exit(1)


def startServer():
    try:
        # start server in background
        os.system("sudo python3 http_server.py &")
    except Exception as error:
        # print("Error: ", error)
        print("Failed to start server...")
        sys.exit(1)


# default runnning instructions


def runInstructions():
    print("To run HTTP server:")
    print("\t1. To start: \"sudo python3 main.py <start-flag>\"")
    print("\t1. To stop: \"sudo python3 main.py <stop-flag>\"")
    print("\t1. To restart: \"sudo python3 main.py <stop-flag>\"")
    print("Options:")
    print("\t<start-flag> : start | START\t(To start server)")
    print("\t<stop-flag> : stop | STOP\t(To stop server)")
    print("\t<restart-flag> : restart | RESTART\t(To restart server)")
    print("\nPlease read README.md for detailed information.")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        operation = sys.argv[1]
        if operation == "start" or operation == "START":
            print("Starting server...")
            startServer()
            time.sleep(1)
            print("Server started...ok")
        elif operation == "stop" or operation == "STOP":
            print("Stopping server...")
            stopServer()
            time.sleep(1)
            print("Server stopped...ok")
        elif operation == "restart" or operation == "RESTART":
            print("Restarting server...")
            stopServer()
            time.sleep(2)
            startServer()
            print("Server restarted...ok")
    else:
        runInstructions()
