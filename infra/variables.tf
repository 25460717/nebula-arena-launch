variable "project_id" {
  description = "The GCP Project ID"
  type        = string
  default     = "nebula-arena-prod"
}

variable "region" {
  description = "Primary GCP Region for Nebula Arena"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "us-central1-a"
}

variable "vpc_name" {
  description = "VPC Network Name"
  type        = string
  default     = "nebula-vpc"
}

variable "subnet_cidr" {
  description = "CIDR range for the dedicated gaming subnet"
  type        = string
  default     = "10.10.0.0/20"
}

variable "pods_cidr" {
  description = "Secondary CIDR range for GKE Pods"
  type        = string
  default     = "10.20.0.0/16"
}

variable "services_cidr" {
  description = "Secondary CIDR range for GKE Services"
  type        = string
  default     = "10.30.0.0/20"
}

variable "min_nodes" {
  description = "Minimum nodes in the dedicated Game Server Node Pool"
  type        = number
  default     = 2
}

variable "max_nodes" {
  description = "Maximum nodes in the dedicated Game Server Node Pool for autoscaling"
  type        = number
  default     = 30
}

variable "machine_type" {
  description = "Machine type for dedicated game nodes (On-Demand e2-standard-4: 4 vCPU, 16GB RAM)"
  type        = string
  default     = "e2-standard-4"
}
