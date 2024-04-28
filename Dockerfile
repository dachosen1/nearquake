FROM python:3.12.3-slim

RUN apt-get update && apt-get -y install cron

WORKDIR /usr/src/app

COPY ./requirements.txt .

RUN  pip3 install --no-cache-dir --upgrade pip \
    -r requirements.txt

COPY . /usr/src/app

# Add crontab file in the cron directory
COPY crontab /etc/cron.d/my-cron-job

RUN chmod 0644 /etc/cron.d/my-cron-job && crontab /etc/cron.d/my-cron-job && touch /var/log/cron.log

CMD cron && tail -f /var/log/cron.log