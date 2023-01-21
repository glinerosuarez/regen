terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

locals {
  app_name = "agent"
}

resource "docker_image" "agent" {
  name = "agent"
  build {
    context    = "${path.module}/../../."
    dockerfile = "/infra/agent/Dockerfile"
  }
  triggers = {
    requirements_sha1 = filesha1("${path.module}/requirements.txt")
    dockerfile_sha1 = filesha1("${path.module}/Dockerfile")
  }
  keep_locally = false
}

resource "docker_container" "agent" {
  image = docker_image.agent.image_id
  name  = "agent"
  env   = ["PYTHONPATH=/app"]
  tty   = true
  networks_advanced {
    name = var.network_name
  }
}