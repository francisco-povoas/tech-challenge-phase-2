variable "aws_region" {
  description = "AWS region."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used to tag bootstrap resources."
  type        = string
  default     = "mvp-oficina"
}

variable "state_bucket_name" {
  description = "S3 bucket name used to store Terraform state."
  type        = string
}