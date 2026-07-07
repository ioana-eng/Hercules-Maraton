FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py /app/
COPY index.html /app/
COPY editie.html /app/
COPY cros.html /app/
COPY semimaraton.html /app/
COPY maraton.html /app/
COPY kids.html /app/
COPY declaratii.html /app/
COPY assets /app/assets

EXPOSE 80

CMD ["python", "app.py"]
