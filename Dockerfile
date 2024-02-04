FROM python:3.8-slim-buster

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    libpng-dev \
    libjpeg-dev \
    libtiff-dev \
    zlib1g-dev \
    python3-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN mkdir /data && mkdir /tmp_images
COPY data/ssd_alphanum_plus.traineddata /data/ssd_alphanum_plus.traineddata
COPY config.py /config.py
COPY config.properties /config.properties
COPY app.py /app.py
COPY metrics.py /metrics.py
COPY log.py /log.py
COPY thing.py /thing.py

ENV TESSDATA_PREFIX=/data

CMD ["python3", "/app.py"]