FROM python:3.7.6

WORKDIR /code/

RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple

ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code

CMD ["python3", "-u", "main.py"]