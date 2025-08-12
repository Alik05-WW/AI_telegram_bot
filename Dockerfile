FROM python:3.11

RUN apt-get update && apt-get install -y tesseract-ocr libtesseract-dev

WORKDIR /app

COPY bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot/ .

CMD ["python", "main.py"]