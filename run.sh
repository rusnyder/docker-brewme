#!/usr/bin/env bash

USER=admin
PASSWORD=admin
GRAFANA_HOST=localhost:3000

add_data_source() {
  curl http://${USER}:${PASSWORD}@${GRAFANA_HOST}/api/datasources \
    -XPOST \
    -H"Content-Type:application.json;charset=UTF-8" \
    -d '{
      "name": "graphite",
      "type": "graphite",
      "url": "http://localhost:8080",
      "access": "proxy",
      "isDefault": true
    }'
}

load_dashboard() {
  local file="$1"
  curl http://${USER}:${PASSWORD}@${GRAFANA_HOST}/api/dashboards/db \
    -XPOST \
    -H"Content-Type:application.json;charset=UTF-8" \
    -d @$file
}
