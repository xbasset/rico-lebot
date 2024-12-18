FROM python:3.9

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y \
    supervisor \
    gcc \
    build-essential \
    python3-dev \
    libffi-dev

RUN pip install --no-cache-dir -r requirements.txt

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 5001

CMD ["supervisord", "-n"]