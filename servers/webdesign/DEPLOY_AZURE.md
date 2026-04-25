# Azure Deployment Guide - WebDesign MCP

This guide provides enterprise-grade deployment instructions for the WebDesign MCP server on Azure using Private Endpoints and Managed Identity.

**Security Level**: Enterprise (org standards)
**Architecture**: Private Container Apps + Private ACR + Managed Identity

---

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│   Your Laptop   │────▶│  Private Endpoint   │────▶│  Azure Container │
│                 │     │  (PEP)              │     │  Apps            │
└─────────────────┘     └─────────────────────┘     └──────────────────┘
                              │                           │
                              ▼                           ▼
                       ┌─────────────────┐     ┌──────────────────┐
                       │  Private DNS    │     │  Azure Container │
                       │  Zone           │     │  Registry (ACR)  │
                       └─────────────────┘     └──────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Azure Monitor  │
                       │  Log Analytics  │
                       └─────────────────┘
```

---

## Prerequisites

- Azure CLI installed: `az --version`
- Azure subscription with Contributor access
- Azure tenant access
- Docker installed locally (for building)

---

## Step 1: Create Resource Group and VNet

```bash
# Login to Azure
az login --tenant your-org.onmicrosoft.com  # Replace with your tenant

# Create resource group
az group create \
  --name m2lab-webdesign-mcp-rg \
  --location westeurope \
  --tags \
    environment=production \
    project=webdesign-mcp \
    owner=your-team \
    cost-center=m2lab-eng

# Create Virtual Network
az network vnet create \
  --name m2lab-mcp-vnet \
  --resource-group m2lab-webdesign-mcp-rg \
  --address-prefixes 10.0.0.0/16 \
  --subnet-name containerapp-subnet \
  --subnet-prefixes 10.0.0.0/23

# Create private endpoint subnet
az network vnet subnet create \
  --name private-endpoint-subnet \
  --resource-group m2lab-webdesign-mcp-rg \
  --vnet-name m2lab-mcp-vnet \
  --address-prefixes 10.0.2.0/24
```

---

## Step 2: Create Private Container Registry (ACR)

```bash
# Create Premium ACR (required for private endpoints)
az acr create \
  --name m2labwebdesignmcp \
  --resource-group m2lab-webdesign-mcp-rg \
  --location westeurope \
  --sku Premium \
  --public-network-enabled false \
  --zone-redundancy enabled \
  --tags environment=production

# Enable admin user (for testing only, use Managed Identity in prod)
az acr update \
  --name m2labwebdesignmcp \
  --admin-enabled true

# Create private endpoint for ACR
az network private-endpoint create \
  --name m2labwebdesignmcp-pep \
  --resource-group m2lab-webdesign-mcp-rg \
  --location westeurope \
  --subnet private-endpoint-subnet \
  --private-connection-resource-id $(az acr show --name m2labwebdesignmcp --query id -o tsv) \
  --group-id registry

# Create private DNS zone for ACR
az network private-dns zone create \
  --resource-group m2lab-webdesign-mcp-rg \
  --name privatelink.azurecr.io

# Link DNS zone to VNet
az network private-dns link vnet create \
  --resource-group m2lab-webdesign-mcp-rg \
  --zone-name privatelink.azurecr.io \
  --name m2lab-mcp-dns-link \
  --virtual-network m2lab-mcp-vnet \
  --registration-enabled false

# Create DNS record
az network private-endpoint dns-zone-group create \
  --resource-group m2lab-webdesign-mcp-rg \
  --endpoint-name m2labwebdesignmcp-pep \
  --name m2labwebdesignmcp-zone-group \
  --private-dns-zone privatelink.azurecr.io \
  --zone-name privatelink.azurecr.io
```

---

## Step 3: Build and Push Docker Image

```bash
# Navigate to webdesign_mcp folder
cd /path/to/mcp-design-deploy/servers/webdesign/mcp_project

# Create optimized Dockerfile
cat > Dockerfile.azure << 'EOF'
FROM python:3.11-slim

# Security: Run as non-root
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

# Copy requirements first for layer caching
COPY mcp_project/pyproject.toml .
RUN pip install --no-cache-dir mcp

# Copy application
COPY mcp_project/ .

# Create output directory
RUN mkdir -p /app/output && chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Environment
ENV WEBDESIGN_OUTPUT_DIR=/app/output
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "print('healthy')" || exit 1

CMD ["python", "webdesign_server.py"]
EOF

