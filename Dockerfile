FROM python:3.6-stretch

WORKDIR /usr/src/app

RUN adduser --system oca-github-bot

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install -e .

USER oca-github-bot
WORKDIR /home/oca-github-bot
