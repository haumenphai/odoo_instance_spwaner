#! /usr/bin/python3

import argparse
import os
import builder


installed_data = builder.get_install_data()
odoo_container_name = installed_data.get('odoo_container_name')
psql_container_name = installed_data.get('psql_container_name')


def docker_compose_up():
    os.system(f'docker compose --file build/docker-compose.yaml up -d')


def docker_compose_down():
    os.system(f'docker compose --file build/docker-compose.yaml down')


def start_odoo():
    os.system(f'docker start {odoo_container_name}')


def stop_odoo():
    os.system(f'docker stop {odoo_container_name}')


def restart_odoo():
    os.system(f'docker restart {odoo_container_name}')


def start_psql():
    os.system(f'docker start {psql_container_name}')


def stop_psql():
    os.system(f'docker stop {psql_container_name}')


def restart_postgresql():
    os.system(f'docker restart {psql_container_name}')


def disable_auto_start():
    os.system(f'docker update --restart=no {psql_container_name} {odoo_container_name}')


def enable_auto_start():
    os.system(f'docker update --restart=always {psql_container_name} {odoo_container_name}')


def upgrade_modules(modules, db_name):
    odoo_log_path = f'{builder.CONTAINER_DATA_DIR}/odoo.conf'
    with open(odoo_log_path, 'r') as f:
        old_config = f.read()
    with open(odoo_log_path, 'w') as f:
        new_text = ""
        for line in old_config.split('\n'):
            if 'logfile' not in line:
                new_text += line + '\n'
        f.write(new_text)

    cmd = f'docker exec {odoo_container_name} {builder.PYTHON_VENV_PATH} ' \
          f'{builder.ODOO_BIN_PATH} -c /opt/odoo/odoo.conf ' \
          f'--db_host={builder.PSQL_DB_HOST} --db_user={builder.PSQL_DB_USER} --db_password={builder.PSQL_DB_PASS} ' \
          f'--http-port 12234 -d {db_name} -u {",".join(modules)} --stop-after-init '
    os.system(cmd)

    with open(odoo_log_path, 'w') as f:
        f.write(old_config)


def deploy_nginx_site():
    def _set_nginx_hosts():
        with open('/etc/hosts', 'r') as f1:
            new_text = "127.0.0.1       nginx\n"
            old_text = f1.read()
            if new_text in old_text:
                return

            new_text += old_text
            with open('/etc/hosts', 'w') as f2:
                f2.write(new_text)
    _set_nginx_hosts()

    nginx_config_file_name = f'{builder.install_config["instance_fqdn"]}.conf'
    os.system(f'sudo cp build/{nginx_config_file_name}  /etc/nginx/sites-available/')
    os.system(f'sudo ln -sf /etc/nginx/sites-available/{nginx_config_file_name} /etc/nginx/sites-enabled/{nginx_config_file_name}')
    os.system('sudo service nginx restart')


def clear_odoo_log():
    os.system(f'echo "" > {builder.CONTAINER_DATA_DIR}/odoo.log')


def parse_args():
    parser = argparse.ArgumentParser(
        prog="Install Odoo use docker compose.",
        description="Install and interact with Odoo.",
        epilog="Text at the bottom of help"
    )

    parser.add_argument('-b', '--build', action='store_true')

    parser.add_argument('--start_odoo', action='store_true', help='Start Odoo')
    parser.add_argument('--stop_odoo', help='Stop Odoo', action='store_true')
    parser.add_argument("-ro", "--restart_odoo", help="Restart Odoo", action='store_true')

    parser.add_argument('--start_psql', help='Start Psql', action='store_true')
    parser.add_argument('--stop_psql', help='Stop Psql', action='store_true')
    parser.add_argument("-rp", "--restart_psql", help="Restart Postgresql", action='store_true')

    parser.add_argument("-cu", "--compose_up", help="Execute compose up", action='store_true')
    parser.add_argument("-cd", "--compose_down", help="Execute compose down", action='store_true')
    parser.add_argument('-da', '--disable_instance', help='Disable Instance', action='store_true')
    parser.add_argument('-ea', '--enable_instance', help='Enable Instance', action='store_true')

    parser.add_argument("-u", "--upgrade_module", help="Upgrade modules, db:module1,module2 ex: -u dbname1:web,mail", default=[])
    parser.add_argument("-cll", "--clear_odoo_log", help="Clean Odoo Log", action='store_true')
    parser.add_argument("-dn", "--deploy_nginx_site", action='store_true')

    parsed_args = parser.parse_args()
    return parsed_args


if __name__ == '__main__':
    args = parse_args()

    if args.build:
        builder.build_odoo()
    elif args.start_odoo:
        start_odoo()
    elif args.stop_odoo:
        stop_odoo()
    elif args.restart_odoo:
        restart_odoo()
    elif args.start_psql:
        start_psql()
    elif args.stop_psql:
        stop_psql()
    elif args.restart_psql:
        restart_postgresql()
    elif args.compose_up:
        docker_compose_up()
    elif args.compose_down:
        docker_compose_down()
    elif args.disable_instance:
        disable_auto_start()
    elif args.enable_instance:
        enable_auto_start()
    elif args.upgrade_module:
        db_name = args.upgrade_module.split(':')[0]
        modules = args.upgrade_module.split(':')[1].split(',')
        upgrade_modules(modules, db_name)
    elif args.clear_odoo_log:
        clear_odoo_log()
    elif args.deploy_nginx_site:
        deploy_nginx_site()
