terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.20.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Dedicated VPC for Game Operations
resource "google_compute_network" "nebula_vpc" {
  name                    = var.vpc_name
  auto_create_subnetworks = false
  description             = "VPC network for Nebula Arena high-performance gaming infrastructure"
}

# 2. Subnet with Secondary IP Ranges for GKE VPC-native Cluster
resource "google_compute_subnetwork" "nebula_subnet" {
  name                     = "${var.vpc_name}-gameserver-subnetwork"
  ip_cidr_range            = var.subnet_cidr
  region                   = var.region
  network                  = google_compute_network.nebula_vpc.id
  private_ip_google_access = true

  secondary_ip_range {
    range_name    = "nebula-pods"
    ip_cidr_range = var.pods_cidr
  }

  secondary_ip_range {
    range_name    = "nebula-services"
    ip_cidr_range = var.services_cidr
  }
}

# 3. Firewall Rules for Game Traffic (Agones UDP Port Range 7000-8000)
resource "google_compute_firewall" "allow_game_traffic" {
  name    = "nebula-allow-agones-game-ports"
  network = google_compute_network.nebula_vpc.name

  allow {
    protocol = "udp"
    ports    = ["7000-8000"]
  }

  allow {
    protocol = "tcp"
    ports    = ["8080", "9090"] # HTTP API & Prometheus metrics
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["game-server-node"]
}

# 4. GKE Regional Cluster (Zonal or Regional control plane, VPC-native)
resource "google_container_cluster" "nebula_gke" {
  name     = "nebula-arena-gke-cluster"
  location = var.zone

  network    = google_compute_network.nebula_vpc.name
  subnetwork = google_compute_subnetwork.nebula_subnet.name

  remove_default_node_pool = true
  initial_node_count       = 1

  ip_allocation_policy {
    cluster_secondary_range_name  = "nebula-pods"
    services_secondary_range_name = "nebula-services"
  }

  addons_config {
    http_load_balancing {
      disabled = false
    }
    network_policy_config {
      disabled = false
    }
  }

  release_channel {
    channel = "REGULAR"
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
}

# 5. Dedicated On-Demand Node Pool for Game Servers (e2-standard-4)
# On-Demand prevents live match drops (NEVER preemptible/Spot for active game servers)
resource "google_container_node_pool" "game_server_nodes" {
  name       = "nebula-game-servers-pool"
  location   = var.zone
  cluster    = google_container_cluster.nebula_gke.name

  autoscaling {
    min_node_count = var.min_nodes
    max_node_count = var.max_nodes
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    machine_type = var.machine_type
    preemptible  = false # STRICT ON-DEMAND: Zero disruption for active matches
    tags         = ["game-server-node"]

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
      "https://www.googleapis.com/auth/monitoring",
      "https://www.googleapis.com/auth/logging.write",
    ]

    labels = {
      "agones.dev/role" = "gameserver"
      "environment"     = "production"
      "workload"        = "nebula-arena"
    }

    taint {
      key    = "agones.dev/role"
      value  = "gameserver"
      effect = "NO_SCHEDULE"
    }
  }
}

# 6. Firestore Database in Datastore / Native Mode for Leaderboards & Player Stats
resource "google_firestore_database" "nebula_leaderboard_db" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  concurrency_mode                = "OPTIMISTIC"
  app_engine_integration_mode     = "DISABLED"
  point_in_time_recovery_enablement = "POINT_IN_TIME_RECOVERY_ENABLED"
  delete_protection_state         = "DELETE_PROTECTION_ENABLED"
}
