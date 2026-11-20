# Deploy the synthetic pilot in SFC's tenant

Target: a dedicated SFC resource group and single-tenant Entra application.
This runbook prepares a synthetic pilot; it does not establish production approval.

## Identity and image prerequisites

Use a dedicated Entra application with organizational accounts only, v2 tokens,
ID-token issuance enabled and app assignment required. The app-role definitions
are in `infra/app-roles.json`. Assign the pilot administrator and reviewer through
the SFC enterprise application. The backend requires the exact tenant, audience,
issuer, valid RSA signature, lifetime and an allowed role. Email suffixes and
unsigned `X-MS-CLIENT-PRINCIPAL` headers do not grant access.

Create the authentication client secret in the approved Key Vault. Keep secret
bytes out of commands, files and Git; deployment parameters accept its URI.
The web-app identity needs a scoped secret-reader grant. The approved SFC
registry/image must grant that identity `AcrPull` before container startup succeeds.

Build the Azure image, which includes the SQL driver and identity dependencies:

```bash
docker build --target azure -t REGISTRY/franark:PILOT_TAG .
```

Publish through SFC's approved registry workflow. The Azure entrypoint prepares
the persistent `/home/franark-data` directory, then runs the app as an unprivileged
user. One process/instance is configured for this pilot.

## Validate and deploy

`infra/Deploy-Sfc.ps1` checks the active subscription's tenant before proceeding.
Without `-Apply`, it runs Azure deployment **what-if**. It requires the tenant,
subscription, resource group, app name, client ID, image and authentication-secret
URI. Use SFC's collected values; no real account identifiers are embedded in source.

The template enables HTTPS-only App Service, managed identity, token storage,
mandatory Entra sign-in, backend JWT verification and disabled basic publishing.
Only `/health` is excluded from the platform sign-in gate. Application APIs still
require valid signed tokens and app roles. The deployment outputs the exact site
and callback URL; add that callback to the dedicated registration.

Account-scoped registry, Key Vault and SQL permissions must be granted separately.
The template does not grant broad subscription/directory access or silently change
an existing app registration. Incomplete authentication fails closed.

## Database

An empty `FRANARK_DATABASE_URL` uses SQLite on the configured persistent directory.
For the approved Azure SQL database, configure the non-secret server/database URL:

```text
mssql+pyodbc://@SERVER.database.windows.net/DATABASE?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no
```

`FRANARK_SQL_AUTH=managed_identity` obtains an Azure SQL token through
`DefaultAzureCredential`. A configured Azure SQL failure does not fall back to
SQLite. The driver and identity hook are included in the Azure image.

Schema creation/migration needs an appropriately authorized bootstrap identity.
After bootstrap, grant the application only the required schema/record operations
and metadata visibility. Keep the Franark database separate from vendor databases.
The additive pilot migration preserves existing local run history and assigns
legacy local records to the local pilot identity; it does not assign them to SFC
employees automatically. Start a clean SFC database for the tenant test.

## Model and remaining connectors

The model runtime remains `demo` unless explicitly selected. To enable OpenAI,
configure `modelRuntime=openai`, `modelId` and a Key Vault reference for the API
key, then grant the app access to that reference. Missing model configuration
prevents model calls. Method and API request limits remain enforced.

Microsoft Graph, signature providers, SharePoint/Blob attachments and vendor
import mappings remain unconnected. Generic files and unsent email drafts are
available for the synthetic pilot. No automatic email or vendor write occurs.

## Tenant acceptance test

Verify administrator and reviewer sign-in, denial for unassigned/foreign-tenant
identities, ownership/assignment isolation, blocked unapproved exports, correction
history, actual SQL persistence, actual model usage and the physical tablet flow.
Record these results separately from local/fake-client checks. No live SFC tenant
or database test has been performed in this development environment.

## Technical sources

- [App Service token headers](https://learn.microsoft.com/en-us/azure/app-service/configure-authentication-oauth-tokens)
- [App Service authentication configuration](https://learn.microsoft.com/en-us/azure/templates/microsoft.web/sites/config-authsettingsv2)
- [SQLAlchemy Azure SQL access tokens](https://docs.sqlalchemy.org/en/20/dialects/mssql.html#connecting-to-databases-with-access-tokens)
- [PyJWT validation](https://pyjwt.readthedocs.io/en/stable/usage.html)
- [Microsoft SQL driver installation](https://learn.microsoft.com/en-us/sql/connect/odbc/linux/installing-the-microsoft-odbc-driver-for-sql-server-on-linux)
