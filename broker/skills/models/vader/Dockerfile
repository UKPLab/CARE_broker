FROM broker_simple_skill

WORKDIR /app

RUN pip3 install nltk
RUN python -m nltk.downloader all

COPY Skill.py Skill.py