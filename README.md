# opera-dns-ui

## Summary

A self contained docker image with php-fpm & caddy for [Opera's PowerDNS Admin UI](https://github.com/operasoftware/dns-ui)

This image is intended to be used behind some form of reverse proxy responsible for Authentication. The proxy should set an `X-Auth-User` header with the authenticated username for the application.

An initial user is created during database initialisation by the application, specified by the `ADMIN_USER` environment variable.

## Examples

### docker-compose with external PowerDNS Authorative

#### TODO: COMPLETE THIS

Using traefik as reverse proxy

```yaml
version: '3'
networks:
  proxy:
    ipam:
      driver: default
      config:
        - subnet: "192.168.254.0/28"
services:
  proxy:
    image: traefik:v2.5
    container_name: proxy
    restart: always
    command:
      - "--providers.docker=true"
      - "--providers.docker.endpoint=unix:///var/run/docker.sock"
    labels:
      
    networks:
      - proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
  dnsui:
    image: emiljacero/opera-dnsui:v0.2.7
    container_name: dnsui
    networks:
      - proxy
    ports:
      - 8080:80/tcp
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.entrypoints=web-secure"
      - "traefik.http.middlewares.dns-auth.basicauth.users=admin:$$apr1$$H6uskkkW$$IgXLP6ewTrSuBkTrqE8wj/"
      - "traefik.http.middlewares.my-auth.basicauth.headerField=X-Auth-User"
      - "traefik.http.routers.dnsui.rule=Host(`dns-admin.example.com`)"
      - "traefik.http.routers.dnsui.tls=true"
      - "traefik.http.routers.dnsui.tls.certresolver=digitalocean_resolver"  # ADD RESOVLER ABOVE
      - "traefik.http.routers.dnsui.tls.domains[0].main=dns-admin.example.com"
      - "traefik.http.routers.dnsui.middlewares=dns-auth@docker"
      - "traefik.http.services.dnsui.loadbalancer.server.port=80"
    environment:
      TZ: Etc/UTC
      DNSUI_WEB_BASEURL: "https://dns-admin.example.com"
      ADMIN_USER: admin
      POSTGRES_HOST: dnsui-db
      POSTGRES_PORT: 5432
      POSTGRES_DB: dnsui
      POSTGRES_USER: dnsui
      POSTGRES_PASSWORD: CHANGEME
      PDNS_API_HOST: pdns-auth
      PDNS_API_PORT: 8000
      PDNS_API_KEY: CHANGEME
  dnsui-db:
    container_name: dnsui-db
    image: postgres:14
    restart: always
    environment:
      TZ: Europe/Stockholm
      POSTGRES_USER: dnsui
      POSTGRES_PASSWORD: CHANGEME
      POSTGRES_DB: dnsui
    volumes:
      - dnsui-db:/var/lib/postgresql/data
volumes:
  dnsui-db
```

### docker-compose with internal PowerDNS Authorative

Note: This does not include a proxy to handle ´Basic Auth´

```yaml
version: '3'
services:
  pdns-auth:
    container_name: pdns-auth
    image: emiljacero/powerdns-auth-docker:4.5
    restart: always
    ports:
      - "53:53/tcp"
      - "53:53/udp"
      # - "8000:8000/tcp"
    environment:
      TZ: Etc/UTC
      ENV_PRIMARY: "yes"
      ENV_SECONDARY: "no"
      ENV_LAUNCH: gpgsql
      ENV_GPGSQL_HOST: pdns-db
      ENV_GPGSQL_PORT: 5432
      ENV_GPGSQL_DBNAME: pdns
      ENV_GPGSQL_USER: pdns
      ENV_GPGSQL_PASSWORD: CHANGEMEPSQL
      ENV_GPGSQL_DNSSEC: "yes"
      ENV_DEFAULT_SOA_EDIT: INCEPTION-INCREMENT
      ENV_LOCAL_ADDRESS: 0.0.0.0
      ENV_LOCAL_PORT: 53
      ENV_WEBSERVER: "yes"
      ENV_WEBSERVER_ADDRESS: 0.0.0.0
      ENV_WEBSERVER_ALLOW_FROM: 0.0.0.0/0
      ENV_WEBSERVER_PORT: 8000
      ENV_WEBSERVER_PASSWORD: CHANGEMEWEBSERVER
      ENV_API: "yes"
      ENV_API_KEY: CHANGEMEAPI
  pdns-db:
    container_name: pdns-db
    image: postgres:14
    restart: always
    environment:
      TZ: Etc/UTC
      POSTGRES_USER: pdns
      POSTGRES_PASSWORD: CHANGEMEPSQL
      POSTGRES_DB: pdns
    volumes:
      - pdns-db:/var/lib/postgresql/data
  dnsui:
    image: emiljacero/opera-dnsui:v0.2.7
    container_name: dnsui
    networks:
      - proxy
    ports:
      - 8080:80/tcp
    environment:
      TZ: Etc/UTC
      DNSUI_WEB_BASEURL: "https://dns-admin.example.com"
      ADMIN_USER: admin
      POSTGRES_HOST: dnsui-db
      POSTGRES_PORT: 5432
      POSTGRES_DB: dnsui
      POSTGRES_USER: dnsui
      POSTGRES_PASSWORD: CHANGEME
      PDNS_API_HOST: pdns-auth
      PDNS_API_PORT: 8000
      PDNS_API_KEY: CHANGEME
      DNSUI_WEB_FOOTER: "'My DNS'"
  dnsui-db:
    container_name: dnsui-db
    image: postgres:14
    restart: always
    environment:
      TZ: Europe/Stockholm
      POSTGRES_USER: dnsui
      POSTGRES_PASSWORD: CHANGEME
      POSTGRES_DB: dnsui
    volumes:
      - dnsui-db:/var/lib/postgresql/data
volumes:
  dnsui-db
  pdns-db
```

## Environment variables

Source configuration [@operasoftware](https://github.com/operasoftware/dns-ui/blob/v0.2.7/config/config-sample.ini)

|Variable Name|Default|Description|
|-|-|-|
|`ADMIN_USER`|`admin`|Initial admin username for DNS UI|
|`POSTGRES_HOST`|`postgres`|Postgresql database host|
|`POSTGRES_PORT`|`5432`|Postgresql database port|
|`POSTGRES_DB`|`dnsui`|Database name|
|`POSTGRES_USER`|`dnsui`|Database user/role|
|`POSTGRES_PASSWORD`|`dnsui`|Database password|
|`DNSUI_API_PROTOCOL`|`http`|`http` or `https`|
|`DNSUI_API_HOST`|`127.0.0.1`|PowerDNS API host|
|`DNSUI_API_PORT`|`8000`|PowerDNS API Port|
|`DNSUI_API_APIKEY`|`CHANGEME`|PowerDNS API key|
|`DNSUI_WEB_BASEURL`|`http://example.com`|The URL used by rewrites|
|`DNSUI_WEB_LOGO`|`'/logo-header-opera.png'`|Your own logo. Must include `'` around the string|
|`DNSUI_WEB_HEADER`|`'DNS Management'`|The header. Must include `'` around the string|
|`DNSUI_WEB_FOOTER`|`'Developed by <a href=\"https://www.opera.com/\">Opera Software</a>.'`|The footer. Must include `'` around the string|
|`DNSUI_FORCE_CHANGE_REVIEW`|`0`|Force all dns changes to be reviewed by someone other|
|`DNSUI_FORCE_CHANGE_COMMENT`|`0`|Force all dns changes to include a comment|
|`DNSUI_EMAIL_ENABLED`|`0`|Enable the sending of email|
|`DNSUI_EMAIL_FROM_ADDRESS`|`dnsui@example.com`|Email from address|
|`DNSUI_EMAIL_FROM_NAME`|`DNS Management System`|Email from name|
|`DNSUI_EMAIL_REPORT_ADDRESS`|`dnsui-report@example.com`|Email report address|
|`DNSUI_EMAIL_REPORT_NAME`|`DNS Administrator`|Email report name|
|`DNSUI_AUTH_USER_CASE_SENSITIVE`|`1`|Should username used for logging in be case sensitive?|
|`DNSUI_LDAP_ENABLED`|`0`|Enable the LDAP connection|
|`DNSUI_LDAP_HOST`|`N/A`||
|`DNSUI_LDAP_STARTTLS`|`N/A`||
|`DNSUI_LDAP_DN_USER`|`N/A`||
|`DNSUI_LDAP_DN_GROUP`|`N/A`||
|`DNSUI_LDAP_BIND_DN`|`N/A`||
|`DNSUI_LDAP_BIND_PASSWORD`|`N/A`||
|`DNSUI_LDAP_USER_ID`|`uid`||
|`DNSUI_LDAP_USER_NAME`|`cn`||
|`DNSUI_LDAP_USER_EMAIL`|`mail`||
|`DNSUI_LDAP_GROUP_MEMBER`|`member`||
|`DNSUI_LDAP_GROUP_MEMBER_VALUE`|`dn`||
|`DNSUI_LDAP_ADMIN_GRUOP_CN`|`N/A`||
|`DNSUI_SOA_EDIT_API`|`DEFAULT`||
|`DNSUI_DNS_DNSSEC`|`1`||
|`DNSUI_DNS_DNS_EDIT`|`1`||
|`DNSUI_AUTOCREATE_PTR`|`0`||
|`DNSUI_LOCAL_ZONE_SUFFIXES`|`localdomain`||
|`DNSUI_GIT_TRACKED_ENABLED`|`0`||
|`SSMTP_MAILHUB`|`smtp.example.com:25`||
|`SSMTP_HOSTNAME`|`example.com`||
|`SSMTP_USE_TLS`|`Yes`||
|`SSMTP_USE_STARTTLS`|`Yes`||
|`SSMTP_FROMLINEOVERRIDE`|`Yes`||
|`SSMTP_AUTH_ENABLED`|`0`||
|`SSMTP_AUTH_METHOD`|``||
|`SSMTP_AUTH_USER`|``||
|`SSMTP_AUTH_PASSWORD`|``||

## Parts and inspiration taken from :)

This docker container is inspired by [mjbnz](https://github.com/mjbnz/opera-dns-ui)
