FROM python:3.7.7
WORKDIR /app
ADD requirements.txt /app
RUN set -ex && \
    pip install --no-cache-dir -r requirements.txt
ADD . /app

USER www-data
CMD python3 monitor.py 7778 7777