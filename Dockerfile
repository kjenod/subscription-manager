FROM continuumio/miniconda3:latest

LABEL maintainer="SWIM EUROCONTROL <http://www.eurocontrol.int>"

ENV PATH="/opt/conda/envs/app/bin:$PATH"
RUN echo "deb http://archive.ubuntu.com/ubuntu trusty main restricted" >> /etc/apt/sources.list
RUN apt-get update -y; apt-get upgrade -y
RUN apt-get install build-essential pkg-config openssl libssl-dev libsasl2-2 libsasl2-dev libsasl2-modules libffi-dev python3-setuptools gcc-4.8 -y --allow-unauthenticated


RUN mkdir -p /app
WORKDIR /app

# for some reason uwsgi cannot compile with later versions of gcc
ENV CC=gcc-4.8

COPY requirements.yml requirements.yml
RUN conda env create --name app -f requirements.yml

ENV CC=gcc

COPY ./subscription_manager/ ./subscription_manager/

COPY . /source/
RUN set -x \
    && pip install /source \
    && rm -rf /source

ENV LD_LIBRARY_PATH=/opt/conda/lib:$LD_LIBRARY_PATH

CMD ["python", "/app/subscription_manager/app.py"]
