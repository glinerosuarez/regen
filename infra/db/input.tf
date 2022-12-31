variable "network_name" {
  type        = string
  description = "Network in which to register containers."
}

variable "username" {
  type        = string
  default = "regen"
  description = "Admin username for the db."
}

variable "password" {
  type        = string
  default = "regen"
  description = "Admin user password."
}

variable "db_name" {
  type        = string
  default = "regen"
  description = "Name of the database."
}