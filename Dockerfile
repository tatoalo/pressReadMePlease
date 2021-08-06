FROM alpine:latest

RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools

#/etc/crontabs/root

ADD test.py /

#COPY pressreader-cron /etc/cron.d/pressreader-cron
COPY pressreader-cron /var/spool/cron/crontabs/root
COPY entrypoint.sh /usr/local/bin

#RUN chmod +x /etc/cron.d/pressreader-cron
#RUN crontab /etc/cron.d/pressreader-cron

RUN chmod +x /usr/local/bin/entrypoint.sh
RUN chmod +x /var/spool/cron/crontabs/root
RUN touch /var/log/cron.log

# CMD ["crond", "-f"]

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
