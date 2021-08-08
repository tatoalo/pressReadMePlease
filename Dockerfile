FROM alpine:3.14

RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN apk add chromium --repository=http://dl-cdn.alpinelinux.org/alpine/v3.14/main
RUN apk add chromium-chromedriver
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools
RUN pip3 install selenium

ADD src/*.py src/

COPY pressreader-cron /var/spool/cron/crontabs/root
COPY entrypoint.sh /usr/local/bin

RUN chmod +x /usr/local/bin/entrypoint.sh
RUN chmod +x /var/spool/cron/crontabs/root

RUN touch /var/log/pressreader-automation.log

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
