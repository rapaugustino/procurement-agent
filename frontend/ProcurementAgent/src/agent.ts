import { ActivityTypes } from "@microsoft/agents-activity";
import { AgentApplication, MemoryStorage, TurnContext } from "@microsoft/agents-hosting";
import { AzureOpenAI, OpenAI } from "openai";
import config from "./config";

const client = new AzureOpenAI({
  apiVersion: "2024-12-01-preview",
  apiKey: config.azureOpenAIKey,
  endpoint: config.azureOpenAIEndpoint,
  deployment: config.azureOpenAIDeploymentName,
});
const systemPrompt = "You are a helpful procurement assistant for the University of Washington. Help users with procurement-related questions, policies, and procedures. Be professional and informative.";

// Define storage and application
const storage = new MemoryStorage();
export const agentApp = new AgentApplication({
  storage,
});

agentApp.conversationUpdate("membersAdded", async (context: TurnContext) => {
  await context.sendActivity(
    `🎯 **Welcome to the UW Procurement Agent!**\n\n` +
    `I'm here to help you with University of Washington procurement questions. ` +
    `Ask me about policies, procedures, vendor information, or approval requirements!`
  );
});

// Listen for ANY message to be received. MUST BE AFTER ANY OTHER MESSAGE HANDLERS
agentApp.activity(ActivityTypes.Message, async (context: TurnContext) => {
  const userMessage = context.activity.text;
  
  // Check if we're waiting for email consent by looking at recent bot messages
  // This is more reliable than trying to persist state between messages in Teams
  const isEmailConsentResponse = (userMessage.toLowerCase().trim() === 'yes' || userMessage.toLowerCase().trim() === 'no') &&
                                 context.activity.text && context.activity.text.length < 10; // Short response
  
  if (isEmailConsentResponse) {
    const response = userMessage.toLowerCase().trim();
    
    if (response === 'yes' || response === 'y') {
      await context.sendActivity('✅ **Proceeding with email drafting...**');
      
      // Get the original request context
      const originalRequest = context.turnState.get('originalRequest') || 'assistance with procurement';
      
      // Prepare backend request for email drafting
      const userId = context.activity.from?.aadObjectId || context.activity.from?.id || 'unknown';
      const userEmail = `${userId}@university.edu`;
      const userName = context.activity.from?.name || 'Teams User';
      const conversationId = context.activity.conversation?.id || `teams-${userId}-${Date.now()}`;
      
      const emailRequest = {
        user_id: userEmail,
        conversation_id: conversationId,
        initial_message: `Please draft an email to Richard Pallangyo regarding: ${originalRequest}`,
        auto_approve: false,
        user_email: userEmail,
        user_name: userName,
        user_tenant_id: config.azureTenantId
      };
      
      try {
        const response = await fetch(`${config.backendUrl}/workflow/execute/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
          },
          body: JSON.stringify(emailRequest)
        });
        
        if (response.ok) {
          await handleBackendStream(context, response);
        } else {
          await context.sendActivity('❌ **Error starting email drafting workflow.** Please try again later.');
        }
      } catch (error) {
        console.error('Error with email drafting request:', error);
        await context.sendActivity('❌ **Error connecting to email drafting service.** Please try again later.');
      }
      return;
    } else if (response === 'no' || response === 'n') {
      await context.sendActivity('❌ **Email drafting cancelled.** Feel free to ask me any other procurement questions!');
      return;
    } else {
      await context.sendActivity('❓ **Please respond with "yes" or "no"** to proceed with email drafting.');
      // Reset the consent flag in conversation state
      conversationState.waitingForEmailConsent = true;
      context.turnState.set('conversationState', conversationState);
      return;
    }
  }
  
  // Try backend first if available (advanced procurement agent)
  if (config.backendUrl) {
    try {
      await context.sendActivity('🔄 Processing with advanced procurement agent...');
      
      // Extract user context from Teams
      const userId = context.activity.from?.aadObjectId || context.activity.from?.id || 'unknown';
      // Get real user email from Teams context (available when user is logged in)
      // Use type assertion to access extended properties that may be available in Teams
      const fromExtended = context.activity.from as any;
      const channelDataExtended = context.activity.channelData as any;
      const userEmail = fromExtended?.email || 
                       fromExtended?.userPrincipalName || 
                       channelDataExtended?.user?.userPrincipalName ||
                       channelDataExtended?.tenant?.userPrincipalName ||
                       `${userId}@university.edu`; // fallback only
      const userName = context.activity.from?.name || 'Teams User';
      const conversationId = context.activity.conversation?.id || `teams-${userId}-${Date.now()}`;
      
      // Store the original request for potential email drafting
      context.turnState.set('originalRequest', userMessage);
      
      // Prepare request for backend
      const backendRequest = {
        user_id: userEmail,
        conversation_id: conversationId,
        initial_message: userMessage,
        auto_approve: false, // Always require approval in Teams
        user_email: userEmail,
        user_name: userName,
        user_tenant_id: config.azureTenantId
      };
      
      // Call backend API
      console.log('🚀 SENDING REQUEST TO BACKEND:', {
        url: `${config.backendUrl}/workflow/execute/stream`,
        request: backendRequest,
        user_message: userMessage
      });
      
      const response = await fetch(`${config.backendUrl}/workflow/execute/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify(backendRequest)
      });
      
      console.log('📥 BACKEND RESPONSE STATUS:', {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries())
      });
      
      if (response.ok) {
        // Handle streaming response from backend
        await handleBackendStream(context, response);
        return; // Success - exit early
      } else {
        await context.sendActivity('❌ **Backend Error**: Unable to connect to procurement agent backend. Please ensure the backend service is running.');
        return;
      }
    } catch (error) {
      await context.sendActivity('❌ **Backend Unavailable**: The procurement agent backend is not accessible. Please contact your administrator.');
      return;
    }
  } else {
    // No backend URL configured
    await context.sendActivity('⚠️ **Configuration Required**: This procurement agent requires backend configuration. Please set BACKEND_URL environment variable.');
    return;
  }
});

