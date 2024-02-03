import time
from log import LOGGER
from config import config

class Metric:
    def __init__(self, name, value):
        self.name = name
        self.previous_value = None
        self.value = value
        self.last_updated = round(time.time(), 0)
        self.sample_frequency = 0

    # get the metric name
    def get_name(self):
        return self.name
    
    # get the metric value
    def get_value(self):
        return self.value
    
    # get the metric previous value
    def get_previous_value(self):
        return self.previous_value
    
    # get last updated
    def get_last_updated(self):
        return self.last_updated
    
    # get sample frequency
    def get_sample_frequency(self):
        return self.sample_frequency
    
    # set the metric value
    def set_value(self, value):
        self.set_previous_value(self.value)
        LOGGER.info('Setting metric %s value to %s' % (self.name, value))
        self.value = value
        self.set_sample_frequency(time.time() - self.get_last_updated())
        self.set_last_updated(time.time())

     # set the metric previous value
    def set_previous_value(self, previous_value):
        LOGGER.info('Setting metric %s previous value to %s' % (self.name, previous_value))
        self.previous_value = previous_value

    # revert the metric value
    def revert_value(self):
        LOGGER.info('Reverting metric %s value to %s' % (self.name, self.previous_value))
        self.value = self.previous_value

    # set the metric last updated
    def set_last_updated(self, last_updated):
        rounded_last_updated = round(last_updated,0)
        LOGGER.info('Setting metric %s last updated to %s' % (self.name, rounded_last_updated))
        self.last_updated = rounded_last_updated

    # set the metric sample frequency
    def set_sample_frequency(self, sample_frequency):
        rounded_sample_frequency = round(sample_frequency,0)
        LOGGER.info('Setting metric %s sample frequency to %s' % (self.name, rounded_sample_frequency))
        self.sample_frequency = rounded_sample_frequency

class StandardMetric(Metric):
    def __init__(self, name, value, max_value, max_rate):
        super().__init__(name, value)
        self.max_value = max_value
        self.max_rate = max_rate

    # get max value
    def get_max_value(self):
        return self.max_value
    
    # get max rate
    def get_max_rate(self):
        return self.max_rate

    def set_confidence_metric(self, confidence_metric):
       self.confidence_metric = confidence_metric
    
    def get_confidence_metric(self):
       return self.confidence_metric
    
    # return boolean if metric value is higher than max value
    def is_value_higher_than_max_value(self):
        if self.value is None:
            return False
        return self.value > self.max_value
    
    # return boolean if metric value is lower than 0
    def is_value_lower_than_zero(self):
        if self.value is None:
            return False
        return self.value < 0
    
    # return boolean if metric delta is higher than max rate
    def is_delta_higher_than_max_rate(self):
        if self.previous_value is None or self.value is None:
            return False
        return abs(self.value - self.previous_value) > self.max_rate
    
    # validate the metric value
    def validate(self):
        if self.is_value_higher_than_max_value() or self.is_value_lower_than_zero():
            LOGGER.warning('Metric %s is not valid' % self.name)
            LOGGER.warning('Metric %s is higher than max value or lower than 0 (metric value: %s).' % (self.name, self.value))
            return False
        else:
            if self.is_delta_higher_than_max_rate() and self.get_sample_frequency() < config['monitoring']['grace_period']:
                LOGGER.warning('Metric %s is not valid' % self.name)
                LOGGER.warning('Delta for metric %s is higher than max rate but has a sample frequency within the grace period (delta value: %s, max rate: %s, sample frequency: %s, grace period: %s).' % (self.name, abs(self.value - self.previous_value), self.max_rate, round(self.get_sample_frequency(), 0), config['monitoring']['grace_period']))
                return False
            else:
                LOGGER.info('Metric %s is valid' % self.name)
                return True
    
class ConfidenceMetric(Metric):
    def __init__(self, name, value, min_value):
        super().__init__(name, value)
        self.min_value = min_value

    # get min value
    def get_min_value(self):
        return self.min_value
    
    def is_value_lower_than_min_value(self):
        if self.value is None:
            return False
        return self.value < self.min_value
    
    def validate(self):
        if self.is_value_lower_than_min_value():
            LOGGER.warning('Metric %s is not valid' % self.name)
            LOGGER.warning('Metric %s is lower than min value (metric value: %s, min value: %s).' % (self.name, self.value, self.min_value))
            return False
        else:
            LOGGER.info('Metric %s is valid' % self.name)
            return True
        