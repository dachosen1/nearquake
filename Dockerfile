FROM python:3.8.6

WORKDIR /usr/src/app

COPY ./requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

ENTRYPOINT python3 run_post_daily_quakes.py