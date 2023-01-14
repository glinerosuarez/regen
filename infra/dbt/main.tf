terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

resource "docker_image" "dbt" {
  name = "dbt"
  keep_locally = false
  build {
    path = abspath("${path.root}/../.")
    dockerfile = "/infra/dbt/Dockerfile"
  }
}

resource "docker_container" "dbt" {
  image = docker_image.dbt.image_id
  name = "dbt"
  entrypoint = ["/bin/bash"]
  networks_advanced {
    name = var.network_name
  }
}