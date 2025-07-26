#!/bin/bash

# Learner Graph RAG System Deployment Script
# Usage: ./deploy.sh [environment] [action]
# Example: ./deploy.sh production deploy

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_DIR="${SCRIPT_DIR}/k8s"
NAMESPACE="learner-graph"
APP_NAME="learner-graph-rag-system"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check kustomize
    if ! command -v kustomize &> /dev/null; then
        log_warning "kustomize is not installed. Using kubectl kustomize instead."
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Build Docker image
build_image() {
    local tag=${1:-latest}
    log_info "Building Docker image with tag: $tag"
    
    docker build -t learner-graph:$tag .
    
    # If using a registry, push the image
    if [[ -n "$DOCKER_REGISTRY" ]]; then
        docker tag learner-graph:$tag $DOCKER_REGISTRY/learner-graph:$tag
        docker push $DOCKER_REGISTRY/learner-graph:$tag
        log_success "Image pushed to registry: $DOCKER_REGISTRY/learner-graph:$tag"
    fi
    
    log_success "Docker image built successfully"
}

# Deploy to Kubernetes
deploy() {
    local environment=${1:-development}
    log_info "Deploying to $environment environment..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply configurations
    if command -v kustomize &> /dev/null; then
        cd $K8S_DIR
        kustomize build . | kubectl apply -f -
    else
        kubectl apply -k $K8S_DIR
    fi
    
    # Wait for rollout
    log_info "Waiting for deployment rollout..."
    kubectl rollout status deployment/learner-graph-app -n $NAMESPACE --timeout=300s
    
    # Check service status
    kubectl get services -n $NAMESPACE
    kubectl get pods -n $NAMESPACE
    
    log_success "Deployment completed successfully"
}

# Rollback deployment
rollback() {
    log_info "Rolling back deployment..."
    kubectl rollout undo deployment/learner-graph-app -n $NAMESPACE
    kubectl rollout status deployment/learner-graph-app -n $NAMESPACE
    log_success "Rollback completed"
}

# Scale deployment
scale() {
    local replicas=${1:-3}
    log_info "Scaling deployment to $replicas replicas..."
    kubectl scale deployment/learner-graph-app --replicas=$replicas -n $NAMESPACE
    kubectl rollout status deployment/learner-graph-app -n $NAMESPACE
    log_success "Scaling completed"
}

# Get logs
logs() {
    local lines=${1:-100}
    log_info "Fetching logs (last $lines lines)..."
    kubectl logs -f deployment/learner-graph-app -n $NAMESPACE --tail=$lines
}

# Health check
health_check() {
    log_info "Performing health check..."
    
    # Get service URL
    SERVICE_URL=$(kubectl get service learner-graph-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    
    if [[ -z "$SERVICE_URL" ]]; then
        SERVICE_URL=$(kubectl get service learner-graph-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    fi
    
    if [[ -z "$SERVICE_URL" ]]; then
        log_warning "LoadBalancer not ready, using port-forward for health check"
        kubectl port-forward service/learner-graph-service 8080:80 -n $NAMESPACE &
        PF_PID=$!
        sleep 5
        SERVICE_URL="localhost:8080"
    fi
    
    # Perform health check
    if curl -f "http://$SERVICE_URL/health" &> /dev/null; then
        log_success "Health check passed - service is running"
    else
        log_error "Health check failed - service may not be ready"
        exit 1
    fi
    
    # Cleanup port-forward if used
    if [[ -n "$PF_PID" ]]; then
        kill $PF_PID 2>/dev/null || true
    fi
}

# Delete deployment
delete() {
    log_warning "This will delete the entire deployment. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "Deleting deployment..."
        kubectl delete -k $K8S_DIR
        log_success "Deployment deleted"
    else
        log_info "Deletion cancelled"
    fi
}

# Show status
status() {
    log_info "Deployment status:"
    echo
    kubectl get all -n $NAMESPACE
    echo
    log_info "Recent events:"
    kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | tail -10
}

# Main script logic
main() {
    local environment=${1:-development}
    local action=${2:-deploy}
    
    case $action in
        "build")
            check_prerequisites
            build_image $3
            ;;
        "deploy")
            check_prerequisites
            build_image latest
            deploy $environment
            health_check
            ;;
        "rollback")
            rollback
            ;;
        "scale")
            scale $3
            ;;
        "logs")
            logs $3
            ;;
        "health")
            health_check
            ;;
        "status")
            status
            ;;
        "delete")
            delete
            ;;
        *)
            echo "Usage: $0 [environment] [action] [options]"
            echo
            echo "Environments: development, staging, production"
            echo "Actions:"
            echo "  build [tag]       - Build Docker image"
            echo "  deploy           - Deploy to Kubernetes"
            echo "  rollback         - Rollback deployment"
            echo "  scale [replicas] - Scale deployment"
            echo "  logs [lines]     - Show application logs"
            echo "  health           - Perform health check"
            echo "  status           - Show deployment status"
            echo "  delete           - Delete deployment"
            echo
            echo "Examples:"
            echo "  $0 production deploy"
            echo "  $0 development scale 5"
            echo "  $0 staging logs 200"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 