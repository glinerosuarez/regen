terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

provider "docker" {}

resource "docker_image" "regen" {
  name = local.app_name
  build {
    path = local.workdir
    tag  = ["regen:dev"]
  }
  keep_locally = false
}

resource "docker_container" "regen" {
  image = docker_image.regen.latest
  name  = "regen_container"
  volumes {
    host_path      = "${local.workdir}/test"
    container_path = "/app/test"
  }
  env = ["PYTHONPATH=/app"]
  tty = true
}