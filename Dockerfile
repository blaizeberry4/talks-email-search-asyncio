FROM python:3.6.4-alpine
MAINTAINER Blaize Berry "blaizeberry@gmail.com"


ENV APP_HOST=0.0.0.0
ENV APP_PORT=80
ENV APP_DIR=/app

COPY . /app
WORKDIR /app


RUN pip install -r requirements.txt

EXPOSE $APP_PORT

ENTRYPOINT ["python"]
CMD ["app.py"]
