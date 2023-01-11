terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

resource "docker_volume" "regen_db_volume" {
  name = "regen-db-volume"
}

resource "docker_image" "db" {
  name         = "postgres:14"
  keep_locally = false
}

resource "docker_container" "regen_db" {
  image = docker_image.db.image_id
  name  = "regen_db"
  env   = ["POSTGRES_USER=${var.username}", "POSTGRES_PASSWORD=${var.password}", "POSTGRES_DB=${var.db_name}"]
  volumes {
    volume_name    = docker_volume.regen_db_volume.name
    host_path      = abspath("${path.root}/db/data")
    container_path = "/var/lib/postgresql/data"
  }
  healthcheck {
    test     = ["CMD", "pg_isready", "-U", var.username]
    interval = "5s"
    retries  = 5
  }
  restart = "always"
  networks_advanced {
    name = var.network_name
  }

  provisioner "local-exec" {
    command = "bash ${path.root}/scripts/healthy_check.sh ${self.name}"
  }
}