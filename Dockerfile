FROM python:3.11.6-slim

RUN mkdir -p /opt/dagster/dagster_home /opt/dagster/app

WORKDIR /opt/dagster/app

COPY ./requirements.txt .

RUN  pip3 install --no-cache-dir --upgrade pip \
    -r requirements.txt

COPY . /opt/dagster/app/

ENV DAGSTER_HOME=/opt/dagster/dagster_home/

EXPOSE 3000

ENTRYPOINT ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000"]
