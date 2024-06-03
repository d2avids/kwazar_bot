FROM python:3.10-alpine
WORKDIR /kwazar_bot
COPY . /kwazar_bot
MAINTAINER David Saidov 'delightxxls@gmail.com'
RUN pip3 install --upgrade setuptools
RUN pip3 install -r requirements.txt
RUN chmod 755 .
CMD ["python", "main.py"]