# Build image
az acr build \
  --registry m2labwebdesignmcp \
  --image webdesign-mcp:v1.0.0 \
  --file Dockerfile.azure \
  .

# Verify image is in registry
az acr repository list --name m2labwebdesignmcp --output table
```

---

## Step 4: Create Log Analytics Workspace

```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --name m2lab-mcp-logs \
  --resource-group m2lab-webdesign-mcp-rg \
  --location westeurope \
  --sku PerGB2018

# Get workspace ID
WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --name m2lab-mcp-logs \
  --resource-group m2lab-webdesign-mcp-rg \
  --query customerId -o tsv)

# Get workspace key
WORKSPACE_KEY=$(az monitor log-analytics workspace get-shared-keys \
  --name m2lab-mcp-logs \
  --resource-group m2lab-webdesign-mcp-rg \
  --query primarySharedKey -o tsv)
```

---

## Step 5: Deploy Container Apps Environment

```bash
# Create Container Apps environment with VNet
az containerapp env create \
  --name m2lab-webdesign-mcp-env \
  --resource-group m2lab-webdesign-mcp-rg \
  --location westeurope \
  --infrastructure-subnet-resource-id "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/m2lab-webdesign-mcp-rg/providers/Microsoft.Network/virtualNetworks/m2lab-mcp-vnet/subnets/containerapp-subnet" \
  --logs-destination log-analytics \
  --logs-workspace-id "$WORKSPACE_ID" \
  --logs-workspace-key "$WORKSPACE_KEY"
```

---

## Step 6: Deploy WebDesign MCP Container App

```bash
# Create with system-assigned managed identity
az containerapp create \
  --name webdesign-mcp \
  --resource-group m2lab-webdesign-mcp-rg \
  --environment m2lab-webdesign-mcp-env \
  --image m2labwebdesignmcp.azurecr.io/webdesign-mcp:v1.0.0 \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1Gi \
  --system-assigned \
  --ingress internal \
  --target-port 8000 \
  --env-vars \
    WEBDESIGN_OUTPUT_DIR=/app/output

# Get managed identity principal ID
PRINCIPAL_ID=$(az containerapp identity show \
  --name webdesign-mcp \
  --resource-group m2lab-webdesign-mcp-rg \
  --query principalId -o tsv)

# Grant ACR pull access to managed identity
az acr role assignment create \
  --assignee $PRINCIPAL_ID \
  --role AcrPull \
  --registry m2labwebdesignmcp \
  --scope $(az acr show --name m2labwebdesignmcp --query id -o tsv)

# Update container to use managed identity (remove admin credentials)
az containerapp registry set \
  --name webdesign-mcp \
  --resource-group m2lab-webdesign-mcp-rg \
  --server m2labwebdesignmcp.azurecr.io \
  --identity system
```

---

## Step 7: Network Security Configuration

```bash
# Create NSG for subnet
az network nsg create \
  --name m2lab-mcp-nsg \
  --resource-group m2lab-webdesign-mcp-rg

# Add NSG rules
az network nsg rule create \
  --name allow-internal \
  --nsg-name m2lab-mcp-nsg \
  --resource-group m2lab-webdesign-mcp-rg \
  --priority 100 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-address-prefixes VirtualNetwork \
  --destination-port-ranges 80 443

# Deny all inbound from internet
az network nsg rule create \
  --name deny-internet \
  --nsg-name m2lab-mcp-nsg \
  --resource-group m2lab-webdesign-mcp-rg \
  --priority 4096 \
  --direction Inbound \
  --access Deny \
  --protocol '*' \
  --source-address-prefixes Internet

# Associate NSG with subnet
az network vnet subnet update \
  --name containerapp-subnet \
  --vnet-name m2lab-mcp-vnet \
  --resource-group m2lab-webdesign-mcp-rg \
  --network-security-group m2lab-mcp-nsg
```

---

## Step 8: Monitoring and Alerts

```bash
# Create diagnostic settings
az monitor diagnostic-settings create \
  --name m2lab-mcp-diagnostics \
  --resource $(az containerapp show --name webdesign-mcp --resource-group m2lab-webdesign-mcp-rg --query id -o tsv) \
  --workspace $(az monitor log-analytics workspace show --name m2lab-mcp-logs --resource-group m2lab-webdesign-mcp-rg --query id -o tsv) \
  --logs '[{"category":"ContainerAppConsoleLogs","enabled":true},{"category":"ContainerAppSystemLogs","enabled":true}]' \
  --metrics '[{"category":"AllMetrics","enabled":true}]'

