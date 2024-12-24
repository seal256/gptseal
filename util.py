import traceback
import logging

def format_exception(e: Exception) -> str:
    exception_type = type(e).__name__
    exception_message = str(e)
    stack_trace = traceback.format_exc()
    message = f"Internal server exception: {exception_type} {exception_message} {stack_trace}"
    return message

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger