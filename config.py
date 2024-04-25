import configparser

# read the configuration from properties file
config = configparser.RawConfigParser()
config.read('config.properties')

# general configuration
PORT = config.get('general', 'port')

# configuration for prometheus metrics
METRICS_PREFIX = config.get('monitoring', 'metrics_prefix')
GRACE_PERIOD = config.getint('monitoring', 'grace_period')

# general image settings
SAVE_SOURCE_IMG = config.getboolean('general', 'save_source_image')
SAVE_RESULT_IMG = config.getboolean('general', 'save_result_image')
SAVE_RESULT_IMG_IN_BUCKET = config.getboolean('general', 'save_result_image_in_bucket')
RESULT_DIR = config.get('general', 'save_image_path')

# charging status configuration
CHARGING_STATUS_THRESHOLD = config.getint('charging_status', 'threshold')
CHARGING_STATUS_ENABLED = config.getboolean('charging_status', 'enabled')
CHARGING_STATUS_X1 = config.getint('charging_status', 'x1')
CHARGING_STATUS_Y1 = config.getint('charging_status', 'y1')
CHARGING_STATUS_X2 = config.getint('charging_status', 'x2')
CHARGING_STATUS_Y2 = config.getint('charging_status', 'y2')
CHARGING_STATUS_LANG = config.get('charging_status', 'lang')
CHARGING_STATUS_CONFIG = config.get('charging_status', 'config')
CHARGING_STATUS_ERODE = config.getboolean('charging_status', 'erode')
CHARGING_STATUS_ERODE_CYCLES = config.getint('charging_status', 'erode_cycles')
CHARGING_STATUS_DILATE = config.getboolean('charging_status', 'dilate')
CHARGING_STATUS_MAX_VALUE = config.getint('charging_status', 'max_value')
CHARGING_STATUS_MAX_RATE = config.getint('charging_status', 'max_rate')
CHARGING_STATUS_MIN_CONFIDENCE = config.getint('charging_status', 'min_confidence')

# input watts configuration
INPUT_WATTS_THRESHOLD = config.getint('input_watts', 'threshold')
INPUT_WATTS_ENABLED = config.getboolean('input_watts', 'enabled')
INPUT_WATTS_X1 = config.getint('input_watts', 'x1')
INPUT_WATTS_Y1 = config.getint('input_watts', 'y1')
INPUT_WATTS_X2 = config.getint('input_watts', 'x2')
INPUT_WATTS_Y2 = config.getint('input_watts', 'y2')
INPUT_WATTS_LANG = config.get('input_watts', 'lang')
INPUT_WATTS_CONFIG = config.get('input_watts', 'config')
INPUT_WATTS_ERODE = config.getboolean('input_watts', 'erode')
INPUT_WATTS_ERODE_CYCLES = config.getint('input_watts', 'erode_cycles')
INPUT_WATTS_DILATE = config.getboolean('input_watts', 'dilate')
INPUT_WATTS_MAX_VALUE = config.getint('input_watts', 'max_value')
INPUT_WATTS_MAX_RATE = config.getint('input_watts', 'max_rate')
INPUT_WATTS_MIN_CONFIDENCE = config.getint('input_watts', 'min_confidence')

# output watts configuration
OUTPUT_WATTS_THRESHOLD = config.getint('output_watts', 'threshold')
OUTPUT_WATTS_ENABLED = config.getboolean('output_watts', 'enabled')
OUTPUT_WATTS_X1 = config.getint('output_watts', 'x1')
OUTPUT_WATTS_Y1 = config.getint('output_watts', 'y1')
OUTPUT_WATTS_X2 = config.getint('output_watts', 'x2')
OUTPUT_WATTS_Y2 = config.getint('output_watts', 'y2')
OUTPUT_WATTS_LANG = config.get('output_watts', 'lang')
OUTPUT_WATTS_CONFIG = config.get('output_watts', 'config')
OUTPUT_WATTS_ERODE = config.getboolean('output_watts', 'erode')
OUTPUT_WATTS_ERODE_CYCLES = config.getint('output_watts', 'erode_cycles')
OUTPUT_WATTS_DILATE = config.getboolean('output_watts', 'dilate')
OUTPUT_WATTS_MAX_VALUE = config.getint('output_watts', 'max_value')
OUTPUT_WATTS_MAX_RATE = config.getint('output_watts', 'max_rate')
OUTPUT_WATTS_MIN_CONFIDENCE = config.getint('output_watts', 'min_confidence')

config = {
    'general': {
        'port': PORT,
        'save_source_image': SAVE_SOURCE_IMG,
        'save_result_image': SAVE_RESULT_IMG,
        'save_result_image_in_bucket': SAVE_RESULT_IMG_IN_BUCKET,
        'save_image_path': RESULT_DIR
    },
    'monitoring': {
        'metrics_prefix': METRICS_PREFIX,
        'grace_period': GRACE_PERIOD
    },
    'metrics': { 
        'charging_status': {
            'enabled': CHARGING_STATUS_ENABLED,
            'threshold': CHARGING_STATUS_THRESHOLD,
            'x1': CHARGING_STATUS_X1,
            'y1': CHARGING_STATUS_Y1,
            'x2': CHARGING_STATUS_X2,
            'y2': CHARGING_STATUS_Y2,
            'lang': CHARGING_STATUS_LANG,
            'config': CHARGING_STATUS_CONFIG,
            'erode': CHARGING_STATUS_ERODE,
            'erode_cycles': CHARGING_STATUS_ERODE_CYCLES,
            'dilate': CHARGING_STATUS_DILATE,
            'max_value': CHARGING_STATUS_MAX_VALUE,
            'max_rate': CHARGING_STATUS_MAX_RATE,
            'min_confidence': CHARGING_STATUS_MIN_CONFIDENCE
        },
        'input_watts': {
            'enabled': INPUT_WATTS_ENABLED,
            'threshold': INPUT_WATTS_THRESHOLD,
            'x1': INPUT_WATTS_X1,
            'y1': INPUT_WATTS_Y1,
            'x2': INPUT_WATTS_X2,
            'y2': INPUT_WATTS_Y2,
            'lang': INPUT_WATTS_LANG,
            'config': INPUT_WATTS_CONFIG,
            'erode': INPUT_WATTS_ERODE,
            'erode_cycles': INPUT_WATTS_ERODE_CYCLES,
            'dilate': INPUT_WATTS_DILATE,
            'max_value': INPUT_WATTS_MAX_VALUE,
            'max_rate': INPUT_WATTS_MAX_RATE,
            'min_confidence': INPUT_WATTS_MIN_CONFIDENCE
        },
        'output_watts': {
            'enabled': OUTPUT_WATTS_ENABLED,
            'threshold': OUTPUT_WATTS_THRESHOLD,
            'x1': OUTPUT_WATTS_X1,
            'y1': OUTPUT_WATTS_Y1,
            'x2': OUTPUT_WATTS_X2,
            'y2': OUTPUT_WATTS_Y2,
            'lang': OUTPUT_WATTS_LANG,
            'config': OUTPUT_WATTS_CONFIG,
            'erode': OUTPUT_WATTS_ERODE,
            'erode_cycles': OUTPUT_WATTS_ERODE_CYCLES,
            'dilate': OUTPUT_WATTS_DILATE,
            'max_value': OUTPUT_WATTS_MAX_VALUE,
            'max_rate': OUTPUT_WATTS_MAX_RATE,
            'min_confidence': OUTPUT_WATTS_MIN_CONFIDENCE
        }
    }
}