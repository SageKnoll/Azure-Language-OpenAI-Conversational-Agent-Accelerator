# Manually Deploying Bicep Template:
Create resource group:
```
az group create \
    --name <rg-name> \
    --location <rg-location>
```

Deploy Bicep template to resource group:
```
az deployment group create \
    --name <deployment-name> \
    --resource-group <rg-name> \
    --template-file main.bicep \
    --parameters @main.bicepparam
```