Docker BrewMe
=============

Docker image containing a Graphite + Grafana + CollectD monitoring stack
built on a Raspbian.

This is less-than-useful as is and just serves as a reference for installing
an equivalent monitoring stack on an actual Raspberry Pi.

Quickstart
==========

You can build and run this simple enough!  All configuration is self-contained
and there is nothing configurable via environment variables or anything fancy
like that:

```shell
# Build the docker image
docker build -t brewme .

# Run it, binding port 80 (grafana) and optionally port 8080 (graphite)
docker run -it -p 9090:80 brewme

# Open Grafana in your browser (may take a minute to come up)
open http://localhost:9090
```

At that point, Grafana should be accessible on whatever port you bind
it to (port 9090, in the example) and you can login in your browser
and get started: http://localhost:9090
