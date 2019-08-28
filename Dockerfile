FROM python
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
#CMD ["python","app.py","--host=0.0.0.0"]
CMD ["gunicorn","-k","flask_sockets.worker","chat:app"]