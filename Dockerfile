FROM python:3.10.8-slim-bullseye
ARG ENV
ENV ENV=$ENV

# echo build type
RUN echo "ENV=$ENV"

# COPY SERVER CODE
WORKDIR /
ADD . /broker
WORKDIR broker

# INSTALL Requirements
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Generate private key if not exists
RUN if [ ! -f /broker/private_key.pem ]; then \
    openssl genrsa -out /broker/private_key.pem 2048; fi

# Add current dir to python path
ENV PYTHONPATH="${PYTHONPATH}:/broker"

CMD ["python3", "broker/app.py"]