variable "aws_region" {
  description = "AWS region used by the staging environment."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used to name resources."
  type        = string
  default     = "mvp-oficina"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "staging"
}

variable "ecr_repository_name" {
  description = "ECR repository name for the API image."
  type        = string
  default     = "mvp-oficina-api"
}

variable "db_name" {
  description = "Staging database name."
  type        = string
  default     = "oficina_staging"
}

variable "db_username" {
  description = "Staging database username."
  type        = string
  default     = "oficina_user"
}

variable "db_password" {
  description = "Staging database password."
  type        = string
  sensitive   = true
}