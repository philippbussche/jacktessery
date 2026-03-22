import configparser

config = configparser.RawConfigParser()
config.read('config.properties')

PORT = config.get('general', 'port')
METRICS_PREFIX = config.get('monitoring', 'metrics_prefix')
GRACE_PERIOD = config.getint('monitoring', 'grace_period')
SAVE_SOURCE_IMG = config.getboolean('general', 'save_source_image')
RESULT_DIR = config.get('general', 'save_image_path')

CHARGING_STATUS_ENABLED = config.getboolean('charging_status', 'enabled')
CHARGING_STATUS_MAX_VALUE = config.getint('charging_status', 'max_value')
CHARGING_STATUS_MAX_RATE = config.getint('charging_status', 'max_rate')
CHARGING_STATUS_MIN_CONFIDENCE = config.getint('charging_status', 'min_confidence')

INPUT_WATTS_ENABLED = config.getboolean('input_watts', 'enabled')
INPUT_WATTS_MAX_VALUE = config.getint('input_watts', 'max_value')
INPUT_WATTS_MAX_RATE = config.getint('input_watts', 'max_rate')
INPUT_WATTS_MIN_CONFIDENCE = config.getint('input_watts', 'min_confidence')

OUTPUT_WATTS_ENABLED = config.getboolean('output_watts', 'enabled')
OUTPUT_WATTS_MAX_VALUE = config.getint('output_watts', 'max_value')
OUTPUT_WATTS_MAX_RATE = config.getint('output_watts', 'max_rate')
OUTPUT_WATTS_MIN_CONFIDENCE = config.getint('output_watts', 'min_confidence')

config = {
    'general': {
        'port': PORT,
        'save_source_image': SAVE_SOURCE_IMG,
        'save_image_path': RESULT_DIR
    },
    'monitoring': {
        'metrics_prefix': METRICS_PREFIX,
        'grace_period': GRACE_PERIOD
    },
    'metrics': {
        'charging_status': {
            'enabled': CHARGING_STATUS_ENABLED,
            'max_value': CHARGING_STATUS_MAX_VALUE,
            'max_rate': CHARGING_STATUS_MAX_RATE,
            'min_confidence': CHARGING_STATUS_MIN_CONFIDENCE
        },
        'input_watts': {
            'enabled': INPUT_WATTS_ENABLED,
            'max_value': INPUT_WATTS_MAX_VALUE,
            'max_rate': INPUT_WATTS_MAX_RATE,
            'min_confidence': INPUT_WATTS_MIN_CONFIDENCE
        },
        'output_watts': {
            'enabled': OUTPUT_WATTS_ENABLED,
            'max_value': OUTPUT_WATTS_MAX_VALUE,
            'max_rate': OUTPUT_WATTS_MAX_RATE,
            'min_confidence': OUTPUT_WATTS_MIN_CONFIDENCE
        }
    }
}
