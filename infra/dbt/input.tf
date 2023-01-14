variable "network_name" {
  type        = string
  description = "Network in which to register containers."
}

variable "db_host" {
  type        = string
  description = "Database host to connect to."
}

variable "db_user" {
  type        = string
  description = "Database user."
}

variable "db_password" {
  type        = string
  description = "Database password."
}

variable "db_port" {
  type        = string
  description = "Database port."
}

variable "db_name" {
  type        = string
  description = "Database name."
}