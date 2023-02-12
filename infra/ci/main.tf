terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

resource "docker_network" "regen_network" {
  name = "test_regen"
}

module "agent" {
  source       = "./../agent"
  network_name = docker_network.regen_network.name
  db_host      = ""
  db_password  = ""
  db_user      = ""
  create_container = false
}

resource "docker_container" "ci" {
  image = module.agent.image_id
  name  = "ci"
  volumes {
    host_path      = "${local.workdir}/test"
    container_path = "/app/test"
  }
  env = ["PYTHONPATH=/app"]
  tty = true
}