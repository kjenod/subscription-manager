FROM swim-base.conda

LABEL maintainer="SWIM EUROCONTROL <http://www.eurocontrol.int>"

ENV PATH="/opt/conda/envs/app/bin:$PATH"
ENV DB_NAME='smdb'

RUN mkdir -p /app
WORKDIR /app

COPY requirements.yml requirements.yml
RUN conda env create --name app -f requirements.yml

COPY ./subscription_manager/ ./subscription_manager/
COPY ./provision ./provision/

COPY . /source/
RUN set -x \
    && pip install /source \
    && rm -rf /source

RUN groupadd -r swim && useradd --no-log-init -md /home/swim -r -g swim swim

RUN chown -R swim:swim /app

USER swim

CMD ["python", "/app/subscription_manager/app.py"]
