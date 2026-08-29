# ATHENA Production Deployment Guide

## 1. Local Development (Docker Compose)
```bash
docker-compose up -d
```
Starts TimescaleDB (PostgreSQL 16), Redis, Zookeeper, Kafka, FastAPI backend, Next.js Web dashboard, Prometheus, and Grafana.

---

## 2. Production Kubernetes (Helm / Manifests)
Deploy to Kubernetes cluster:
```bash
kubectl apply -f infrastructure/kubernetes/deployment.yaml
```
- Multi-replica API deployment with readiness/liveness probes.
- Ingress with TLS termination and Prometheus metrics scraping.
