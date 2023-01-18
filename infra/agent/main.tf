terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

locals {
  app_name = "agent"
  workdir  = abspath("${path.root}/../.")
}

resource "docker_image" "agent" {
  name = "agent"
  build {
    context    = local.workdir
    tag        = ["agent:dev"]
    dockerfile = "Dockerfile"
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