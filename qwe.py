import time
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('qwe')
for i in range(1000):
    logger.debug("i: %s", i)
    time.sleep(1)
