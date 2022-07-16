FROM bitnami/spark:3.1.3-debian-11-r0

USER root

COPY requirements.txt /opt/bitnami/spark/requirements.txt

RUN pip install --upgrade pip
RUN pip install -r /opt/bitnami/spark/requirements.txt
