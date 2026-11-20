[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][guid]$TenantId,
    [Parameter(Mandatory=$true)][guid]$SubscriptionId,
    [Parameter(Mandatory=$true)][string]$ResourceGroup,
    [Parameter(Mandatory=$true)][string]$AppName,
    [Parameter(Mandatory=$true)][guid]$ClientId,
    [Parameter(Mandatory=$true)][string]$ContainerImage,
    [Parameter(Mandatory=$true)][uri]$AuthSecretUri,
    [string]$DatabaseUrl = '',
    [ValidateSet('demo','openai')][string]$ModelRuntime = 'demo',
    [string]$ModelId = '',
    [string]$OpenAiKeySecretUri = '',
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
if (-not (Get-Command az -ErrorAction SilentlyContinue)) { throw 'Azure CLI is required.' }
& az account set --subscription ($SubscriptionId.ToString())
if ($LASTEXITCODE -ne 0) { throw 'Azure subscription selection failed.' }
$activeTenant = & az account show --query tenantId --output tsv
if ($LASTEXITCODE -ne 0 -or $activeTenant.Trim() -ne $TenantId.ToString()) { throw 'The active Azure tenant does not match the SFC deployment target.' }
if ($AuthSecretUri.Scheme -ne 'https' -or -not $AuthSecretUri.Host.EndsWith('.vault.azure.net')) { throw 'The authentication secret must be an Azure Key Vault secret URI.' }
$parameters = @{
    appName=@{value=$AppName}; tenantId=@{value=$TenantId.ToString()}; clientId=@{value=$ClientId.ToString()}
    containerImage=@{value=$ContainerImage}; authSecretUri=@{value=$AuthSecretUri.AbsoluteUri}
    databaseUrl=@{value=$DatabaseUrl}; modelRuntime=@{value=$ModelRuntime}
    modelId=@{value=$ModelId}; openAiKeySecretUri=@{value=$OpenAiKeySecretUri}
}
$parameterFile = [IO.Path]::GetTempFileName()
try {
    @{parameters=$parameters} | ConvertTo-Json -Depth 8 | Set-Content -Path $parameterFile -Encoding UTF8
    $operation = if ($Apply) { 'create' } else { 'what-if' }
    & az deployment group $operation --resource-group $ResourceGroup --template-file (Join-Path $PSScriptRoot 'sfc-pilot.bicep') --parameters "@$parameterFile"
    if ($LASTEXITCODE -ne 0) { throw 'Azure deployment validation or creation failed.' }
} finally { Remove-Item $parameterFile -Force -ErrorAction SilentlyContinue }
