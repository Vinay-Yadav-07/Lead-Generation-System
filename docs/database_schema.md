CREATE TABLE leads (
    id INTEGER PRIMARY KEY,
    full_name TEXT,
    job_title TEXT,
    company_name TEXT,
    company_website TEXT,
    industry TEXT,
    employee_count INTEGER,
    founding_year INTEGER,
    linkedin_url TEXT,
    email TEXT,
    email_status TEXT,
    phone TEXT,
    phone_status TEXT,
    role_verified BOOLEAN,
    confidence_score INTEGER,
    confidence_level TEXT,
    source TEXT,
    status TEXT,
    created_at TIMESTAMP
);

CREATE TABLE outreach_logs (
    id INTEGER PRIMARY KEY,
    lead_id INTEGER,
    channel TEXT,
    subject TEXT,
    body TEXT,
    status TEXT,
    provider_message TEXT,
    created_at TIMESTAMP
);
