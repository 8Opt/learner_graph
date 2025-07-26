#!/bin/bash

# ==============================================================================
# Environment Setup Script for Learner Graph RAG System
# ==============================================================================
# This script helps set up environment variables for different environments
# ==============================================================================

set -e

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

# Generate secure JWT secret
generate_jwt_secret() {
    if command -v openssl &> /dev/null; then
        openssl rand -base64 32
    else
        # Fallback for systems without openssl
        python3 -c "import secrets; print(secrets.token_urlsafe(32))"
    fi
}

# Setup development environment
setup_development() {
    log_info "Setting up development environment..."
    
    if [ -f ".env" ]; then
        log_warning ".env file already exists. Creating backup..."
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Copy development template
    cp environment.dev .env
    
    # Generate JWT secret
    JWT_SECRET=$(generate_jwt_secret)
    sed -i.bak "s/dev-jwt-secret-key-change-in-production-please/$JWT_SECRET/" .env
    rm .env.bak
    
    log_success "Development environment created!"
    log_info "Configuration file: .env"
    log_info "You can now start the application with: python -m app.main"
}

# Setup production environment
setup_production() {
    log_info "Setting up production environment..."
    
    if [ -f ".env" ]; then
        log_warning ".env file already exists. Creating backup..."
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Copy template
    cp environment.template .env
    
    # Generate secure JWT secret
    JWT_SECRET=$(generate_jwt_secret)
    sed -i.bak "s/your-super-secret-jwt-key-here-please-change-this/$JWT_SECRET/" .env
    
    # Set production defaults
    sed -i.bak "s/ENVIRONMENT=development/ENVIRONMENT=production/" .env
    sed -i.bak "s/LOG_LEVEL=INFO/LOG_LEVEL=WARNING/" .env
    sed -i.bak "s/DEBUG=false/DEBUG=false/" .env
    sed -i.bak "s/API_RATE_LIMIT_PER_MINUTE=1000/API_RATE_LIMIT_PER_MINUTE=100/" .env
    
    rm .env.bak
    
    log_success "Production environment template created!"
    log_warning "IMPORTANT: Please review and update the following in .env file:"
    echo "  - DATABASE_URL (use PostgreSQL for production)"
    echo "  - REDIS_URL (configure Redis cluster if needed)"
    echo "  - SMTP_* settings for email notifications"
    echo "  - CORS_ALLOWED_ORIGINS (set your domain)"
    echo "  - All other service-specific credentials"
}

# Setup testing environment
setup_testing() {
    log_info "Setting up testing environment..."
    
    if [ -f ".env.test" ]; then
        log_warning ".env.test file already exists. Creating backup..."
        cp .env.test .env.test.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Create test environment
    cat > .env.test << EOF
# Test Environment Configuration
DATABASE_URL=sqlite:///./test_learner_graph.db
REDIS_URL=redis://localhost:6379
TESTING=true
LOG_LEVEL=DEBUG
AB_TEST_ENABLED=false
METRICS_ENABLED=false
SMTP_SERVER=
JWT_SECRET_KEY=test-jwt-secret-not-for-production
ENVIRONMENT=test
EOF
    
    log_success "Testing environment created: .env.test"
}

# Setup Docker environment
setup_docker() {
    log_info "Setting up Docker environment..."
    
    if [ -f ".env.docker" ]; then
        log_warning ".env.docker file already exists. Creating backup..."
        cp .env.docker .env.docker.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Create Docker environment
    cat > .env.docker << EOF
# Docker Environment Configuration
DATABASE_URL=sqlite:///./learner_graph.db
REDIS_URL=redis://redis:6379
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=docker
JWT_SECRET_KEY=$(generate_jwt_secret)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
EOF
    
    log_success "Docker environment created: .env.docker"
    log_info "Use this with: docker-compose --env-file .env.docker up"
}

# Setup Kubernetes secrets
setup_kubernetes_secrets() {
    log_info "Setting up Kubernetes secrets..."
    
    if [ -f "k8s/secrets.env" ]; then
        log_warning "k8s/secrets.env file already exists. Creating backup..."
        cp k8s/secrets.env k8s/secrets.env.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Copy secrets template
    cp k8s/secrets.env.template k8s/secrets.env
    
    # Generate secure values
    JWT_SECRET=$(generate_jwt_secret)
    DB_PASSWORD=$(generate_jwt_secret | head -c 16)
    REDIS_PASSWORD=$(generate_jwt_secret | head -c 16)
    GRAFANA_PASSWORD=$(generate_jwt_secret | head -c 12)
    
    # Update secrets file
    sed -i.bak "s/your-super-secret-jwt-key-generate-new-one/$JWT_SECRET/" k8s/secrets.env
    sed -i.bak "s/your-secure-database-password-here/$DB_PASSWORD/" k8s/secrets.env
    sed -i.bak "s/your-redis-password-here/$REDIS_PASSWORD/" k8s/secrets.env
    sed -i.bak "s/your-secure-grafana-admin-password/$GRAFANA_PASSWORD/" k8s/secrets.env
    
    rm k8s/secrets.env.bak
    
    log_success "Kubernetes secrets created: k8s/secrets.env"
    log_warning "IMPORTANT: Update the remaining credentials in k8s/secrets.env"
    log_warning "Never commit k8s/secrets.env to version control!"
}

# Validate environment
validate_environment() {
    log_info "Validating environment configuration..."
    
    if [ ! -f ".env" ]; then
        log_error ".env file not found. Please run setup first."
        exit 1
    fi
    
    # Check required variables
    required_vars=("DATABASE_URL" "REDIS_URL" "JWT_SECRET_KEY")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" .env || grep -q "^$var=$" .env || grep -q "your-.*-here" .env; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -eq 0 ]; then
        log_success "Environment validation passed!"
    else
        log_error "Missing or incomplete configuration for:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        exit 1
    fi
}

# Show help
show_help() {
    echo "Learner Graph RAG System - Environment Setup"
    echo
    echo "Usage: $0 [command]"
    echo
    echo "Commands:"
    echo "  dev         Setup development environment (.env)"
    echo "  prod        Setup production environment template (.env)"
    echo "  test        Setup testing environment (.env.test)"
    echo "  docker      Setup Docker environment (.env.docker)"
    echo "  k8s         Setup Kubernetes secrets (k8s/secrets.env)"
    echo "  validate    Validate current environment configuration"
    echo "  help        Show this help message"
    echo
    echo "Examples:"
    echo "  $0 dev       # Setup for local development"
    echo "  $0 prod      # Setup for production deployment"
    echo "  $0 k8s       # Generate Kubernetes secrets"
}

# Main script logic
main() {
    case "${1:-help}" in
        "dev"|"development")
            setup_development
            ;;
        "prod"|"production")
            setup_production
            ;;
        "test"|"testing")
            setup_testing
            ;;
        "docker")
            setup_docker
            ;;
        "k8s"|"kubernetes")
            setup_kubernetes_secrets
            ;;
        "validate")
            validate_environment
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@" 