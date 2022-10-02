FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive
ARG TZ=Europe/London

COPY src/*.py src/
WORKDIR /src

COPY --chmod=777 pressreader-cron /var/spool/cron/crontabs/root
COPY --chmod=777 entrypoint.sh /usr/local/bin

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-distutils python3-pip curl cron vim && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3 1 && \
    pip3 install --no-cache-dir playwright==1.26.1 python-dotenv==0.21.0 requests==2.28.1 &&  \
    playwright install chromium && \
    playwright install-deps chromium &&  \
    # clean apt cache
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    crontab /var/spool/cron/crontabs/root

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
