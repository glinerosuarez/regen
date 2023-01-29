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

module "dbt" {
  source       = "./dbt"
  network_name = docker_network.regen_network.name
  db_host      = module.db.db_host
  db_name      = module.db.db_name
  db_password  = module.db.db_password
  db_port      = module.db.db_port
  db_user      = module.db.db_user
}

module "agent" {
  source       = "./agent"
  network_name = docker_network.regen_network.name
  db_host      = module.db.db_host
  db_password  = module.db.db_password
  db_user      = module.db.db_user
}



