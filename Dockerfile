FROM php:7.4-fpm
# FROM php:8.0-fpm

LABEL maintainer="emil@jacero.se"

ARG DEBIAN_FRONTEND=noninteractive
ARG APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn
ARG DNS_UI_VERSION=v0.2.7

# Install php extension build deps
RUN apt-get update -y \
    && apt-get upgrade -yq --no-install-recommends --no-install-suggests \
    && apt-get install -yq --no-install-recommends --no-install-suggests tzdata curl wget gnupg2 jq dnsutils python3 python3-pip python3-psycopg2 \
    libldb-dev libldap2-dev libcurl4-openssl-dev libicu-dev libpq-dev postgresql-client netcat \
    && sed -i -e '$a\deb http://deb.debian.org/debian bullseye main' /etc/apt/sources.list \
    && apt-get update -y \
    && apt-get install -yq --no-install-recommends --no-install-suggests ssmtp \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && ln -s /usr/lib/x86_64-linux-gnu/libldap.so /usr/lib/libldap.so \
    && ln -s /usr/lib/x86_64-linux-gnu/liblber.so /usr/lib/liblber.so \
    && sed -i -e 's/^.*FromLineOverride=.*$/FromLineOverride=YES/' /etc/ssmtp/ssmtp.conf \
    && ( echo "sendmail_path = /usr/sbin/ssmtp -t" > /usr/local/etc/php/conf.d/docker-php-mail.ini )

RUN docker-php-ext-install pdo_pgsql pgsql ldap intl

# Install Caddy
RUN curl --silent --show-error --fail --location \
    --header "Accept: application/tar+gzip, application/x-gzip, application/octet-stream" -o - \
    "https://github.com/caddyserver/caddy/releases/download/v1.0.4/caddy_v1.0.4_linux_amd64.tar.gz" \
    | tar --no-same-owner -C /usr/bin/ -xz caddy \
    && chmod 0755 /usr/bin/caddy \
    && /usr/bin/caddy -version

# Install dns-ui
RUN mkdir -p /srv/dns-ui \
    && cd /srv/dns-ui \
    && curl --silent --show-error --fail --location \
    -o - "https://github.com/operasoftware/dns-ui/archive/refs/tags/$DNS_UI_VERSION.tar.gz" \
    | tar --strip-components=1 -xz \
    && chown -R www-data:www-data .

# Set timezone
ENV TZ=Etc/UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Installing python modules
ADD requirements.txt /
RUN pip3 install -r /requirements.txt

# Prepare directories
RUN mkdir /data && mkdir /app

COPY src/Caddyfile /etc/Caddyfile
ADD src /app

EXPOSE 80
WORKDIR /app
STOPSIGNAL SIGTERM
ENTRYPOINT ["/app/entrypoint.py"]

VOLUME /data
