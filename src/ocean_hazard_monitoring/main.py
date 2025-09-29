"""Main entry point for the Ocean Hazard Monitoring application"""
import argparse
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path('logs/ocean_hazard_monitoring.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run():
    """Main entry point for the Ocean Hazard Monitoring application"""
    parser = argparse.ArgumentParser(description='Ocean Hazard Monitoring System')
    parser.add_argument('--mode', type=str, default='development',
                        choices=['development', 'production'],
                        help='Run mode (development or production)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug('Debug mode enabled')
    
    logger.info(f'Starting Ocean Hazard Monitoring System in {args.mode} mode')
    
    # Create necessary directories if they don't exist
    Path('logs').mkdir(exist_ok=True)
    
    try:
        # Here we would initialize the various components of our system
        # For now, we'll just log that the system has started
        logger.info('Ocean Hazard Monitoring System started successfully')
        
        # In a real implementation, we would start the various services here
        # For example: data collection, AI/NLP processing, API server, etc.
        
        # Keep the application running (in a real implementation)
        # import time
        # while True:
        #     time.sleep(1)
            
    except Exception as e:
        logger.error(f'Failed to start Ocean Hazard Monitoring System: {str(e)}', exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    run()