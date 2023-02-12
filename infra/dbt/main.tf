terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

locals {
  mod_path = abspath("${path.root}/dbt")
}

resource "docker_image" "dbt" {
  name         = "dbt"
  keep_locally = false
  build {
    context    = abspath("${path.root}/../.")
    dockerfile = "/infra/dbt/Dockerfile"
  }
  triggers = {
    docker_file_sha1 = filesha1("${local.mod_path}/Dockerfile")
    profiles_conf    = filesha1("${local.mod_path}/profiles.yml")
    server           = filesha1("${local.mod_path}/server.py")
  }
}

resource "docker_container" "dbt" {
  image   = docker_image.dbt.image_id
  name    = "dbt"
  env     = ["DB_HOST=${var.db_host}", "DB_USER=${var.db_user}", "DB_PASSWORD=${var.db_password}", "DB_PORT=${var.db_port}", "DB_NAME=${var.db_name}"]
  command = ["python", "/app/server/server.py"]
  volumes {
    host_path      = abspath("${path.root}/../etl/transform")
    container_path = "/app/regen"
  }
  networks_advanced {
    name = var.network_name
  }
}