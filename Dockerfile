FROM python:3.11.6-slim

RUN apt-get update

WORKDIR /usr/src/app

COPY ./requirements.txt .

RUN  pip3 install --no-cache-dir --upgrade pip \
    -r requirements.txt

COPY . /usr/src/app

ENTRYPOINT [ "python3", "main.py" ]