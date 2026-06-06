import copy
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from data.config import settings

RESET = "\033[0m"
VERDE = "\033[32m"
AMARILLO = "\033[33m"
ROJO = "\033[31m"
CYAN = "\033[36m"

class ColoresConsoleFormatter(logging.Formatter):
    def format(self, record):
        formato_base = '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s'

        record = copy.copy(record)
        if record.levelno == logging.INFO:
            record.levelname = f"{VERDE}{record.levelname}{RESET}"
        elif record.levelno == logging.WARNING:
            record.levelname = f"{AMARILLO}{record.levelname}{RESET}"
        else:
            record.levelname = f"{ROJO}{record.levelname}{RESET}"
        
        record.filename = f"{CYAN}{record.filename}{RESET}"
        formatter = logging.Formatter(formato_base, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

def configurar_logger(nombre_modulo="sires_motor"):
    logger = logging.getLogger(nombre_modulo)
    if logger.hasHandlers():
        return logger

    logger.setLevel(settings.LOG_LEVEL.upper())

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoresConsoleFormatter())
    logger.addHandler(console_handler)
    
    os.makedirs("logs", exist_ok=True)

    file_handler = RotatingFileHandler(
        "logs/ejecucion.log",
        maxBytes= 5 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )

    formato_archivo = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler.setFormatter(formato_archivo)
    logger.addHandler(file_handler)
    
    return logger

log = configurar_logger()