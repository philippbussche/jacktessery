# create a flask app with one route for uploading images

from flask import Flask, request, jsonify
from PIL import Image, ImageOps, ImageFilter
from pytesseract import pytesseract
from prometheus_flask_exporter import PrometheusMetrics, Gauge
from datetime import datetime

from log import LOGGER
from metric import Metric
from config import config

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# configuration for prometheus metrics
metrics.info('app_info', 'jacktessery metrics')
# Iterate over all metrics in the config file and create a gauge for each metric and add each gauge to the metrics dictionary
prom_metrics = {}
for metric in config['metrics']:
    if config['metrics'][metric]['enabled']:
        LOGGER.info('Creating prometheus metric %s' % metric)
        prom_metrics[metric] = Gauge('%s_%s' % (config['monitoring']['metrics_prefix'], metric), 'Metric %s of a thing' % metric, labelnames=['thing'])
    else:
        LOGGER.warning('Skipping prometheus metric %s because it is disabled' % metric)
prom_metrics["last_updated"] = Gauge('%s_%s' % (config['monitoring']['metrics_prefix'], "last_updated"), 'Metric last_updated of a thing', labelnames=['thing'])

metric_objects = {}

# general image settings 
SOURCE_IMG = 'source_%s.jpg'

@app.route('/')
def index():
    return "Hello World!"

@app.route('/upload/<thing>', methods=['POST'])
def upload(thing):
    response = {'thing': thing}
    # generate file suffix which is the current timestamp
    suffix = str(int(datetime.now().timestamp()))   
    # get the image file from the request
    file = request.files['image']
    img = Image.open(file.stream)
    if config['general']['save_source_image']:
        src_filename = config['general']['save_image_path'] + "/" + SOURCE_IMG % suffix
        LOGGER.info('Saving source image to %s' % src_filename)
        img.save(src_filename, quality=100, subsampling=0)
    for metric in config['metrics']:
        if config['metrics'][metric]['enabled']:
            LOGGER.info('Getting metric %s of %s' % (metric, thing))
            metric_obj = get(img, config['metrics'], metric, suffix)
            response[metric] = set_prom_metric_with_validation(metric_obj, thing)
        else:
            LOGGER.warning('Skipping metric %s of %s because it is disabled' % (metric, thing))
    return jsonify(response)

def set_metric(metric, label, value):
    if value is not None:
        LOGGER.info('Setting prometheus metric %s to %s' % (metric, value))
        metric.labels(label).set(value)
    else:
        LOGGER.warning('Not setting prometheus metric %s because value is None' % metric)

def get_value(img, lang, config):
    try:
        value = float(pytesseract.image_to_string(img, lang=lang, config=config))
    except ValueError:
        value = None
    return value

def get(img, config, config_key, suffix):
    img = manipulate_image(img, threshold=config[config_key]['threshold'], crop=(config[config_key]['x1'], config[config_key]['y1'], config[config_key]['x2'], config[config_key]['y2']), filename='result_' + config_key + "_" + suffix + ".jpg", suffix=suffix, erode=config[config_key]['erode'], erode_cycles=config[config_key]['erode_cycles'], dilate=config[config_key]['dilate'])
    value = get_value(img, lang=config[config_key]['lang'], config=config[config_key]['config'])
    if config_key in metric_objects:
        metric_obj = metric_objects[config_key]
        LOGGER.info('Metric object for %s already exists. Updating values.' % config_key)
        metric_obj.set_value(value)
    else:
        LOGGER.info('Creating new metric object for %s' % config_key)
        metric_obj = Metric(config_key, value, config[config_key]['max_value'], config[config_key]['max_rate'])
    metric_objects[config_key] = metric_obj
    return metric_obj

def erode_image(cycles, image):
     for _ in range(cycles):
          image = image.filter(ImageFilter.MinFilter(3))
     return image

# function to manipulate the image
def manipulate_image(img, threshold=230, crop=(1730, 1650, 2010, 1890), filename='result.jpg', suffix='', erode=False, erode_cycles=1, dilate=False):
    # convert the image to grayscale
    im_greystyle = ImageOps.grayscale(img) 
    # threshold the image
    LOGGER.info('Thresholding image with threshold %s' % threshold)
    im_threshold = im_greystyle.point(lambda p: p > threshold and 255)
    # crop the image
    LOGGER.info('Cropping image')
    im_crop = im_threshold.crop(crop)
    if erode:
        LOGGER.info('Eroding image with %s cycles' % erode_cycles)
        im_erode = erode_image(erode_cycles, im_crop)
        # invert the image
        im_invert = ImageOps.invert(im_erode)
    elif dilate:
        LOGGER.info('Dilating image')
        im_dilate = im_crop.filter(ImageFilter.MaxFilter(3))
        # invert the image
        im_invert = ImageOps.invert(im_dilate)
    else:
        im_invert = ImageOps.invert(im_crop)
    # add a border of 5 pixels to the image
    im_border = ImageOps.expand(im_invert, border=5, fill='black')
    # save the image to a file 
    if config['general']['save_result_image']:
        dest_filename = config['general']['save_image_path'] + "/" + filename
        LOGGER.info('Saving result image to %s' % dest_filename)
        im_border.save(dest_filename, quality=100, subsampling=0)
    return im_border

def set_prom_metric_with_validation(metric_obj, thing):
    if metric_obj.validate():
        set_metric(prom_metrics[metric_obj.get_name()], thing, metric_obj.get_value())
        set_metric(prom_metrics["last_updated"], thing, metric_obj.get_last_updated())
        return metric_obj.get_value()
    else:
        msg = "metric validation failed. value: %s, previous value: %s, max value: %s, max rate: %s, sample frequency: %s" % (metric_obj.get_value(), metric_obj.get_previous_value(), metric_obj.get_max_value(), metric_obj.get_max_rate(), metric_obj.get_sample_frequency())
        metric_obj.revert_value()
        return msg

app.run(host='0.0.0.0', port=config['general']['port'])

