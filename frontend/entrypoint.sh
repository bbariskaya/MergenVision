#!/bin/sh
set -e

sed -i "s|API_BASE_URL_PLACEHOLDER|${API_BASE_URL}|g" /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
