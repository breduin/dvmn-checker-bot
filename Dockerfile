FROM python:3.10

WORKDIR /app

COPY *.py ./
COPY requirements.txt ./
RUN pip install -U pip && pip install -r requirements.txt

ENTRYPOINT ["python", "bot.py"]