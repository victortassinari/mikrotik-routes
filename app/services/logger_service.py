import logging
import os
import sys

def setup_logger():
    # Determine log path
    if getattr(sys, 'frozen', False):
        # Running as executable
        base_path = os.path.dirname(sys.executable)
    else:
        # Running in dev
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    log_dir = os.path.join(base_path, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "app.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger("MikroTikRoutes")
    logger.info("Application started")
    return logger

logger = setup_logger()
