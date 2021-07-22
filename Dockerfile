FROM alpine:3.14

USER root
WORKDIR /workdir

RUN apk update
RUN apk add musl-dev gcc
RUN apk add python3 python3-dev py3-pip

COPY ./requirements.txt .
RUN python3 -m pip install -r requirements.txt

COPY ./ta_bot/ ./ta_bot/
CMD ["python3", "-m", "ta_bot"]