// Handle streaming response from backend (optional enhancement)
async function handleBackendStream(context: TurnContext, response: Response) {
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  
  if (!reader) {
    throw new Error('No response body reader available');
  }
  
  let buffer = '';
  let currentEvent = '';
  
  try {
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          // Capture the event type
          currentEvent = line.substring(7).trim();
          console.log('🏷️ SSE EVENT TYPE:', currentEvent);
        } else if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.substring(6));
            // Add the event type to the data
            data.event = currentEvent;
            console.log('📡 SSE DATA PARSED:', {
              raw_line: line,
              parsed_data: data,
              event_type: data.event
            });
            await handleBackendEvent(context, data);
            // Reset event type after processing
            currentEvent = '';
          } catch (e) {
            console.log('❌ SSE PARSE ERROR:', {
              line: line,
              error: e.message
            });
          }
        } else if (line.trim()) {
          console.log('📜 SSE NON-DATA LINE:', line);
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

// Handle individual backend events
async function handleBackendEvent(context: TurnContext, data: any) {
  // Add comprehensive logging
  console.log('🔍 FRONTEND EVENT RECEIVED:', {
    event: data.event,
    tool_name: data.tool_name,
    message: data.message,
    result_length: data.result ? data.result.length : 0,
    result_preview: data.result ? data.result.substring(0, 100) + '...' : 'No result',
    full_data: JSON.stringify(data, null, 2)
  });
  
  switch (data.event || 'unknown') {
    case 'workflow_started':
      // Only show initial processing message
      await context.sendActivity(`🔄 **Processing your request...**`);
      break;
      
    case 'planning':
    case 'plan_created':
    case 'step_started':
    case 'tool_executing':
    case 'dynamic_steps_added':
    case 'approval_granted':
    case 'waiting_approval':
      // Hide internal workflow steps - users don't need to see these
      console.log(`ℹ️ Internal workflow step: ${data.event} - ${data.message}`);
      break;
      
    case 'step_completed':
      // Get the step name from various possible properties
      const stepName = data.step_name || data.tool_name || data.name || 'Step';
      
      if (stepName === 'procurement_rag_agent_tool') {
        await context.sendActivity(`✅ **Procurement Analysis**\n\n${data.result}`);
        
        // Check if RAG agent offered email assistance and ask for user consent
        if (data.result && (
          data.result.toLowerCase().includes('would you like assistance drafting an email') ||
          data.result.toLowerCase().includes('i can help you draft an email')
        )) {
          await context.sendActivity(`\n❓ **Would you like me to draft an email for you?**\n\nPlease respond with:\n• **"yes"** to draft an email\n• **"no"** to skip email drafting`);
          // No need to store state - we'll detect yes/no responses by their content
          return; // Stop processing here until user responds
        }
      } else if (stepName === 'draft_communication_tool') {
        await context.sendActivity(`📧 **Email Draft**\n\n${data.result}`);
      } else if (stepName === 'send_communication_tool') {
        await context.sendActivity(`✅ **Email Sent**\n\n${data.result}`);
      } else {
        // Only show step completion for non-RAG steps to avoid duplication
        if (stepName !== 'procurement_rag_agent_tool') {
          console.log(`ℹ️ Step completed: ${stepName}`);
        }
      }
      break;
      
    case 'approval_required':
      await context.sendActivity(
        `⏳ **Approval Required**\n\n` +
        `Please review the email draft above and respond with:\n` +
        `• **"approve"** to send the email\n` +
        `• **"reject"** to cancel sending`
      );
      break;
      
    case 'workflow_completed':
      // Only show completion message if it's different from the RAG result
      // or if no RAG step was completed (to avoid duplication)
      const completionMessage = data.final_result || data.message;
      if (completionMessage && completionMessage.length < 200) {
        // Short completion messages are likely status updates, show them
        await context.sendActivity(`🎉 **Complete!** ${completionMessage}`);
      } else {
        // Long completion messages are likely duplicates of RAG content, just show status
        await context.sendActivity(`🎉 **Request completed successfully!**`);
      }
      break;
      
    case 'error':
      await context.sendActivity(`❌ **Error**: ${data.message}`);
      break;
      
    default:
      // Handle any other events with generic message
      if (data.message) {
        await context.sendActivity(`ℹ️ ${data.message}`);
      }
      break;
  }
}
