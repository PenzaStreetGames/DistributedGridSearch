FROM python:3

WORKDIR /usr/src/app

COPY ./subtask .
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./subtask.py" ]
