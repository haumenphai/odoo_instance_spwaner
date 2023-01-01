import json
import os
import shutil

install_config = False
container_custom_addons_path = []
build_custom_addons_path = []


def get_install_config():
    with open('install_config.json', 'r') as f:
        txt_json = f.read()
        return json.loads(txt_json)


def build_custom_dockerfile():
    os.system('rm -rf build/custom_addons')

    script_install_custom_addons = ""
    for custom_addon_path in install_config['custom_addons_path']:
        addon_name = custom_addon_path.split('/')[-1]
        container_addon_path = f"/opt/odoo/{install_config['instance_name']}/custom_addons/{addon_name}"
        container_custom_addons_path.append(container_addon_path)

        build_custom_addon_path = f'build/custom_addons/{addon_name}'
        docker_context_addon_path = f'custom_addons/{addon_name}'
        shutil.copytree(custom_addon_path, build_custom_addon_path)
        build_custom_addons_path.append(build_custom_addon_path)

        script_install_custom_addons +=  \
            f"RUN mkdir -m 770 -p {container_addon_path}\n" \
            f"COPY {docker_context_addon_path} {container_addon_path}\n"

        requirement_path = os.path.join(docker_context_addon_path, 'requirements.txt')
        if os.path.exists(requirement_path):
            script_install_custom_addons += f"RUN $python_venv_path -m pip install -r {requirement_path}\n"

    with open('templates/Dockerfile.template', 'r') as f:
        dockerfile_txt = f.read().replace('{instance_name}', install_config['instance_name']) \
                                 .replace('{script_install_custom_addons}', script_install_custom_addons)
        with open('build/Dockerfile', 'w') as f2:
            f2.write(dockerfile_txt)


def build_custom_odoo_config():
    with open('templates/odoo.conf.template', 'r') as f:
        _odoo_config_txt = ""
        for k, v in install_config['container_odoo_config'].items():
            _odoo_config_txt += f"{k} = {v}\n"

        odoo_config = f.read().replace('{addons_path}', ','.join(container_custom_addons_path) + ',/opt/odoo/odoo15/addons') \
                              .replace('{odoo_config}', _odoo_config_txt)

        with open('containers_data/odoo.conf', 'w') as f2:
            f2.write(odoo_config)


def build_custom_docker_image():
    os.system(f'cd build && docker build -t odoo_{install_config["instance_name"]} .')


def build_custom_docker_compose_file():
    with open('templates/docker-compose.yaml.template', 'r') as f:
        docker_compose_file = f.read().format(
            instance_name=install_config['instance_name'],
            docker_image='odoo_' + install_config['instance_name'],
            http_port_mapping=install_config['http_port_mapping'],
            long_polling_port_mapping=install_config['long_polling_port_mapping'],
            odoo_source_path=install_config['odoo_source_path'],
        )
        with open('build/docker-compose.yaml', 'w') as f2:
            f2.write(docker_compose_file)


def clear_temp_files():
    os.system('rm -rf build/custom_addons')


if __name__ == '__main__':
    install_config = get_install_config()
    build_custom_dockerfile()
    build_custom_odoo_config()
    build_custom_docker_image()
    build_custom_docker_compose_file()
    clear_temp_files()
