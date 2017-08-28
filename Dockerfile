FROM resin/rpi-raspbian

# Install Graphite, Grafana, Apache, and dupervisord
RUN apt-get update && apt-get upgrade && apt-get install \
      apache2 \
      apache2-utils \
      apt-transport-https \
      collectd \
      gcc \
      libapache2-mod-wsgi \
      libcairo2-dev \
      libffi-dev \
      libssl-dev \
      python \
      python-dev \
      python-pip && \
    apt-get remove python-openssl && \
    pip install pyopenssl supervisor && \
    mkdir /var/log/supervisord && \
    pip install https://github.com/graphite-project/whisper/tarball/master && \
    pip install https://github.com/graphite-project/carbon/tarball/master && \
    pip install https://github.com/graphite-project/graphite-web/tarball/master && \
    sed -i'' -e 's/\(^ *\)\(if hasattr(socket, "SO_REUSEPORT"):\)/\1if False: #\2/' /opt/graphite/lib/carbon/protocols.py && \
    PYTHONPATH=/opt/graphite/webapp django-admin.py migrate \
      --settings=graphite.settings \
      --run-syncdb && \
    echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@admin.com', 'admin')" | PYTHONPATH=/opt/graphite/webapp django-admin.py shell --settings=graphite.settings && \
    echo "deb https://dl.bintray.com/fg2it/deb-rpi-1b jessie main" >> /etc/apt/sources.list && \
    curl -s https://bintray.com/user/downloadSubjectPublicKey?username=bintray | sudo apt-key add - && \
    apt-get update && apt-get install grafana

# Copy over configurations
COPY bin/brewme /usr/lib/brewme
COPY bin/graphite /opt/graphite/bin
COPY conf/graphite /opt/graphite/conf
COPY conf/graphite-web /opt/graphite/webapp/graphite
COPY conf/apache2/ports.conf /etc/apache2/ports.conf
COPY conf/apache2/conf-available /etc/apache2/conf-available
COPY conf/apache2/sites-available /etc/apache2/sites-available
COPY conf/grafana /etc/grafana
COPY conf/collectd/collectd.conf /etc/collectd/collectd.conf
COPY conf/collectd/collectd.conf.d /etc/collectd/collectd.conf.d
COPY conf/collectd/plugins /usr/lib/collectd/plugins
COPY conf/supervisord /etc/supervisor

# Create some users - assign some ownership
RUN groupadd graphite && \
    useradd -g graphite -d /opt/graphite graphite && \
    chown -R graphite. /opt/graphite && \
    chown -R www-data:www-data /opt/graphite/storage/log/webapp

# Run final setup of apache
RUN a2dissite 000-default.conf && \
    a2enmod proxy && \
    a2enmod proxy_http && \
    a2ensite graphite && \
    a2ensite grafana

# Expose the Grafana and Graphite ports
EXPOSE 8080
EXPOSE 80

ENTRYPOINT ["/usr/local/bin/supervisord","--configuration", "/etc/supervisor/supervisord.conf"]
