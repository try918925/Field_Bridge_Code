import logging
import logging.handlers
import os

class ColoredLogger(logging.Logger):
    def __init__(self, name, level=logging.INFO, log_file=None):
        logging.Logger.__init__(self, name, level)

        color_formatter = logging.Formatter(
            "%(asctime)s - %(name)s[line:%(lineno)d]: %(message)s", "%Y-%m-%d %H:%M:%S")

        self.color = True
        if log_file:
            console = logging.handlers.TimedRotatingFileHandler(log_file, when= 'midnight', backupCount= 15, encoding='utf-8')
            console.setLevel(logging.DEBUG)
            console.setFormatter(color_formatter)
            self.addHandler(console)

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(color_formatter)
        self.addHandler(console)

        return

    def info(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.INFO):
            if self.color:
                self._log(logging.INFO, "\033[32m%s\033[0m" % ("INFO - " + str(msg)), args, **kwargs)
            else:
                self._log(logging.INFO, msg, args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.DEBUG):
            if self.color:
                self._log(logging.DEBUG, "\033[37m%s\033[0m" % ("DEBUG - " + str(msg)), args, **kwargs)
            else:
                self._log(logging.DEBUG, msg, args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.INFO):
            self._log(logging.WARNING, "\033[33m%s\033[0m" % ("WARNING - " + str(msg)), args, **kwargs)

    def error(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.ERROR):
            self._log(logging.ERROR, "\033[31m%s\033[0m" % ("ERROR - " + str(msg)), args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.INFO):
            self._log(logging.WARNING, "\033[36m%s\033[0m" % ("CRITICAL - " + str(msg)) , args, **kwargs)

def init_logger(name, level=logging.DEBUG, log_file=None):
    try:
        logger = ColoredLogger(name, level= level, log_file= log_file)
        print(f"Succeed to init logger {log_file}.")
        return True, logger
    
    except Exception as error:
        print(f"Failed to init logger {{log_file}}: \n'{type(error).__name__}: {error}'.")
        return False, None   