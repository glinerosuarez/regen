terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

locals {
  app_name     = "agent"
  context_path = "${path.module}/../../."
}

resource "docker_image" "agent" {
  name = "agent"
  build {
    context    = local.context_path
    dockerfile = "/infra/agent/Dockerfile"
  }
  triggers = {
    requirements_sha1 = filesha1("${path.module}/requirements.txt")
    dockerfile_sha1   = filesha1("${path.module}/Dockerfile")
    src_sha1          = sha1(join("", [for f in fileset(local.context_path, "src/**") : filesha1("${local.context_path}/${f}")]))
  }
  keep_locally = false
}

resource "docker_container" "agent" {
  count = var.create_container ? 1 : 0
  image = docker_image.agent.image_id
  name  = "agent"
  env   = ["PYTHONPATH=/app", "REGEN_DB_HOST=${var.db_host}", "REGEN_DB_USER=${var.db_user}", "REGEN_DB_PASSWORD=${var.db_password}"]
  tty   = true
  networks_advanced {
    name = var.network_name
  }
  volumes {
    host_path      = abspath("${path.module}/output")
    container_path = "/app/output"
  }
}