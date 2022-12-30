terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

provider "docker" {}

locals {
  common_env = [
    "AIRFLOW__CORE__EXECUTOR=CeleryExecutor",
    "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow",
    # For backward compatibility, with Airflow <2.3
    "AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow",
    "AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:airflow@postgres/airflow",
    "AIRFLOW__CELERY__BROKER_URL=redis://:@redis:6379/0",
    "AIRFLOW__CORE__FERNET_KEY=\"\"",
    "AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=true",
    "AIRFLOW__CORE__LOAD_EXAMPLES=false",
    "AIRFLOW__API__AUTH_BACKENDS=airflow.api.auth.backend.basic_auth",
    "_PIP_ADDITIONAL_REQUIREMENTS=${var._pip_additional_requirements}"
  ]
  volumes = [
    {
      host_path      = abspath("./dags")
      container_path = "/opt/airflow/dags"
    },
    {
      host_path      = abspath("./logs")
      container_path = "/opt/airflow/logs"
    },
    {
      host_path      = abspath("./plugins")
      container_path = "/opt/airflow/plugins"
    }
  ]
}

resource "docker_network" "airflow_network" {
  name = "airflow"
}

resource "docker_image" "postgres" {
  name         = "postgres:13"
  keep_locally = false
}

resource "docker_image" "redis" {
  name         = "redis:latest"
  keep_locally = false
}

resource "docker_image" "airflow" {
  name         = var.airflow_image_name
  keep_locally = false
}

resource "docker_container" "postgres" {
  image = docker_image.postgres.image_id
  name  = "postgres"
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

  provisioner "local-exec" {
    command = "bash ./scripts/healthy_check.sh ${self.name}"
  }
}

resource "docker_container" "redis" {
  image = docker_image.redis.image_id
  name  = "redis"
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

  provisioner "local-exec" {
    command = "bash ./scripts/healthy_check.sh ${self.name}"
  }
}

resource "docker_container" "airflow-init" {
  image  = docker_image.airflow.image_id
  name   = "airflow-init"
  attach = true
  env = concat(
    local.common_env,
    [
      "_AIRFLOW_DB_UPGRADE=true",
      "_AIRFLOW_WWW_USER_CREATE=true",
      "_AIRFLOW_WWW_USER_USERNAME=${var._airflow_www_user_username}",
      "_AIRFLOW_WWW_USER_PASSWORD=${var._airflow_www_user_password}",
      "_PIP_ADDITIONAL_REQUIREMENTS="
    ]
  )
  volumes {
    host_path      = abspath(".")
    container_path = "/sources"
  }
  user       = "0:0"
  depends_on = [docker_container.redis, docker_container.postgres]
  entrypoint = ["/bin/bash"]
  command    = ["/sources/scripts/airflow_init.sh"]
  networks_advanced {
    name = docker_network.airflow_network.name
  }
  must_run = false
}

resource "docker_container" "airflow-webserver" {
  image = docker_image.airflow.image_id
  name  = "airflow-webserver"
  env   = local.common_env
  dynamic "volumes" {
    for_each = local.volumes
    iterator = v
    content {
      host_path      = v.value.host_path
      container_path = v.value.container_path
    }
  }
  user       = var.airflow_uid
  depends_on = [docker_container.postgres, docker_container.redis, docker_container.airflow-init]
  command    = ["webserver"]
  restart    = "always"
  ports {
    internal = 8080
    external = 8080
  }
  healthcheck {
    test     = ["CMD", "curl", "--fail", "http://localhost:8080/health"]
    interval = "10s"
    timeout  = "10s"
    retries  = 5
  }
  networks_advanced {
    name = docker_network.airflow_network.name
  }
}

resource "docker_container" "airflow-scheduler" {
  image      = docker_image.airflow.image_id
  name       = "airflow-scheduler"
  env        = local.common_env
  user       = var.airflow_uid
  depends_on = [docker_container.postgres, docker_container.redis, docker_container.airflow-init]
  command    = ["scheduler"]
  restart    = "always"
  healthcheck {
    test     = ["CMD-SHELL", "airflow jobs check --job-type SchedulerJob --hostname \"$${HOSTNAME}\""]
    interval = "10s"
    timeout  = "10s"
    retries  = 5
  }
  dynamic "volumes" {
    for_each = local.volumes
    iterator = v
    content {
      host_path      = v.value.host_path
      container_path = v.value.container_path
    }
  }
  networks_advanced {
    name = docker_network.airflow_network.name
  }
}

resource "docker_container" "airflow-worker" {
  image      = docker_image.airflow.image_id
  name       = "airflow-worker"
  user       = var.airflow_uid
  env        = concat(local.common_env, ["DUMB_INIT_SETSID=0"])
  depends_on = [docker_container.postgres, docker_container.redis, docker_container.airflow-init]
  command    = ["celery", "worker"]
  restart    = "always"
  healthcheck {
    test     = ["CMD-SHELL", "celery --app airflow.executors.celery_executor.app inspect ping -d \"celery@$${HOSTNAME}\""]
    interval = "10s"
    timeout  = "10s"
    retries  = 5
  }
  dynamic "volumes" {
    for_each = local.volumes
    iterator = v
    content {
      host_path      = v.value.host_path
      container_path = v.value.container_path
    }
  }
  networks_advanced {
    name = docker_network.airflow_network.name
  }
}

resource "docker_container" "airflow-triggerer" {
  image      = docker_image.airflow.image_id
  name       = "airflow-triggerer"
  env        = local.common_env
  user       = var.airflow_uid
  depends_on = [docker_container.postgres, docker_container.redis, docker_container.airflow-init]
  command    = ["triggerer"]
  restart    = "always"
  healthcheck {
    test     = ["CMD-SHELL", "airflow jobs check --job-type TriggererJob --hostname \"$${HOSTNAME}\""]
    interval = "10s"
    timeout  = "10s"
    retries  = 5
  }
  dynamic "volumes" {
    for_each = local.volumes
    iterator = v
    content {
      host_path      = v.value.host_path
      container_path = v.value.container_path
    }
  }
  networks_advanced {
    name = docker_network.airflow_network.name
  }
}

resource "docker_container" "airflow-cli" {
  count      = var.debug_mode ? 1 : 0
  image      = docker_image.airflow.image_id
  name       = var.airflow_uid
  user       = var.airflow_uid
  env        = concat(local.common_env, ["CONNECTION_CHECK_MAX_COUNT=0"])
  depends_on = [docker_container.postgres, docker_container.redis]
  command    = ["bash", "-c", "airflow"]
  dynamic "volumes" {
    for_each = local.volumes
    iterator = v
    content {
      host_path      = v.value.host_path
      container_path = v.value.container_path
    }
  }
}
