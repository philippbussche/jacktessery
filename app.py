# create a flask app with one route for uploading images

from flask import Flask, request
import json
from PIL import Image, ImageOps, ImageFilter
from pytesseract import pytesseract
from prometheus_flask_exporter import PrometheusMetrics, Gauge
from datetime import datetime

from log import LOGGER
from metrics import StandardMetric, ConfidenceMetric
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
        prom_metrics[metric + "_confidence"] = Gauge('%s_%s' % (config['monitoring']['metrics_prefix'], metric + "_confidence"), 'Metric %s confidence of a thing' % metric, labelnames=['thing'])
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
    response = {'thing': thing, 'metrics': []}
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
            standard_metric_obj = get(img, config['metrics'], metric, suffix)
            if standard_metric_obj is not None:
                set_prom_metric_with_validation(standard_metric_obj, thing)
                response["metrics"].append(standard_metric_obj)
        else:
            LOGGER.warning('Skipping metric %s of %s because it is disabled' % (metric, thing))
    return json.dumps(response, default=lambda o: o.__dict__, indent=4)

def set_metric(metric, labels, value):
    if value is not None:
        LOGGER.info('Setting prometheus metric %s to %s' % (metric, value))
        metric.labels(labels).set(value)
    else:
        LOGGER.warning('Not setting prometheus metric %s because value is None' % metric)

def get_value(img, lang, config):
    try:
        value = float(pytesseract.image_to_string(img, lang=lang, config=config))
    except ValueError:
        value = None
    return value

def get_data(img, lang, config):
    try:
        data = pytesseract.image_to_data(img, lang=lang, config=config, output_type=pytesseract.Output.DICT)
    except ValueError:
        data = None
    return data

def get(img, config, config_key, suffix):
    img = manipulate_image(img, threshold=config[config_key]['threshold'], crop=(config[config_key]['x1'], config[config_key]['y1'], config[config_key]['x2'], config[config_key]['y2']), filename='result_' + config_key + "_" + suffix + ".jpg", suffix=suffix, erode=config[config_key]['erode'], erode_cycles=config[config_key]['erode_cycles'], dilate=config[config_key]['dilate'])
    data = get_data(img, lang=config[config_key]['lang'], config=config[config_key]['config'])
    if len(data['text']) < 5 or len(data['conf']) < 5:
        LOGGER.warning('No value detected for metric %s' % config_key)
        return None
    else:
        confidence = data['conf'][4]
        value_from_data = int(data['text'][4])
        if config_key in metric_objects:
            standard_metric_obj = metric_objects[config_key]
            LOGGER.info('Metric object for %s already exists. Updating values.' % config_key)
            standard_metric_obj.set_value(value_from_data)
            standard_metric_obj.get_confidence_metric().set_value(confidence)
        else:
            LOGGER.info('Creating new metric object for %s' % config_key)
            standard_metric_obj = StandardMetric(config_key, value_from_data, config[config_key]['max_value'], config[config_key]['max_rate'])
            confidence_metric_obj = ConfidenceMetric(config_key + "_confidence", confidence, config[config_key]['min_confidence'])
            standard_metric_obj.set_confidence_metric(confidence_metric_obj)
        metric_objects[config_key] = standard_metric_obj
        return standard_metric_obj

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

def set_prom_metric_with_validation(standard_metric_obj, thing):
    if standard_metric_obj.validate() and standard_metric_obj.get_confidence_metric().validate():
        set_metric(prom_metrics[standard_metric_obj.get_name()], thing, standard_metric_obj.get_value())
        set_metric(prom_metrics[standard_metric_obj.get_name() + "_confidence"], thing, standard_metric_obj.get_confidence_metric().get_value())
        set_metric(prom_metrics["last_updated"], thing, standard_metric_obj.get_last_updated())
    else:
        standard_metric_obj.revert_value()

app.run(host='0.0.0.0', port=config['general']['port'])

