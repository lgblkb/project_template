import time
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('app')


def main():
    logger.info('Start')
    for i in range(100):
        time.sleep(1)
        logger.info("i: %s", i)
    logger.info('Finish')
    pass


if __name__ == '__main__':
    main()
