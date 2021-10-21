import datetime
import logging
import colorlog


def beijing(sec, what):
    beijing_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    return beijing_time.timetuple()


def set_up_log():
    logging.Formatter.converter = beijing

    # log_file_folder = './logs'
    # make_dir(log_file_folder)
    # log_file_name = log_file_folder + os.sep + "logs.log"
    logger = logging.getLogger('python-logstash')
    # file_formatter = logging.Formatter('%(asctime)s - %(levelname)s > %(message)s')
    console_formatter = colorlog.ColoredFormatter(
        fmt='%(log_color)s%(asctime)s - %(levelname)s > %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'white',  # cyan white
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red'
        }
    )

    logger.setLevel(logging.INFO)
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(console_formatter)

    # file_handler = handlers.TimedRotatingFileHandler(filename=log_file_name, when='D', encoding='utf-8')
    # file_handler.setFormatter(file_formatter)
    # logger.addHandler(file_handler)

    logger.addHandler(stdout_handler)
    return logger


log = set_up_log()
