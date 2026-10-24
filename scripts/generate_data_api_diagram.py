#!/usr/bin/env python3
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch, Rectangle
import matplotlib.lines as mlines

fig, ax = plt.subplots(1, 1, figsize=(16, 12))
ax.set_xlim(0, 16)
ax.set_ylim(0, 12)
ax.axis('off')

# Colors
color_api = '#4A90E2'
color_plane = '#7ED321'
color_storage = '#F5A623'
color_security = '#D0021B'
color_worker = '#9013FE'
color_broker = '#50E3C2'

# Title
ax.text(8, 11.5, 'Enterprise Python Data API - Production Architecture', 
        ha='center', va='center', fontsize=18, fontweight='bold')

# API Gateway
gateway = FancyBboxPatch((0.5, 10), 2.5, 0.8, boxstyle="round,pad=0.1", 
                         facecolor=color_api, alpha=0.7, edgecolor='black')
ax.add_patch(gateway)
ax.text(1.75, 10.4, 'API Gateway\n(Traefik/NGINX)', ha='center', va='center', 
        fontsize=9, fontweight='bold')

# FastAPI Control Plane
api_box = FancyBboxPatch((4, 9.8), 4, 1, boxstyle="round,pad=0.1",
                        facecolor=color_api, alpha=0.8, edgecolor='black')
ax.add_patch(api_box)
ax.text(6, 10.3, 'FastAPI Application API (Control Plane)', ha='center', va='center',
        fontsize=11, fontweight='bold')
ax.text(6, 10.0, 'IAM/RBAC | Dataset Registry | Job Management | Audit', ha='center', va='center',
        fontsize=8)

# Identity
idp = FancyBboxPatch((9.5, 9.8), 2.5, 1, boxstyle="round,pad=0.1",
                     facecolor=color_security, alpha=0.7, edgecolor='black')
ax.add_patch(idp)
ax.text(10.75, 10.4, 'Identity & Access', ha='center', va='center',
        fontsize=10, fontweight='bold')
ax.text(10.75, 10.05, 'Keycloak + OIDC', ha='center', va='center', fontsize=8)

# Processing Plane
proc_box = FancyBboxPatch((1, 7.5), 6, 1.8, boxstyle="round,pad=0.1",
                         facecolor=color_worker, alpha=0.6, edgecolor='black')
ax.add_patch(proc_box)
ax.text(4, 9.0, 'Data Processing Plane', ha='center', va='center',
        fontsize=11, fontweight='bold')
ax.text(2.5, 8.4, 'Python Workers\n(Celery)', ha='center', va='center', fontsize=8)
ax.text(4, 8.4, 'Polars + PyArrow', ha='center', va='center', fontsize=8)
ax.text(5.5, 8.4, 'Pandera (Quality)', ha='center', va='center', fontsize=8)
ax.text(4, 7.9, 'Batch Processing', ha='center', va='center', fontsize=7, style='italic')

# Streaming
stream_box = FancyBboxPatch((8, 7.5), 3, 1.8, boxstyle="round,pad=0.1",
                           facecolor=color_broker, alpha=0.6, edgecolor='black')
ax.add_patch(stream_box)
ax.text(9.5, 9.0, 'Real-time Processing', ha='center', va='center',
        fontsize=11, fontweight='bold')
ax.text(9.5, 8.4, 'Redpanda/Kafka', ha='center', va='center', fontsize=9)
ax.text(9.5, 7.9, 'Event Consumers', ha='center', va='center', fontsize=8)

# Broker/Queue
broker = FancyBboxPatch((12, 7.8), 2.5, 1.2, boxstyle="round,pad=0.1",
                        facecolor=color_broker, alpha=0.8, edgecolor='black')
ax.add_patch(broker)
ax.text(13.25, 8.6, 'Job Queue', ha='center', va='center',
        fontsize=10, fontweight='bold')
ax.text(13.25, 8.2, 'Celery + Redis', ha='center', va='center', fontsize=8)

# Storage Plane
storage_box = FancyBboxPatch((1, 4.5), 8.5, 2.2, boxstyle="round,pad=0.1",
                             facecolor=color_storage, alpha=0.6, edgecolor='black')
ax.add_patch(storage_box)
ax.text(5.25, 6.4, 'Storage Plane', ha='center', va='center',
        fontsize=11, fontweight='bold')
