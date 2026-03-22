from flask import Flask, request
import json
import os
import io
import requests as http_requests
from PIL import Image, ImageOps
from prometheus_flask_exporter import PrometheusMetrics, Gauge
from datetime import datetime
from azure.storage.blob import BlobServiceClient

from log import LOGGER
from metrics import StandardMetric, ConfidenceMetric
from thing import Thing
from config import config

# Azure configuration from environment variables
AZURE_STORAGE_ACCOUNT_NAME = os.environ['AZURE_STORAGE_ACCOUNT_NAME']
AZURE_STORAGE_ACCOUNT_KEY = os.environ['AZURE_STORAGE_ACCOUNT_KEY']
AZURE_STORAGE_CONTAINER_NAME = os.environ['AZURE_STORAGE_CONTAINER_NAME']
AZURE_AGENT_URL = os.environ['AZURE_AGENT_URL']
AZURE_AGENT_PROMPT = os.environ['AZURE_AGENT_PROMPT']

blob_service_client = BlobServiceClient(
    account_url=f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
    credential=AZURE_STORAGE_ACCOUNT_KEY
)

app = Flask(__name__)
metrics_exporter = PrometheusMetrics(app)

metrics_exporter.info('app_info', 'jacktessery metrics')
prom_metrics = {}
for metric in config['metrics']:
    if config['metrics'][metric]['enabled']:
        LOGGER.info('Creating prometheus metric %s' % metric)
        prom_metrics[metric] = Gauge('%s_%s' % (config['monitoring']['metrics_prefix'], metric), 'Metric %s of a thing' % metric, labelnames=['thing'])
        prom_metrics[metric + "_confidence"] = Gauge('%s_%s' % (config['monitoring']['metrics_prefix'], metric + "_confidence"), 'Metric %s confidence of a thing' % metric, labelnames=['thing'])
    else:
        LOGGER.warning('Skipping prometheus metric %s because it is disabled' % metric)
prom_metrics["last_updated"] = Gauge('%s_%s' % (config['monitoring']['metrics_prefix'], "last_updated"), 'Metric last_updated of a thing', labelnames=['thing'])

monitored_things = {}

SOURCE_IMG = 'source_%s.jpg'

@app.route('/')
def index():
    return "Hello World!"

@app.route('/upload/<thing_name>', methods=['POST'])
def upload(thing_name):
    if thing_name not in monitored_things:
        this_thing = Thing(thing_name)
        monitored_things[thing_name] = this_thing
    else:
        this_thing = monitored_things[thing_name]
    suffix = str(int(datetime.now().timestamp()))
    file = request.files['image']
    img = Image.open(file.stream)
    if config['general']['save_source_image']:
        src_filename = config['general']['save_image_path'] + "/" + SOURCE_IMG % suffix
        LOGGER.info('Saving source image to %s' % src_filename)
        img.save(src_filename, quality=100, subsampling=0)
    blob_url = upload_to_blob(img, SOURCE_IMG % suffix)
    for metric_name in config['metrics']:
        if config['metrics'][metric_name]['enabled']:
            LOGGER.info('Getting metric %s of %s' % (metric_name, thing_name))
            standard_metric_obj = get(metric_name, blob_url, this_thing)
            if standard_metric_obj is not None:
                set_prom_metric_with_validation(standard_metric_obj, this_thing)
        else:
            LOGGER.warning('Skipping metric %s of %s because it is disabled' % (metric_name, this_thing.get_name()))
    return json.dumps(this_thing, default=lambda o: o.__dict__, indent=4)

def upload_to_blob(img, blob_name):
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=100, subsampling=0)
    img_bytes.seek(0)
    blob_client = blob_service_client.get_blob_client(
        container=AZURE_STORAGE_CONTAINER_NAME,
        blob=blob_name
    )
    blob_client.upload_blob(img_bytes, overwrite=True)
    LOGGER.info('Uploaded image to blob storage: %s' % blob_client.url)
    return blob_client.url

def call_agent(metric_name, image_url):
    prompt = AZURE_AGENT_PROMPT.format(metric_name=metric_name, image_url=image_url)
    LOGGER.info('Calling agent for metric %s with image %s' % (metric_name, image_url))
    response = http_requests.post(AZURE_AGENT_URL, json={'prompt': prompt})
    response.raise_for_status()
    return response.text.strip()

def get(metric_name, blob_url, thing):
    try:
        response_text = call_agent(metric_name, blob_url)
        value = int(float(response_text))
    except Exception as e:
        LOGGER.warning('Error getting metric %s from agent: %s' % (metric_name, e))
        return None
    confidence = 100
    if next((True for x in thing.get_metrics() if x.name == metric_name), False):
        standard_metric_obj = next((x for x in thing.get_metrics() if x.name == metric_name), None)
        LOGGER.info('Metric object for %s already exists. Updating values.' % metric_name)
        standard_metric_obj.set_value(value)
        standard_metric_obj.get_confidence_metric().set_value(confidence)
    else:
        LOGGER.info('Creating new metric object for %s' % metric_name)
        standard_metric_obj = StandardMetric(metric_name, value, config['metrics'][metric_name]['max_value'], config['metrics'][metric_name]['max_rate'])
        confidence_metric_obj = ConfidenceMetric(metric_name + "_confidence", confidence, config['metrics'][metric_name]['min_confidence'])
        standard_metric_obj.set_confidence_metric(confidence_metric_obj)
        thing.add_metric(standard_metric_obj)
    return standard_metric_obj

def set_metric(metric, labels, value):
    if value is not None:
        LOGGER.info('Setting prometheus metric %s to %s' % (metric, value))
        metric.labels(labels).set(value)
    else:
        LOGGER.warning('Not setting prometheus metric %s because value is None' % metric)

def set_prom_metric_with_validation(standard_metric_obj, thing):
    if standard_metric_obj.validate() and standard_metric_obj.get_confidence_metric().validate():
        set_metric(prom_metrics[standard_metric_obj.get_name()], thing.get_name(), standard_metric_obj.get_value())
        set_metric(prom_metrics[standard_metric_obj.get_name() + "_confidence"], thing.get_name(), standard_metric_obj.get_confidence_metric().get_value())
        set_metric(prom_metrics["last_updated"], thing.get_name(), standard_metric_obj.get_last_updated())
    else:
        standard_metric_obj.revert_value()

app.run(host='0.0.0.0', port=config['general']['port'])
