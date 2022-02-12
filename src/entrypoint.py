#!/usr/bin/env python3

from email.policy import default
from multiprocessing.connection import wait
import os
import sys
import subprocess
import requests
import json
import time

from lib.logger import logger as log
from lib.template import Template
from lib.gpgsql import wait_for_db, has_existing_default_user, execute_sql

# Set working directory
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# PATHS
base_dir = os.path.dirname(os.path.realpath(__file__))
template_path = os.path.join(base_dir, 'templates')
config_ini_path = "/srv/dns-ui/config/config.ini"
ssmtp_path = "/etc/ssmtp/ssmtp.conf"
insert_user_sql_path = "/app/insert_user.sql"

if os.getenv('DEV') == "true":
    template_path = os.path.join(base_dir, 'templates')
    config_ini_path = f"{base_dir}/dev/config.ini"
    ssmtp_path = f"{base_dir}/dev/ssmtp.conf"
    insert_user_sql_path = f"{base_dir}/dev/insert_user.sql"


log.debug(f"base_dir: {base_dir}")
log.debug(f"template_path: {template_path}")
log.debug(f"config_ini_path: {config_ini_path}")
log.debug(f"ssmtp_path: {ssmtp_path}")

# Init
renderer = Template()


def get_from_environment(env_search_terms=["ENV_"]):
    enviroment = {}
    log.info("Getting environment variables")
    for search_term in env_search_terms:
        for k, v in os.environ.items():
            if f"{search_term}" in k:
                obj = {k: v}
                enviroment.update(obj)
    log.debug(json.dumps(enviroment, indent=2))
    return enviroment


def web_connect_check(url, headers):
    response = None
    try:
        response = requests.get(url, headers=headers).status_code
    except requests.exceptions.ConnectionError as error:
        log.error(f"Got connection error. Check the url ({url})")
        log.debug(error)
    except Exception as error:
        log.error(error)
    return response


def wait_for_api(url, headers, timeout=30):
    time_end = time.time() + timeout
    while web_connect_check(url, headers) is False:
        if time.time() > time_end:
            log.error('Could not connect to the PowerDNS API')
            sys.exit(1)
        log.info(
            f"Waiting for PowerDNS API at: url"
        )
        time.sleep(5)
    log.info(f"Successfully connected to PowerDNS API ({url})")


def main():
    # Write templates
    render_list = [{"template": "config.ini.j2",
                    "output_file": config_ini_path,
                   "search_term": ["DNSUI_", "POSTGRES_"]},
                   {"template": "ssmtp.conf.j2",
                   "output_file": ssmtp_path,
                    "search_term": ["SSMTP_"]},
                   {"template": "instert_user.sql.j2",
                   "output_file": insert_user_sql_path,
                    "search_term": ["ADMIN_"]}]
    for templ in render_list:
        log.debug(templ)
        template = os.path.join(template_path, templ.get('template'))
        renderer.render_template(template=template,
                                 output_file=templ.get('output_file'),
                                 data=get_from_environment(templ.get('search_term')))

    # Add default user if the database is fresh
    psql_host = os.getenv('POSTGRES_HOST', default="127.0.0.1")
    psql_port = os.getenv('POSTGRES_PORT', default="5432")
    psql_db = os.getenv('POSTGRES_DB', default="dnsui")
    psql_user = os.getenv('POSTGRES_USER', default="dnsui")
    psql_password = os.getenv('POSTGRES_PASSWORD', default="CHANGEME")
    default_user = os.getenv('ADMIN_USER', default="admin")

    wait_for_db(psql_host, psql_port, psql_user, psql_password)
    if not has_existing_default_user(psql_host, psql_port, psql_user, psql_password, psql_db, default_user):
        log.info("Insert default User ({})")
        execute_sql(psql_host, psql_port, psql_user,
                    psql_password, psql_db, insert_user_sql_path)

    # Only continue if connection to API succeeds
    api_protocol = os.getenv('DNSUI_API_PROTOCOL', default="http")
    api_host = os.getenv('DNSUI_API_HOST', default="127.0.0.1")
    api_port = os.getenv('DNSUI_API_PORT', default="8000")
    api_key = os.getenv('DNSUI_API_APIKEY', default="CHANGEME")
    api_url = f"{api_protocol}://{api_host}:{api_port}/api/v1/servers"
    api_headers = {"X-API-KEY": api_key}

    wait_for_api(api_url, api_headers)

    log.info("Starting Caddy")
    process = subprocess.Popen([
        "/bin/sh", "-c", "/usr/bin/caddy",
        "--conf", "/etc/Caddyfile", "--log", "stdout"
    ],
        shell=False)
    process.wait()
    log.info("Caddy stopped")


if __name__ == "__main__":
    main()
