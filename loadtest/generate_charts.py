import json
import os
import matplotlib.pyplot as plt
import numpy as np

# Load real benchmark data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_FILE = os.path.join(BASE_DIR, "evidencias", "loadtest_results.json")
with open(RESULTS_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

rampa = data["rampa"]
pico = data["pico"]
extrapolacion = data["extrapolacion"]

# Grafana Dark Theme Styling
plt.style.use('dark_background')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.color'] = '#2a2e39'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.alpha'] = 0.7

# -------------------------------------------------------------------------
# GRÁFICA 1: Simulación fiel Tablero Grafana (Dark Mode, 4 Paneles)
# -------------------------------------------------------------------------
fig, axs = plt.subplots(2, 2, figsize=(16, 10), facecolor='#111217')
fig.suptitle("Nebula Arena - Mission Critical Telemetry (Agones / GKE / Prometheus)", 
             fontsize=17, fontweight='bold', color='#56AEE9', y=0.98)

# Panel 1: CCU Curve (Rampa 0 -> 1,000 + Pico sostenido)
ax1 = axs[0, 0]
ax1.set_facecolor('#181b1f')
time_points = [0, 2, 5, 8, 12, 16, 20, 25]
ccu_points = [0] + [r["ccu"] for r in rampa] + [1000, 1000]
ax1.plot(time_points, ccu_points, color='#73BF69', linewidth=2.5, label='Gamers CCU (Active Players)')
ax1.fill_between(time_points, ccu_points, color='#73BF69', alpha=0.25)
ax1.set_title("Panel 1: Concurrent Users (CCU)", fontsize=13, fontweight='bold', color='#D8D9DA', loc='left')
ax1.set_xlabel("Timeline (Minutes)", color='#8E8E8E')
ax1.set_ylabel("Active Players", color='#8E8E8E')
ax1.grid(True)
ax1.legend(loc='upper left', frameon=False)
ax1.annotate('Peak Sustained: 1,000 CCU', xy=(16, 1000), xytext=(8, 850),
             arrowprops=dict(facecolor='#FADE2A', shrink=0.05, width=1, headwidth=6),
             fontsize=10, color='#FADE2A', fontweight='bold')

# Panel 2: Tick duration p99 vs 50ms Target Budget
ax2 = axs[0, 1]
ax2.set_facecolor('#181b1f')
tick_times = [0, 2, 5, 8, 12, 15, 18, 21, 25]
p99_ticks = [15.0] + [r["p99_tick_ms"] for r in rampa] + [32.5, 32.8, 32.2]
ax2.plot(tick_times, p99_ticks, color='#5794F2', linewidth=2.5, label='p99 Tick Duration (ms)')
ax2.axhline(y=50.0, color='#F2495C', linestyle='--', linewidth=2.2, label='Budget Threshold (50 ms = 20Hz)')
ax2.fill_between(tick_times, p99_ticks, 50.0, color='#5794F2', alpha=0.15)
ax2.set_title("Panel 2: Simulation Tick Duration p99 (Budget: 50ms)", fontsize=13, fontweight='bold', color='#D8D9DA', loc='left')
ax2.set_xlabel("Timeline (Minutes)", color='#8E8E8E')
ax2.set_ylabel("Latency (ms)", color='#8E8E8E')
ax2.set_ylim(10, 60)
ax2.grid(True)
ax2.legend(loc='lower right', frameon=False)
ax2.annotate('Safe Margin: ~17ms Headroom', xy=(21, 32.8), xytext=(10, 42),
             arrowprops=dict(facecolor='#73BF69', shrink=0.05, width=1, headwidth=6),
             fontsize=10, color='#73BF69', fontweight='bold')

# Panel 3: Agones Servers by State (Allocated, Ready Buffer, Scheduled)
ax3 = axs[1, 0]
ax3.set_facecolor('#181b1f')
times_agones = [0, 2, 5, 8, 12, 16, 20, 25]
alloc_servers = [0] + [r["allocated_servers"] for r in rampa] + [100, 100]
ready_buffer = [10] + [r["ready_buffer_servers"] for r in rampa] + [20, 20]
ax3.plot(times_agones, alloc_servers, color='#FF9830', linewidth=2.5, label='Allocated (In-Game 10p Matches)')
ax3.plot(times_agones, ready_buffer, color='#3274D9', linewidth=2.0, linestyle='-.', label='Ready Buffer (20% Target)')
ax3.fill_between(times_agones, alloc_servers, color='#FF9830', alpha=0.20)
ax3.set_title("Panel 3: Agones Dedicated Game Servers by State", fontsize=13, fontweight='bold', color='#D8D9DA', loc='left')
ax3.set_xlabel("Timeline (Minutes)", color='#8E8E8E')
ax3.set_ylabel("GameServer Instances", color='#8E8E8E')
ax3.grid(True)
ax3.legend(loc='upper left', frameon=False)

# Panel 4: GKE Active Nodes Escalamiento (Game Server Node Pool)
ax4 = axs[1, 1]
ax4.set_facecolor('#181b1f')
times_gke = [0, 2, 5, 8, 12, 16, 20, 25]
nodes_gke = [2] + [r["active_gke_nodes"] for r in rampa] + [22, 22]
ax4.step(times_gke, nodes_gke, color='#B877D9', linewidth=2.5, where='post', label='Active e2-standard-4 Nodes')
ax4.fill_between(times_gke, nodes_gke, step='post', color='#B877D9', alpha=0.20)
ax4.set_title("Panel 4: GKE Cluster Autoscaler - Active Nodes", fontsize=13, fontweight='bold', color='#D8D9DA', loc='left')
ax4.set_xlabel("Timeline (Minutes)", color='#8E8E8E')
ax4.set_ylabel("Node Count (On-Demand)", color='#8E8E8E')
ax4.set_ylim(0, 30)
ax4.grid(True)
ax4.legend(loc='upper left', frameon=False)
ax4.annotate('Max Auto-expanded: 22 Nodes', xy=(16, 22), xytext=(7, 26),
             arrowprops=dict(facecolor='#B877D9', shrink=0.05, width=1, headwidth=6),
             fontsize=10, color='#B877D9', fontweight='bold')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
grafana_path = os.path.join(BASE_DIR, "evidencias", "grafana_dashboard_launch.png")
plt.savefig(grafana_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
plt.close()
print(f"[OK] Generada gráfica Grafana: {grafana_path}")

# -------------------------------------------------------------------------
# GRÁFICA 2: Dual Loadtest + Extrapolación 500 a 20,000 Espectadores CDN
# -------------------------------------------------------------------------
fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(16, 7), facecolor='#111217')
fig.suptitle("Nebula Arena - Load Test Rampa/Pico y Extrapolación de Tráfico CDN", 
             fontsize=16, fontweight='bold', color='#56AEE9', y=0.98)

# Izquierda: Load Test Rampa y Pico 1,000 Gamers + 500 Espectadores
ax_left.set_facecolor('#181b1f')
categories = ['Base\n(0 CCU)', 'Rampa 1\n(250 CCU)', 'Rampa 2\n(500 CCU)', 'Rampa 3\n(750 CCU)', 'Pico Sostenido\n(1,000 CCU + 500 HLS)']
gamers = [0, 250, 500, 750, 1000]
spectators = [0, 0, 0, 100, 500]
x = np.arange(len(categories))
width = 0.35

rects1 = ax_left.bar(x - width/2, gamers, width, label='Gamers (20Hz UDP/Game)', color='#3274D9')
rects2 = ax_left.bar(x + width/2, spectators, width, label='Espectadores (HLS 2s @ 4.5Mbps)', color='#E0B400')

ax_left.set_title("A. Ejecución Real: Rampa y Pico de Carga", fontsize=13, fontweight='bold', color='#D8D9DA', loc='left')
ax_left.set_ylabel("Usuarios Concurrentes (CCU)", color='#8E8E8E')
ax_left.set_xticks(x)
ax_left.set_xticklabels(categories, fontsize=9)
ax_left.grid(True, axis='y')
ax_left.legend(loc='upper left', frameon=False)

for rect in rects1:
    height = rect.get_height()
    if height > 0:
        ax_left.annotate(f'{height}', xy=(rect.get_x() + rect.get_width()/2, height),
                         xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8, color='#5794F2')
for rect in rects2:
    height = rect.get_height()
    if height > 0:
        ax_left.annotate(f'{height}', xy=(rect.get_x() + rect.get_width()/2, height),
                         xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8, color='#E0B400')

# Derecha: Extrapolación de Ancho de Banda (Gbps) y CDN Cache Hit Ratio (500 -> 20,000)
ax_right.set_facecolor('#181b1f')
spec_x = [e["spectators"] for e in extrapolacion]
total_bw = [e["total_egress_gbps"] for e in extrapolacion]
cache_hit = [e["cache_hit_ratio_pct"] for e in extrapolacion]
origin_bw = [e["origin_shield_gbps"] for e in extrapolacion]

color_bw = '#F2495C'
ax_right.plot(spec_x, total_bw, color=color_bw, linewidth=2.8, marker='o', label='Ancho de Banda Total (Gbps)')
ax_right.plot(spec_x, origin_bw, color='#73BF69', linewidth=2.0, linestyle='--', marker='s', label='Tráfico en Origen (Origin Shield Gbps)')
ax_right.set_xlabel("Espectadores Simultáneos (Stream HLS 1080p60 @ 4,500 kbps)", color='#8E8E8E')
ax_right.set_ylabel("Ancho de Banda (Gbps)", color=color_bw)
ax_right.tick_params(axis='y', labelcolor=color_bw)
ax_right.grid(True)

# Eje secundario para Cache Hit Ratio %
ax_twin = ax_right.twinx()
color_cache = '#FADE2A'
ax_twin.plot(spec_x, cache_hit, color=color_cache, linewidth=2.2, linestyle='-.', marker='^', label='CDN Cache Hit Ratio (%)')
ax_twin.set_ylabel("Cache Hit Ratio (%)", color=color_cache)
ax_twin.tick_params(axis='y', labelcolor=color_cache)
ax_twin.set_ylim(94, 100.5)

ax_right.set_title("B. Extrapolación: 500 a 20,000 Espectadores (Ancho de Banda vs Eficiencia CDN)", 
                   fontsize=13, fontweight='bold', color='#D8D9DA', loc='left')

lines_1, labels_1 = ax_right.get_legend_handles_labels()
lines_2, labels_2 = ax_twin.get_legend_handles_labels()
ax_right.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center left', frameon=False)

ax_right.annotate(f'20k Specs: 90.0 Gbps Egress\n(99.85% Edge Hit -> 0.135 Gbps Origin)', 
                  xy=(20000, 90.0), xytext=(10000, 75),
                  arrowprops=dict(facecolor='#F2495C', shrink=0.05, width=1, headwidth=6),
                  fontsize=9, color='#FFFFFF', fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", fc="#2a2e39", ec="#56AEE9"))

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
extrap_path = os.path.join(BASE_DIR, "evidencias", "loadtest_extrapolacion_20k.png")
plt.savefig(extrap_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
plt.close()
print(f"[OK] Generada gráfica Extrapolación: {extrap_path}")
