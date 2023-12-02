FROM nginx:1.25.3-alpine3.18

RUN apk update && \
    apk add -u consul-template && \
    rm -rf /tmp/* /var/tmp/* /var/cache/apk/*

ADD templates /etc/nginx/templates
ADD watch.sh /
RUN chmod 755 watch.sh
ADD index.html /srv

CMD /watch.sh
