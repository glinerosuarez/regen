terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

provider "docker" {}

locals {

}

resource "docker_network" "airflow_network" {
  name = "airflow"
}

resource "docker_image" "postgres" {
  name         = "postgres:13"
  keep_locally = false
}

resource "docker_container" "postgres" {
  image = docker_image.postgres.latest
  name  = "postgres_container"
  env   = ["POSTGRES_USER=airflow", "POSTGRES_PASSWORD=airflow", "POSTGRES_DB=airflow"]
  volumes {
    volume_name    = "postgres-db-volume"
    container_path = "/var/lib/postgresql/data"
  }
  healthcheck {
    test     = ["CMD", "pg_isready", "-U", "airflow"]
    interval = "5s"
    retries  = 5
  }
  restart = "always"
  networks_advanced {
    name = docker_network.airflow_network.name
  }
}

resource "docker_image" "redis" {
  name         = "redis:latest"
  keep_locally = false
}

resource "docker_container" "redis" {
  image = docker_image.redis.latest
  name  = "redis_container"
  healthcheck {
    test     = ["CMD", "redis-cli", "ping"]
    interval = "5s"
    timeout  = "30s"
    retries  = 50
  }
  restart = "always"
  networks_advanced {
    name = docker_network.airflow_network.name
  }
}
