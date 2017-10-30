FROM vkushnir/oracle-instantclient:python2.7.11-1
MAINTAINER Vladimir Kushnir <v_kushnir@outlook.com>
LABEL description = "Switch ISG services for active users" \
      version = "v0.4"

ARG APP_HOME="/opt/isg"

ENV DB_ADDRESS=localhost \
    DB_NAME=radius \
    DB_USER=radius \
    DB_PASSWORD=password \
    DB_MIN=2 \
    DB_MAX=20 \
    DB_INC=2 \
    THREADS_MAX=20 \
    RADIUS_SECRET=secret \
    RADIUS_COAPORT=1700 \
    RADIUS_AUTHPORT=1812 \
    RADIUS_ACCTPORT=1813 \
    LOG_LEVEL=INFO \
    PYTHONPATH=/opt/isg

RUN apt-get update && \
    apt-get install -y python-pip && \
    python -m pip install pyrad --upgrade && \
    apt-get purge -y python-pip && \
    apt-get autoremove -y && \
    apt-get autoclean -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR ${APP_HOME}
COPY localtime /etc
COPY app/*.py ${APP_HOME}/
COPY app/dictionary/* ${APP_HOME}/dictionary/

RUN python -m compileall ${APP_HOME}

VOLUME /var/log/isg

ENTRYPOINT ["python2"]
CMD ["${APP_HOME}/isg.pyc"]
