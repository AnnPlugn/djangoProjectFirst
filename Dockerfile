
FROM python:3.10
ENV PYTHONUNBUFFERED 1
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
ADD . /djangoProjectFirst/