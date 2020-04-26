### Monitor which sessions are active. Query via
### nc localhost PORT < /dev/null

import logging
import sys
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger('monitor')

# NOTE: I accidentally lost the source code, but this still runs so... ️🤷
from monitor_internal import run_monitor

if __name__ == '__main__':
    host = 'localhost'
    port = int(sys.argv[1])
    web_port = int(sys.argv[2])
    logger.info(f'Running on port {port} and connecting to webserver on {web_port}')
    run_monitor(host, port, web_port)
