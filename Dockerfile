FROM python
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
CMD gunicorn --worker-class eventlet -w 1 app:app