ax.text(2.8, 5.8, 'PostgreSQL\n(Metadata/Jobs/RBAC/Audit)', ha='center', va='center', fontsize=8)
ax.text(5.25, 5.8, 'S3-Compatible Object Storage\n(MinIO/S3)', ha='center', va='center', fontsize=8)
ax.text(7.7, 5.8, 'Parquet + PyArrow\n(Raw/Curated)', ha='center', va='center', fontsize=8)
ax.text(5.25, 5.0, 'Data Formats & Metadata', ha='center', va='center', fontsize=7, style='italic')

# Observability
obs = FancyBboxPatch((10.5, 4.5), 4, 2.2, boxstyle="round,pad=0.1",
                     facecolor='#BD10E0', alpha=0.6, edgecolor='black')
ax.add_patch(obs)
ax.text(12.5, 6.4, 'Observability', ha='center', va='center',
        fontsize=11, fontweight='bold')
ax.text(12.5, 5.8, 'OpenTelemetry', ha='center', va='center', fontsize=8)
ax.text(12.5, 5.4, 'Prometheus + Grafana', ha='center', va='center', fontsize=8)
ax.text(12.5, 5.0, 'Tracing, Metrics, Logs', ha='center', va='center', fontsize=7, style='italic')

# Hybrid Cloud Zones
# On-Prem
onprem = Rectangle((0.3, 2), 7, 1.8, facecolor='#E8F4FD', alpha=0.6, 
                   edgecolor='blue', linewidth=2)
ax.add_patch(onprem)
ax.text(3.8, 3.5, 'On-Premises - Private Data Zone', ha='center', va='center',
        fontsize=10, fontweight='bold')
ax.text(1.8, 2.9, 'Private PostgreSQL\n(MinIO)', ha='center', va='center', fontsize=7)
ax.text(3.8, 2.9, 'Sensitive Data\nProcessing', ha='center', va='center', fontsize=7)
ax.text(5.8, 2.9, 'Private Connectors', ha='center', va='center', fontsize=7)

# Cloud
cloud = Rectangle((8.7, 2), 6.8, 1.8, facecolor='#F0F8FF', alpha=0.6,
                  edgecolor='cyan', linewidth=2)
ax.add_patch(cloud)
ax.text(12.1, 3.5, 'Cloud - Application & Elastic Processing Zone', ha='center', va='center',
        fontsize=10, fontweight='bold')
ax.text(10.2, 2.9, 'API Gateway\n(FastAPI)', ha='center', va='center', fontsize=7)
ax.text(12.1, 2.9, 'Elastic Workers\n(Scalable)', ha='center', va='center', fontsize=7)
ax.text(14.0, 2.9, 'Event Broker', ha='center', va='center', fontsize=7)

# Connections
# Gateway to API
ax.annotate('', xy=(4, 10.3), xytext=(3, 10.4),
            arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
# API to Processing
ax.annotate('', xy=(4, 9.3), xytext=(6, 9.8),
            arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
# API to IDP
ax.annotate('', xy=(9.5, 10.3), xytext=(8, 10.3),
            arrowprops=dict(arrowstyle='<->', lw=1.5, color=color_security))
# Processing to Storage
ax.annotate('', xy=(4, 6.7), xytext=(4, 7.5),
            arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
# Processing to Broker
ax.annotate('', xy=(12, 8.4), xytext=(7, 8.4),
            arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
# Broker to Workers
ax.annotate('', xy=(8, 8.4), xytext=(12, 8.4),
            arrowprops=dict(arrowstyle='<->', lw=1.5, color='black'))
# Zones connection
ax.annotate('Site-to-Site VPN / Private Link\n(TLS + Firewall)', xy=(8.7, 2.9), xytext=(7.3, 2.9),
            arrowprops=dict(arrowstyle='<->', lw=2, color='red'), 
            ha='center', va='center', fontsize=7, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

# Legend
legend_elements = [
    mpatches.Patch(color=color_api, label='API/Control Plane'),
    mpatches.Patch(color=color_worker, label='Processing Plane'),
    mpatches.Patch(color=color_broker, label='Streaming/Queue'),
    mpatches.Patch(color=color_storage, label='Storage Plane'),
    mpatches.Patch(color=color_security, label='Security/Identity'),
    mpatches.Patch(color='#BD10E0', label='Observability')
]
ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0.02, 0.98), fontsize=8)

plt.tight_layout()
plt.savefig('/Users/maaeyeng/data-engineering-platform/docs/api/python-data-api/enterprise_data_api_architecture.png', 
            dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig('/Users/maaeyeng/data-engineering-platform/docs/api/python-data-api/enterprise_data_api_architecture.pdf', 
            bbox_inches='tight', facecolor='white')
print("Diagrams generated successfully!")
