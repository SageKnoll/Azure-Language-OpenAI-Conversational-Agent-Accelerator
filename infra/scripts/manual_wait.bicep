@description('Location for all resources.')
param location string = resourceGroup().location

@secure()
param vm_admin_password string = newGuid()
param vm_admin_username string = 'azureuser'

resource vnet 'Microsoft.Network/virtualNetworks@2024-05-01' = {
  name: 'vnet-manual-wait'
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: ['10.0.0.0/16']
    }
    subnets: [
      {
        name: 'sn-vm'
        properties: {
          addressPrefix: '10.0.0.0/24'
        }
      }
    ]
  }
  
  resource subnet 'subnets' existing = {
    name: 'sn-vm'
  }
}

resource nic 'Microsoft.Network/networkInterfaces@2024-05-01' = {
  name: 'nic-manual-wait'
  location: location
  properties: {
    ipConfigurations: [
      {
        name: 'ipconfig1'
        properties: {
          subnet: {
            id: vnet::subnet.id
          }
          privateIPAllocationMethod: 'Dynamic'
        }
      }
    ]
  }
}

resource vm 'Microsoft.Compute/virtualMachines@2021-03-01' = {
  name: 'vm-manual-wait'
  location: location
  properties: {
    hardwareProfile: {
      vmSize: 'Standard_B1s'
    }
    storageProfile: {
      imageReference: {
        publisher: 'microsoftcblmariner'
        offer: 'cbl-mariner'
        sku: 'cbl-mariner-2'
        version: 'latest'
      }
      osDisk: {
        createOption: 'FromImage'
        osType: 'Linux'
      }
    }
    osProfile: {
      computerName: 'vm-manual-wait'
      adminUsername: vm_admin_username
      adminPassword: vm_admin_password
      linuxConfiguration: {
        patchSettings: {
          patchMode: 'AutomaticByPlatform'
          assessmentMode: 'AutomaticByPlatform'
        }
      }
    }
    networkProfile: {
      networkInterfaces: [
        {
          id: nic.id
        }
      ]
    }
    diagnosticsProfile: {
      bootDiagnostics: {
        enabled: false
      }
    }
  }
}

resource run_command 'Microsoft.Compute/virtualMachines/runCommands@2024-11-01' = {
  name: 'run-command-manual-wait'
  parent: vm
  location: location
  properties: {
    asyncExecution: false
    source: {
      script: 'sleep 300'
    }
  }
}