# Create alert for high CPU
az monitor metrics alert create \
  --name high-cpu-alert \
  --resource-group m2lab-webdesign-mcp-rg \
  --scopes $(az containerapp show --name webdesign-mcp --resource-group m2lab-webdesign-mcp-rg --query id -o tsv) \
  --condition "avg cpu percentage > 80" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action $(az monitor action-group create --name m2lab-mcp-alerts --resource-group m2lab-webdesign-mcp-rg --short-name mcpalert --email-receiver your-email@example.com --query id -o tsv)
```

---

## Step 9: Verify Deployment

```bash
# Check container status
az containerapp show \
  --name webdesign-mcp \
  --resource-group m2lab-webdesign-mcp-rg \
  --query properties.runningStatus

# View logs
az containerapp logs show \
  --name webdesign-mcp \
  --resource-group m2lab-webdesign-mcp-rg \
  --follow

# Get private FQDN (for internal access)
az containerapp show \
  --name webdesign-mcp \
  --resource-group m2lab-webdesign-mcp-rg \
  --query properties.configuration.ingress.fqdn \
  --output tsv
```

---

## Security Checklist

### Network Security
- [ ] No public IP assigned to Container App (`--ingress internal`)
- [ ] VNet integration configured
- [ ] NSG rules restrict inbound traffic
- [ ] Private DNS zones configured
- [ ] Private Endpoints for ACR

### Identity & Access
- [ ] System-assigned Managed Identity enabled
- [ ] No admin credentials stored in code
- [ ] ACR uses Managed Identity for pull
- [ ] Least privilege RBAC assignments
- [ ] Regular access reviews scheduled

### Monitoring
- [ ] Log Analytics workspace configured
- [ ] Diagnostic settings enabled
- [ ] Container logs forwarded
- [ ] Alerts configured for anomalies
- [ ] Retention policy set (M2Lab compliance)

### Compliance
- [ ] Resource tags applied
- [ ] Cost center assigned
- [ ] Data residency: West Europe (EU)
- [ ] Encryption at rest enabled (default)
- [ ] Encryption in transit (TLS 1.2+)

---

## Cost Estimation

| Resource | Monthly Cost (EUR) |
|----------|-------------------|
| Container Apps (1 replica, 0.5 CPU, 1GB) | ~15-25 |
| Premium ACR | ~15 |
| Log Analytics (1GB/day) | ~10 |
| Private DNS Zone | ~0.50 |
| Data transfer (internal) | Minimal |
| **Total** | **~40-50 EUR/month** |

---

## Troubleshooting

### Container won't start
```bash
# Check events
az containerapp show \
  --name webdesign-mcp \
  --resource-group m2lab-webdesign-mcp-rg \
  --query properties.latestRevisionName \
  --output tsv | xargs -I {} az containerapp revision show \
    --name webdesign-mcp \
    --resource-group m2lab-webdesign-mcp-rg \
    --revision {}

# Check logs
az containerapp logs show \
  --name webdesign-mcp \
  --resource-group m2lab-webdesign-mcp-rg \
  --tail 100
```

### Can't pull image from ACR
```bash
# Verify managed identity has AcrPull
az role assignment list \
  --assignee $(az containerapp identity show --name webdesign-mcp --resource-group m2lab-webdesign-mcp-rg --query principalId -o tsv) \
  --all \
  --query "[?roleDefinitionName=='AcrPull']"

# Check ACR network rules
az acr network-rule list --name m2labwebdesignmcp
```

### Access denied from external
```bash
# Verify ingress is internal only
az containerapp ingress show \
  --name webdesign-mcp \
  --resource-group m2lab-webdesign-mcp-rg \
  --query external

# Should return: false
```

---

## Org-Specific Considerations

1. **Tenant**: Deploy in your Azure AD tenant
2. **Region**: West Europe for EU data residency
3. **Compliance**: Align with ISO 27001 controls
4. **Backup**: Document recovery procedures
5. **Network**: Integrate with corporate network if needed
6. **Secrets**: Use Azure Key Vault for any secrets (future enhancement)

---

## Next Steps

1. [ ] Review architecture with security team
2. [ ] Set up CI/CD pipeline (GitHub Actions → Azure DevOps)
3. [ ] Implement Key Vault for secrets
4. [ ] Add Application Insights for APM
5. [ ] Configure backup/disaster recovery
6. [ ] Document runbook for operations team

---

**Last Updated**: March 2025
**Owner: M2Lab Engineering Team
**Review Cycle**: Quarterly
