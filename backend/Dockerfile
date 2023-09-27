FROM python:3.8-slim

WORKDIR /app

COPY . /app
RUN pip install -r requirements.txt
EXPOSE 5000

CMD [ "flask", "--app", "hello", "run", "--host=0.0.0.0" ]