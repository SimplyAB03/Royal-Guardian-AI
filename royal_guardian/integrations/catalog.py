from royal_guardian.integrations.base import IntegrationDescriptor, IntegrationStatus

INTEGRATIONS = [
    IntegrationDescriptor("anthropic", "Anthropic Claude", IntegrationStatus.BLOCKED_BY_CREDENTIALS, ("ANTHROPIC_API_KEY",)),
    IntegrationDescriptor("openai", "OpenAI", IntegrationStatus.BLOCKED_BY_CREDENTIALS, ("OPENAI_API_KEY",)),
    IntegrationDescriptor("gemini", "Google Gemini", IntegrationStatus.BLOCKED_BY_CREDENTIALS, ("GOOGLE_AI_API_KEY",)),
    IntegrationDescriptor("google", "Google Workspace", IntegrationStatus.BLOCKED_BY_EXTERNAL_SETUP, ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")),
    IntegrationDescriptor("microsoft", "Microsoft 365 / Graph", IntegrationStatus.BLOCKED_BY_EXTERNAL_SETUP, ("MICROSOFT_CLIENT_ID", "MICROSOFT_CLIENT_SECRET")),
    IntegrationDescriptor("slack", "Slack", IntegrationStatus.BLOCKED_BY_EXTERNAL_SETUP, ("SLACK_CLIENT_ID", "SLACK_CLIENT_SECRET")),
    IntegrationDescriptor("github", "GitHub", IntegrationStatus.BLOCKED_BY_EXTERNAL_SETUP, ("GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET")),
    IntegrationDescriptor("stripe", "Stripe Billing", IntegrationStatus.BLOCKED_BY_CREDENTIALS, ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET")),
    IntegrationDescriptor("twilio", "Twilio Voice/SMS", IntegrationStatus.BLOCKED_BY_CREDENTIALS, ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN")),
    IntegrationDescriptor("servicenow", "ServiceNow", IntegrationStatus.PLANNED),
    IntegrationDescriptor("jira", "Jira Service Management", IntegrationStatus.PLANNED),
    IntegrationDescriptor("zendesk", "Zendesk", IntegrationStatus.PLANNED),
    IntegrationDescriptor("freshservice", "Freshservice", IntegrationStatus.PLANNED),
    IntegrationDescriptor("hubspot", "HubSpot", IntegrationStatus.PLANNED),
    IntegrationDescriptor("salesforce", "Salesforce", IntegrationStatus.PLANNED),
    IntegrationDescriptor("notion", "Notion", IntegrationStatus.PLANNED),
    IntegrationDescriptor("dropbox", "Dropbox", IntegrationStatus.PLANNED),
]
