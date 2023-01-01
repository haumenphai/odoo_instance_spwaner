ODOO DOTD
=========
TODO:
Cải tiến cho phép chạy 1 lệnh duy nhất (chạy file) để build 1 instance,
Cho phép cấu hình custom addons path trong file install_config, tự động cài requirement cho
custom addons_path, sau đó sẽ build 1 Dockerfile mới từ các config và build image mới, chạy từ image đó

Hoàn thiện doc cài đặt

Doc:
Đây là script install odoo với docker-compose, có thể chạy nhiều instance odoo trên 1 server với các config khác nhau.
+ Mỗi instance sẽ cần copy script cài đặt và chỉnh sửa install_config.conf riêng để phù hợp với từng instance.
+ Các instance sẽ dùng chung odoo_source_code trên server, với custom addons thì dùng riêng source code.

Luồng hoạt động:
+ Người dùng sẽ clone repo và đặt chúng ở một thư mục riêng trên server: ví dụ: /opt/odoo/instance_name/dotd_odoo_docker
+ Sau khi đã clone thì chỉnh sửa config trong file: instance_config.conf, file đó bao gồm các thông tin:
    + các custom addons path
    + port, instance_name, odoo_config: [port, ...]
+ Sau khi đã chỉnh sửa xong config thì chạy file install.sh, nó sẽ build ra 1 file Dockerfile phù hợp với config và tạo
image từ Dockerfile custom đó, sau đó có thể cài đặt start instance bằng lệnh: docker compose up 



HOW TO USE FROM SCRATCH?
-----------


**Clone and CD to source folder**: ```cd dotd_odoo_docker/odoo15```

**Build Image**: ```sudo docker build -t haumenphai/dotd_odoo:15 .```

**RUN application**: ``` docker compose --env-file docker_compose_env up ```
