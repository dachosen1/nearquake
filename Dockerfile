FROM python:3.12.3-slim

RUN apt-get update && apt-get -y install cron

WORKDIR /usr/src/app

COPY ./requirements.txt .

RUN  pip3 install --no-cache-dir --upgrade pip \
    -r requirements.txt

COPY . /usr/src/app

# Add crontab file in the cron directory
ADD crontab /etc/cron.d/my-cron-job

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/my-cron-job

# Apply cron job
RUN crontab /etc/cron.d/my-cron-job

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Run the command on container startup
CMD cron && tail -f /var/log/cron.log