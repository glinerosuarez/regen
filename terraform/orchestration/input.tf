variable "airflow_image_name" {
  type        = string
  default     = "apache/airflow:2.5.0"
  description = "Docker image name used to run Airflow."
}

variable "_pip_additional_requirements" {
  type        = string
  default     = ""
  description = "pip additional requirements."
}

variable "airflow_uid" {
  type        = string
  default     = "50000:0"
  description = "User used for run the first process."
}

variable "_airflow_www_user_username" {
  type    = string
  default = "airflow"
}

variable "_airflow_www_user_password" {
  type    = string
  default = "airflow"
}