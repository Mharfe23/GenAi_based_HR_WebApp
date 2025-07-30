import logging
import socket

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

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    handler = LogstashHandler()
    formatter = logging.Formatter('{"@timestamp": "%(asctime)s", "message": "%(message)s", "level": "%(levelname)s", "module": "%(module)s"}')
    handler.setFormatter(formatter)
    
    # Remove existing handlers to avoid duplicate logs
    for h in logger.handlers[:]:
        logger.removeHandler(h)
    
    logger.addHandler(handler)
