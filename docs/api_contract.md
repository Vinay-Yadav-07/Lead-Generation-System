GET /
GET /api/health
GET /integrations/status
GET /leads
GET /lead/{id}
PATCH /lead/{id}/status
GET /lead/{id}/cold-email
POST /lead/{id}/send-email

POST /add-lead
POST /import-inc42
POST /discover-companies-db?replace=true
POST /discover-websites
POST /score-companies
POST /generate-leads-from-companies
POST /verify/{id}
POST /verify-all
POST /campaign/send-approved

GET /icp
PUT /icp
GET /companies-db
GET /top-companies
GET /export/csv
GET /export/json
GET /stats
GET /outreach-logs
