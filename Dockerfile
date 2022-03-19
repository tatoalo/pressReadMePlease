FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive
ARG TZ=Europe/London

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-distutils python3-pip curl cron vim && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3 1 && \
    pip3 install --no-cache-dir playwright==1.20.0 python-dotenv==0.19.0 requests==2.26.0 &&  \
    playwright install chromium && \
    playwright install-deps chromium &&  \
    # clean apt cache
    apt-get clean && rm -rf /var/lib/apt/lists/*

ADD src/*.py src/
WORKDIR /src

COPY --chmod=777 pressreader-cron /var/spool/cron/crontabs/root
COPY --chmod=777 entrypoint.sh /usr/local/bin

RUN crontab /var/spool/cron/crontabs/root

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
