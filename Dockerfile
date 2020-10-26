FROM python:3.6
RUN apt-get update
ENV PYTHONUNBUFFERED 1
RUN mkdir /FFXIVBOT
WORKDIR /FFXIVBOT
ADD  requirements.txt /FFXIVBOT/
# RUN curl -l https://tuna.moe/oh-my-tuna/oh-my-tuna.py | python  # Remove this line if your server is located outside of mainland China
RUN pip install -r requirements.txt
ADD . /FFXIVBOT/
# change to docker verison
RUN mv /FFXIVBOT/FFXIV/settings_example.py /FFXIVBOT/FFXIV/settings.py
RUN mv /FFXIVBOT/ffxivbot/config_example.json /FFXIVBOT/ffxivbot/config.json
RUN sed -i 's/("127.0.0.1", 6379)/("redis", 6379)/' /FFXIVBOT/FFXIV/settings.py
RUN sed -i 's/127.0.0.1/db/' /FFXIVBOT/FFXIV/settings.py
RUN sed -i "s/'USER': 'FFXIV_DEV'/'USER': 'root'/" /FFXIVBOT/FFXIV/settings.py
RUN sed -i "s/'PASSWORD': 'PASSWORD'/'PASSWORD': 'root'/" /FFXIVBOT/FFXIV/settings.py
RUN sed -i 's/127.0.0.1/rabbit/' /FFXIVBOT/ffxivbot/consumers.py
RUN sed -i 's/localhost/rabbit/' /FFXIVBOT/ffxivbot/pika_rabbit.py
RUN sed -i 's/localhost/redis/' /FFXIVBOT/ffxivbot/handlers/QQGroupChat.py
RUN sed -i 's/localhost/redis/' /FFXIVBOT/ffxivbot/handlers/QQGroupCommand_wordcloud.py
EXPOSE 8002
