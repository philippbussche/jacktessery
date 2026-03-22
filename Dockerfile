FROM python:3.11-slim-bullseye

RUN pip3 install --upgrade pip

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN mkdir /tmp_images
COPY config.py /config.py
COPY config.properties /config.properties
COPY app.py /app.py
COPY metrics.py /metrics.py
COPY log.py /log.py
COPY thing.py /thing.py

CMD ["python3", "/app.py"]
