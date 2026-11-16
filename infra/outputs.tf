output "vpc_id" {
  description = "The ID of the Nebula VPC"
  value       = google_compute_network.nebula_vpc.id
}

output "subnet_id" {
  description = "The ID of the gaming subnet"
  value       = google_compute_subnetwork.nebula_subnet.id
}

output "cluster_name" {
  description = "The GKE cluster name"
  value       = google_container_cluster.nebula_gke.name
}

output "cluster_endpoint" {
  description = "Cluster endpoint IP"
  value       = google_container_cluster.nebula_gke.endpoint
  sensitive   = true
}

output "node_pool_name" {
  description = "Dedicated Game Server Node Pool"
  value       = google_container_node_pool.game_server_nodes.name
}

output "firestore_database_name" {
  description = "Firestore Database for Leaderboard"
  value       = google_firestore_database.nebula_leaderboard_db.name
}
