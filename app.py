from flask import Flask, request
import json
import os
import io
import requests as http_requests
from PIL import Image
from prometheus_flask_exporter import PrometheusMetrics, Gauge
from datetime import datetime
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import timedelta, timezone

from log import LOGGER
from metrics import StandardMetric
from thing import Thing
from config import config

# Azure configuration from environment variables
AZURE_STORAGE_ACCOUNT_NAME = os.environ['AZURE_STORAGE_ACCOUNT_NAME']
AZURE_STORAGE_ACCOUNT_KEY = os.environ['AZURE_STORAGE_ACCOUNT_KEY']
AZURE_STORAGE_CONTAINER_NAME = os.environ['AZURE_STORAGE_CONTAINER_NAME']
AZURE_AGENT_URL = os.environ['AZURE_AGENT_URL']
AZURE_AGENT_CODE = os.environ['AZURE_AGENT_CODE']
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
    else:
        LOGGER.warning('Skipping prometheus metric %s because it is disabled' % metric)
prom_metrics["last_updated"] = Gauge('%s_%s' % (config['monitoring']['metrics_prefix'], "last_updated"), 'Metric last_updated of a thing', labelnames=['thing'])

prefix = config['monitoring']['metrics_prefix']
prom_string_metrics = {
    'weather_diagnosis':   Gauge('%s_weather_diagnosis' % prefix,   'Weather diagnosis',   labelnames=['thing', 'value']),
    'weather_explanation': Gauge('%s_weather_explanation' % prefix, 'Weather explanation', labelnames=['thing', 'value']),
}
last_string_values = {}

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
    response_json = call_agent(blob_url)
    if response_json is None:
        LOGGER.error('No response from agent, skipping metric extraction')
        return json.dumps(this_thing, default=lambda o: o.__dict__, indent=4)
    for metric_name in config['metrics']:
        if config['metrics'][metric_name]['enabled']:
            LOGGER.info('Getting metric %s of %s' % (metric_name, thing_name))
            standard_metric_obj = get(metric_name, response_json, this_thing)
            if standard_metric_obj is not None:
                set_prom_metric_with_validation(standard_metric_obj, this_thing)
        else:
            LOGGER.warning('Skipping metric %s of %s because it is disabled' % (metric_name, this_thing.get_name()))
    weather_check = response_json.get('weather_check')
    if weather_check:
        set_string_metric('weather_diagnosis', thing_name, weather_check.get('diagnosis'))
        set_string_metric('weather_explanation', thing_name, weather_check.get('explanation'))
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
    sas_token = generate_blob_sas(
        account_name=AZURE_STORAGE_ACCOUNT_NAME,
        container_name=AZURE_STORAGE_CONTAINER_NAME,
        blob_name=blob_name,
        account_key=AZURE_STORAGE_ACCOUNT_KEY,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(minutes=10)
    )
    sas_url = f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_STORAGE_CONTAINER_NAME}/{blob_name}?{sas_token}"
    LOGGER.info('Uploaded image to blob storage: %s' % blob_client.url)
    return sas_url

def call_agent(image_url):
    prompt = AZURE_AGENT_PROMPT.format(image_url=image_url)
    LOGGER.info('Calling agent with image %s' % image_url)
    response = http_requests.post(AZURE_AGENT_URL, params={'code': AZURE_AGENT_CODE}, json={'prompt': prompt}, stream=True)
    response.raise_for_status()
    full_text = ''.join(chunk.decode('utf-8') for chunk in response.iter_content(chunk_size=None) if chunk)
    LOGGER.info('Agent response status: %s' % response.status_code)
    LOGGER.info('Agent response body: %s' % full_text)
    if not full_text:
        LOGGER.error('Agent returned status %s with empty body' % response.status_code)
        return None
    outer = json.loads(full_text)
    response_text = outer.get('response', '')
    # extract JSON object regardless of any surrounding prose or code fences
    start = response_text.find('{')
    end = response_text.rfind('}')
    if start == -1 or end == -1:
        LOGGER.error('No JSON object found in agent response: %s' % response_text)
        return None
    return json.loads(response_text[start:end + 1])

def get_nested(data, path):
    for key in path.split('.'):
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data

def get(metric_name, response_json, thing):
    json_path = config['metrics'][metric_name]['json_path']
    raw_value = get_nested(response_json, json_path)
    if raw_value is None:
        LOGGER.warning('No value for metric %s (json_path: %s)' % (metric_name, json_path))
        return None
    value = float(1 if raw_value is True else 0 if raw_value is False else raw_value)
    if next((True for x in thing.get_metrics() if x.name == metric_name), False):
        standard_metric_obj = next((x for x in thing.get_metrics() if x.name == metric_name), None)
        LOGGER.info('Metric object for %s already exists. Updating values.' % metric_name)
        standard_metric_obj.set_value(value)
    else:
        LOGGER.info('Creating new metric object for %s' % metric_name)
        standard_metric_obj = StandardMetric(metric_name, value, config['metrics'][metric_name]['max_value'], config['metrics'][metric_name]['max_rate'])
        thing.add_metric(standard_metric_obj)
    return standard_metric_obj

def set_string_metric(metric_name, thing_name, new_value):
    if new_value is None:
        return
    key = (metric_name, thing_name)
    old_value = last_string_values.get(key)
    if old_value is not None and old_value != new_value:
        prom_string_metrics[metric_name].labels(thing=thing_name, value=old_value).set(0)
    prom_string_metrics[metric_name].labels(thing=thing_name, value=new_value).set(1)
    last_string_values[key] = new_value
    LOGGER.info('Setting string metric %s to %s' % (metric_name, new_value))

def set_metric(metric, labels, value):
    if value is not None:
        LOGGER.info('Setting prometheus metric %s to %s' % (metric, value))
        metric.labels(labels).set(value)
    else:
        LOGGER.warning('Not setting prometheus metric %s because value is None' % metric)

def set_prom_metric_with_validation(standard_metric_obj, thing):
    if standard_metric_obj.validate():
        set_metric(prom_metrics[standard_metric_obj.get_name()], thing.get_name(), standard_metric_obj.get_value())
        set_metric(prom_metrics["last_updated"], thing.get_name(), standard_metric_obj.get_last_updated())
    else:
        standard_metric_obj.revert_value()

app.run(host='0.0.0.0', port=config['general']['port'])
