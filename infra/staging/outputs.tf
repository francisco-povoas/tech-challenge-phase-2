output "ecr_repository_name" {
  description = "ECR repository name."
  value       = aws_ecr_repository.api.name
}

output "ecr_repository_url" {
  description = "ECR repository URL."
  value       = aws_ecr_repository.api.repository_url
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint."
  value       = aws_db_instance.postgres.address
}

output "rds_port" {
  description = "RDS PostgreSQL port."
  value       = aws_db_instance.postgres.port
}

output "database_url_example" {
  description = "Example DATABASE_URL for the application."
  value       = "postgresql+asyncpg://${var.db_username}:<password>@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${var.db_name}"
  sensitive   = true
}