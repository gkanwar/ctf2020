import sys
# NOTE: I accidentally lost the source code, but this still runs so... ️🤷
from monitor_internal import run_monitor

if __name__ == '__main__':
    host = 'localhost'
    port = int(sys.argv[1])
    web_port = int(sys.argv[2])
    run_monitor(host, port, web_port)
