nginx &

consul-template -consul-addr consul:8500 -wait 3s -template "/etc/nginx/templates/default.conf.ctmpl:/etc/nginx/conf.d/default.conf:/usr/sbin/nginx -s reload"
