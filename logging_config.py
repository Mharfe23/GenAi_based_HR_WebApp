import logging
import socket
import json

class LogstashHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(("logstash", 5000))
                sock.sendall(log_entry.encode('utf-8'))
        except Exception as e:
            # Optional: fallback to console if logstash unreachable
            print(f"Logging error: {e}")


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        return json.dumps(log_record)
    
def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    handler = LogstashHandler()
    #formatter = logging.Formatter('{"@timestamp": "%(asctime)s", "message": "%(message)s", "level": "%(levelname)s", "module": "%(module)s"}')
    #handler.setFormatter(formatter)
    handler.setFormatter(JsonFormatter())
    
    # Remove existing handlers to avoid duplicate logs
    for h in logger.handlers[:]:
        logger.removeHandler(h)
    
    logger.addHandler(handler)
