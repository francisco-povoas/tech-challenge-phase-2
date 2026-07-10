terraform {
  backend "s3" {
    bucket = "tfstate-mvp-oficina-706619443268"
    key    = "staging/terraform.tfstate"
    region = "us-east-1"
  }
}