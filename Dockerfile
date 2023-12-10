FROM python:3.10

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install protobuf
RUN pip install protobuf

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

COPY . .

CMD ["python", "./main.py"]