const config = {
  // OpenAI configuration (required for basic functionality)
  azureOpenAIKey: process.env.AZURE_OPENAI_API_KEY,
  azureOpenAIEndpoint: process.env.AZURE_OPENAI_ENDPOINT,
  azureOpenAIDeploymentName: process.env.AZURE_OPENAI_DEPLOYMENT_NAME,
  
  // Optional backend integration (for advanced procurement agent features)
  backendUrl: process.env.BACKEND_URL, // Leave undefined to use OpenAI only
  
  // Optional Azure AD configuration (for Microsoft Graph API integration)
  azureTenantId: process.env.AZURE_TENANT_ID,
  azureClientId: process.env.AZURE_CLIENT_ID,
};

export default config;
