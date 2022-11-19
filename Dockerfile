FROM ubuntu:20.04

ENV PYTHONPATH="/"
ENV TZ=Europe/Paris

ARG DEBIAN_FRONTEND=noninteractive

COPY src/*.py src/

COPY --chmod=777 pressreader-cron /var/spool/cron/crontabs/root
COPY  pyproject.toml poetry.lock /
COPY --chmod=777 entrypoint.sh /usr/local/bin

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-distutils python3-pip curl cron vim tzdata && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3 1 && \
    pip3 install --no-cache-dir poetry && poetry update && \
    poetry run pip freeze | xargs pip3 install && \
    playwright install chromium && \
    playwright install-deps chromium &&  \
    # clean apt cache
    apt-get clean && rm -rf /var/lib/apt/lists/*

CMD ["./usr/local/bin/entrypoint.sh"]