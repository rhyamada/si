FROM python
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
CMD sed -n 's/web: //p' Procfile | sh