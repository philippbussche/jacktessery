import configparser

raw_config = configparser.RawConfigParser()
raw_config.read('config.properties')

RESERVED_SECTIONS = {'general', 'monitoring'}

metrics = {}
for section in raw_config.sections():
    if section not in RESERVED_SECTIONS:
        metrics[section] = {
            'enabled': raw_config.getboolean(section, 'enabled'),
            'json_path': raw_config.get(section, 'json_path'),
            'max_value': raw_config.getfloat(section, 'max_value'),
            'max_rate': raw_config.getfloat(section, 'max_rate'),
        }

config = {
    'general': {
        'port': raw_config.get('general', 'port'),
        'save_source_image': raw_config.getboolean('general', 'save_source_image'),
        'save_image_path': raw_config.get('general', 'save_image_path')
    },
    'monitoring': {
        'metrics_prefix': raw_config.get('monitoring', 'metrics_prefix'),
        'grace_period': raw_config.getint('monitoring', 'grace_period')
    },
    'metrics': metrics
}
