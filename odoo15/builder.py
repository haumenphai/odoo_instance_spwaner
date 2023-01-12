import json
import os
import shutil

ODOO_INSTALLATION_DIR = '/opt/odoo'
BUILD_DIR = 'build'
CONTAINER_DATA_DIR = 'containers_data'
ODOO_BIN_PATH = f'{ODOO_INSTALLATION_DIR}/odoo15/odoo-bin'
ODOO_REQUIREMENTS_PATH = f'{ODOO_INSTALLATION_DIR}/odoo15/requirements.txt'
PYTHON_VENV_PATH = '/opt/python3.8-venv/odoo15/bin/python3.8'

PSQL_DB_HOST = 'postgresql'  # includes psql service name
PSQL_DB_USER = 'odoo'
PSQL_DB_PASS = 'odoo-dotd-2022'


def _get_install_config():
    with open('install_config.json', 'r') as f:
        txt_json = f.read()
        return json.loads(txt_json)


install_config = _get_install_config()
container_custom_addons_path = []
installed_data = {}


def _pre_install():
    os.system(f'rm -rf {BUILD_DIR}')
    os.system(f'mkdir -p {BUILD_DIR} {CONTAINER_DATA_DIR}')
    os.system(f'echo "" > {CONTAINER_DATA_DIR}/odoo.log')


def _build_custom_dockerfile():
    os.system('rm -rf build/custom_addons build/requirements.txt')

    script_install_custom_addons = ""
    for custom_addon_path in install_config['custom_addons_path']:
        addon_name = custom_addon_path.split('/')[-1]
        container_addon_path = f"{ODOO_INSTALLATION_DIR}/custom_addons/{addon_name}"
        container_custom_addons_path.append(container_addon_path)

        build_custom_addon_path = f'build/custom_addons/{addon_name}'
        docker_context_addon_path = f'custom_addons/{addon_name}'
        shutil.copytree(custom_addon_path, build_custom_addon_path)

        script_install_custom_addons += \
            f"RUN mkdir -m 770 -p {container_addon_path}\n" \
            f"COPY {docker_context_addon_path} {container_addon_path}\n"

        requirement_path = os.path.join(docker_context_addon_path, 'requirements.txt')
        if os.path.exists(requirement_path):
            script_install_custom_addons += f"RUN $python_venv_path -m pip install -r {requirement_path}\n"

    shutil.copyfile(f'{install_config["odoo_source_path"]}/requirements.txt', f'{BUILD_DIR}/requirements.txt')
    with open('templates/Dockerfile.template', 'r') as f:
        dockerfile_txt = f.read().replace('{instance_name}', install_config['instance_name']) \
            .replace('{script_install_custom_addons}', script_install_custom_addons) \
            .replace('{odoo_installation_dir}', ODOO_INSTALLATION_DIR) \
            .replace('{python_venv_path}', PYTHON_VENV_PATH) \
            .replace('{host_odoo_requirements_path}', 'requirements.txt')
        with open('build/Dockerfile', 'w') as f2:
            f2.write(dockerfile_txt)


def _build_custom_odoo_config():
    with open('templates/odoo.conf.template', 'r') as f:
        _odoo_config_txt = ""
        for k, v in install_config['container_odoo_config'].items():
            _odoo_config_txt += f"{k} = {v}\n"

        odoo_config = f.read().format(
            addons_path=','.join(container_custom_addons_path) + f',{ODOO_INSTALLATION_DIR}/odoo15/addons',
            odoo_installation_dir=ODOO_INSTALLATION_DIR,
            odoo_config=_odoo_config_txt
        )

        with open('containers_data/odoo.conf', 'w') as f2:
            f2.write(odoo_config)


def _build_custom_docker_image():
    os.system(f'cd build && docker build -t odoo_{install_config["instance_name"]} .')


def _build_custom_docker_compose_file():
    with open('templates/docker-compose.yaml.template', 'r') as f:
        docker_compose_content = f.read().format(
            instance_name=install_config['instance_name'],
            docker_image='odoo_' + install_config['instance_name'],
            http_port_mapping=install_config['http_port_mapping'],
            long_polling_port_mapping=install_config['long_polling_port_mapping'],
            odoo_source_path=install_config['odoo_source_path'],
            odoo_installation_dir=ODOO_INSTALLATION_DIR,
            psql_db_user=PSQL_DB_USER,
            psql_db_password=PSQL_DB_PASS,
            psql_db_host=PSQL_DB_HOST
        )
        with open(f'{BUILD_DIR}/docker-compose.yaml', 'w') as f2:
            f2.write(docker_compose_content)


def _build_nginx_config_file():
    with open('templates/nginx_site.template', 'r') as f:
        upstream_name = install_config['instance_fqdn'].replace('.', '_')
        nginx_content = f.read().replace('{instance_upstream}', upstream_name) \
                                .replace('{instance_upstream_longpolling}', f"{upstream_name}_longpolling") \
                                .replace('{instance_fqdn}', install_config['instance_fqdn']) \
                                .replace('{http_port_mapping}', install_config['http_port_mapping'])

        if install_config['container_odoo_config']['workers'] == 0:
            nginx_content = nginx_content.replace('{long_polling_port_mapping}', install_config['http_port_mapping'])
        else:
            nginx_content = nginx_content.replace('{long_polling_port_mapping}', install_config['long_polling_port_mapping'])

        with open(f'{BUILD_DIR}/{install_config["instance_fqdn"]}.conf', 'w') as f2:
            f2.write(nginx_content)


def _clear_temp_files():
    # TODO use symbolic link
    os.system('rm -rf build/custom_addons')


def _write_installed_data():
    with open(f'{BUILD_DIR}/installed_data.json', 'w') as f:
        f.write(json.dumps({
            'odoo_container_name': 'odoo_' + install_config['instance_name'],
            'psql_container_name': 'psql_compose_' + install_config['instance_name'],
            'installed': True
        }))


def get_install_data():
    path = f'{BUILD_DIR}/installed_data.json'

    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.loads(f.read())
    return {}


def build_odoo():
    _pre_install()
    _build_custom_dockerfile()
    _build_custom_odoo_config()
    _build_custom_docker_image()
    _build_custom_docker_compose_file()
    _build_nginx_config_file()
    _write_installed_data()
    _clear_temp_files()
