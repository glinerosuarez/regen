variable "airflow_image_name" {
  type        = string
  default     = "apache/airflow:2.5.0"
  description = "Docker image name used to run Airflow."
}