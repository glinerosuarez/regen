terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

provider "docker" {}

resource "docker_network" "regen_network" {
  name = "regen"
}

module "orchestration" {
  source       = "./orchestration"
  network_name = docker_network.regen_network.name
}

module "db" {
  source       = "./db"
  network_name = docker_network.regen_network.name
}



