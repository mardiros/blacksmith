FROM nginx:1.21.6-alpine

RUN apk update && \
    apk add -u consul-template && \
    rm -rf /tmp/* /var/tmp/* /var/cache/apk/*

ADD templates /etc/nginx/templates
ADD watch.sh /
RUN chmod 755 watch.sh
ADD index.html /srv

CMD /watch.sh
