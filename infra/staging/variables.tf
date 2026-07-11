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

variable "eks_version" {
  description = "EKS Kubernetes version."
  type        = string
  default     = "1.30"
}

variable "eks_node_instance_types" {
  description = "EC2 instance types used by the EKS managed node group."
  type        = list(string)
  default     = ["t3.small"]
}

variable "eks_node_desired_size" {
  description = "Desired number of EKS worker nodes."
  type        = number
  default     = 1
}

variable "eks_node_min_size" {
  description = "Minimum number of EKS worker nodes."
  type        = number
  default     = 1
}

variable "eks_node_max_size" {
  description = "Maximum number of EKS worker nodes."
  type        = number
  default     = 2
}

variable "eks_supported_availability_zones" {
  description = "Availability zones supported by EKS control plane in us-east-1."
  type        = list(string)
  default = [
    "us-east-1a",
    "us-east-1b",
    "us-east-1c",
    "us-east-1d",
    "us-east-1f"
  ]
}