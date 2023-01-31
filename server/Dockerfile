# 1 runnign code using python 3.7
FROM python:3.7

# 2 installt he flask stuff
RUN pip install Flask gunicorn

# 3 copy the src file to the work directory
COPY src/ /app
WORKDIR /app

# 4 set the environment variable for the port 8080 (cloud run expects port 8080)
ENV PORT 8080

# 5 run gunicorn bound to 8080 port
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app