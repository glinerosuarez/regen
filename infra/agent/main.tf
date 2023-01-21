terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

locals {
  app_name = "agent"
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
    dockerfile_sha1 = filesha1("${path.module}/Dockerfile")
    src_sha1 = sha1(join("", [for f in fileset(local.context_path, "src/**") : filesha1("${local.context_path}/${f}")]))
  }
  keep_locally = false
}

resource "docker_volume" "agent" {
  name = "agent"
}

resource "docker_container" "agent" {
  image = docker_image.agent.image_id
  name  = "agent"
  env   = ["PYTHONPATH=/app"]
  tty   = true
  networks_advanced {
    name = var.network_name
  }
  volumes {
    volume_name    = docker_volume.agent.name
    host_path      = abspath("${path.module}/output")
    container_path = "/app/output"
  }
}