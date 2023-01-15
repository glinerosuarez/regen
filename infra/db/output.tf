output "db_host" {
  value = docker_container.regen_db.name
}

output "db_name" {
  value = var.db_name
}

output "db_password" {
  value = var.password
}

output "db_port" {
  value = "5432"
}

output "db_user" {
  value = var.username
}

