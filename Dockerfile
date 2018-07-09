FROM python:3.6-stretch
MAINTAINER Blaize Berry "blaizeberry@gmail.com"


ENV APP_HOST=0.0.0.0
ENV APP_PORT=80
ENV APP_DIR=/app

COPY . /app
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends openssl libblas-dev liblapack-dev
RUN pip install --no-cache -r requirements.txt

EXPOSE $APP_PORT

ENTRYPOINT ["python"]
CMD ["app.py"]
