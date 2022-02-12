# opera-dns-ui

This docker container is inspired by [mjbnz](https://github.com/mjbnz/opera-dns-ui)

## Summary

A self contained docker image with php-fpm & caddy for [Opera's PowerDNS Admin UI](https://github.com/operasoftware/dns-ui)

This image is intended to be used behind some form of reverse proxy responsible for Authentication. The proxy should set an `X-Auth-User` header with the authenticated username for the application. (the application's support for PHP authentication has been enabled, LDAP disabled).

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
      - "traefik.docker.network=ns1_proxy"
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
```

## Environment variables

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

### Example docker invocation

    docker run -d                                      \
           -e MAIL_SERVER=smtp.example.com             \
           -e POSTGRES_HOST=dbhost.example.com         \
           -e POSTGRES_PASSWORD=a-very-secret-password \
           -e PDNS_API_HOST=dns.example.com            \
           -e PDNS_API_KEY=a-very-secret-key           \
           -v /srv/dnsui:/data                         \
           --restart=unless-stopped                    \
       mjbnz/opera-dns-ui:latest

##### Parts and inspiration taken from

* <https://github.com/maxguru/operadns-ui-docker>
* <https://github.com/LolHens/docker-dns-ui>
* <https://bitpress.io/caddy-with-docker-and-php/>
* <https://github.com/stevepacker/docker-containers/tree/caddy-php7>
