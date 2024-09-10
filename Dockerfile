FROM python:3.10

WORKDIR .
COPY Pipfile .
COPY Pipfile.lock .
RUN pip install pipenv
RUN pipenv install --system --deploy

COPY . .

ENV DB_URL='mysql://user:pass@172.20.0.1:3307/wallets'
ENV PYTHONBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=app.settings

RUN alembic upgrade head

CMD ["python3.10", "app/manage.py", "runserver", "0.0.0.0:8080" ]

