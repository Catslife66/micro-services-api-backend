FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN python -m venv /venv

RUN /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install -r requirements.txt

ENV PATH="/venv/bin:$PATH"

EXPOSE 8000

CMD ["/bin/sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]