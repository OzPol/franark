targetScope = 'resourceGroup'

@minLength(3)
@maxLength(50)
param appName string
@minLength(36)
@maxLength(36)
param tenantId string
@minLength(36)
@maxLength(36)
param clientId string
@minLength(1)
param containerImage string
@minLength(1)
param authSecretUri string
param location string = resourceGroup().location
@allowed(['B1', 'S1'])
param planSku string = 'B1'
param databaseUrl string = ''
@allowed(['demo', 'openai'])
param modelRuntime string = 'demo'
param modelId string = ''
param openAiKeySecretUri string = ''

resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: '${appName}-plan'
  location: location
  kind: 'linux'
  sku: { name: planSku, capacity: 1 }
  properties: { reserved: true }
}

resource app 'Microsoft.Web/sites@2023-12-01' = {
  name: appName
  location: location
  kind: 'app,linux,container'
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'DOCKER|${containerImage}'
      acrUseManagedIdentityCreds: true
      alwaysOn: true
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      http20Enabled: true
      healthCheckPath: '/health'
    }
  }
}

resource appSettings 'Microsoft.Web/sites/config@2023-12-01' = {
  parent: app
  name: 'appsettings'
  properties: {
    WEBSITES_PORT: '8765'
    WEBSITES_ENABLE_APP_SERVICE_STORAGE: 'true'
    FRANARK_DATA_DIR: '/home/franark-data'
    FRANARK_AUTH_MODE: 'entra'
    FRANARK_TENANT_ID: tenantId
    FRANARK_CLIENT_ID: clientId
    FRANARK_PUBLIC_ORIGIN: 'https://${app.properties.defaultHostName}'
    FRANARK_ALLOWED_HOSTS: '${app.properties.defaultHostName},127.0.0.1,localhost'
    FRANARK_DATABASE_URL: databaseUrl
    FRANARK_SQL_AUTH: 'managed_identity'
    FRANARK_RUNTIME: modelRuntime
    FRANARK_MODEL: modelId
    FRANARK_MAX_CALLS: '10'
    FRANARK_MAX_TOOL_ROUNDS: '2'
    FRANARK_MAX_OUTPUT_TOKENS: '1400'
    MICROSOFT_PROVIDER_AUTHENTICATION_SECRET: '@Microsoft.KeyVault(SecretUri=${authSecretUri})'
    OPENAI_API_KEY: empty(openAiKeySecretUri) ? '' : '@Microsoft.KeyVault(SecretUri=${openAiKeySecretUri})'
  }
}

resource authentication 'Microsoft.Web/sites/config@2022-09-01' = {
  parent: app
  name: 'authsettingsV2'
  properties: {
    platform: { enabled: true, runtimeVersion: '~1' }
    globalValidation: {
      requireAuthentication: true
      unauthenticatedClientAction: 'RedirectToLoginPage'
      redirectToProvider: 'azureactivedirectory'
      excludedPaths: ['/health']
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          clientId: clientId
          clientSecretSettingName: 'MICROSOFT_PROVIDER_AUTHENTICATION_SECRET'
          openIdIssuer: '${environment().authentication.loginEndpoint}${tenantId}/v2.0'
        }
        validation: { allowedAudiences: [clientId] }
      }
    }
    login: { tokenStore: { enabled: true } }
    httpSettings: { requireHttps: true }
  }
  dependsOn: [appSettings]
}

resource scmPolicy 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2023-12-01' = {
  parent: app
  name: 'scm'
  properties: { allow: false }
}
resource ftpPolicy 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2023-12-01' = {
  parent: app
  name: 'ftp'
  properties: { allow: false }
}

output appUrl string = 'https://${app.properties.defaultHostName}/portal'
output identityPrincipalId string = app.identity.principalId
output redirectUri string = 'https://${app.properties.defaultHostName}/.auth/login/aad/callback'
