import { ActivityTypes } from "@microsoft/agents-activity";
import { AgentApplication, MemoryStorage, TurnContext } from "@microsoft/agents-hosting";
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
  
  // Store the user's message for potential email context (unless it's a consent response)
  const isLikelyConsentResponse = userMessage && userMessage.toLowerCase().trim().length < 15 && 
    (userMessage.toLowerCase().includes('yes') || userMessage.toLowerCase().includes('no') || 
     userMessage.toLowerCase().includes('never mind') || userMessage.toLowerCase().includes('cancel'));
  
  if (!isLikelyConsentResponse) {
    context.turnState.set('lastUserMessage', userMessage);
  }
  
  // Check if we're waiting for email consent OR email approval
  // This is more reliable than trying to persist state between messages in Teams
  const isEmailConsentResponse = (userMessage.toLowerCase().trim() === 'yes' || userMessage.toLowerCase().trim() === 'no') &&
                                 context.activity.text && context.activity.text.length < 10; // Short response
  
  // Check if this is an email approval/rejection response
  const isEmailApprovalResponse = userMessage && (
    userMessage.toLowerCase().trim() === 'approve' ||
    userMessage.toLowerCase().trim() === 'reject' ||
    userMessage.toLowerCase().trim() === 'cancel' ||
    (userMessage.toLowerCase().includes('edit') && userMessage.length < 100)
  );
  
  // Handle email approval responses first
  if (isEmailApprovalResponse) {
    const response = userMessage.toLowerCase().trim();
    
    if (response === 'approve') {
      await context.sendActivity('✅ **Email approved!** Sending now...');
      
      // Get the stored email draft and send it via backend
      const storedEmailDraft = context.turnState.get('pendingEmailDraft');
      if (storedEmailDraft && config.backendUrl) {
        try {
          // Send approval to backend
          const approvalResponse = await fetch(`${config.backendUrl}/workflow/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              workflow_id: storedEmailDraft.workflowId,
              action: 'approve'
            })
          });
          
          if (approvalResponse.ok) {
            await context.sendActivity('🎉 **Email sent successfully!** Richard Pallangyo will receive your message.');
          } else {
            await context.sendActivity('❌ **Error sending email.** Please try again or contact Richard directly at rapaugustino@gmail.com.');
          }
        } catch (error) {
          await context.sendActivity('❌ **Error sending email.** Please try again or contact Richard directly at rapaugustino@gmail.com.');
        }
      } else {
        await context.sendActivity('🎉 **Email approved!** (Simulated - missing backend connection)');
      }
      return;
    } else if (response === 'reject' || response === 'cancel') {
      await context.sendActivity('😊 **No worries!** Email cancelled. Feel free to ask any other procurement questions - I\'m here to help! 🤝');
      return;
    } else if (response.includes('edit')) {
      await context.sendActivity('✏️ **Email editing requested.** Please provide your specific changes and I\'ll update the draft for you.');
      return;
    }
  }
  
  if (isEmailConsentResponse) {
    const response = userMessage.toLowerCase().trim();
    
    if (response === 'yes' || response === 'y') {
      await context.sendActivity('✅ **Proceeding with email drafting...**');
      
      // Get the original request context - we need to find the user's actual question
      // that triggered the email assistance offer, not the "yes" response
      let originalRequest = 'assistance with procurement';
      
      // Store the current user message ("yes") and look for the previous question
      // The user's actual question should be stored when we first offer email assistance
      const storedOriginalQuestion = context.turnState.get('pendingEmailQuestion');
      if (storedOriginalQuestion) {
        originalRequest = storedOriginalQuestion;
      }
      
      // Prepare backend request for email drafting
      const userId = context.activity.from?.aadObjectId || context.activity.from?.id || 'unknown';
      const userEmail = `${userId}@university.edu`;
      const userName = context.activity.from?.name || 'Teams User';
      const conversationId = context.activity.conversation?.id || `teams-${userId}-${Date.now()}`;
      
      const emailRequest = {
        user_id: userEmail,
        conversation_id: conversationId,
        initial_message: `Draft an email to Richard Pallangyo requesting specific information. The user asked: "${originalRequest}". The RAG agent found general procurement information but could not find the specific details the user needs. Please draft a professional email that references the user's specific question and asks Richard for the missing information.`,
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
    } else if (response === 'no' || response === 'n' || 
               response.includes('never mind') || response.includes('nevermind') ||
               response.includes('forget') || response.includes('cancel') ||
               response.includes('don\'t need') || response.includes('all set')) {
      await context.sendActivity('😊 **No worries!** Feel free to ask any other procurement questions - I\'m here to help! 🤝');
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
      // Clean start - no verbose messages with M365 Agents SDK
      break;
      
    case 'planning':
    case 'plan_created':
    case 'step_started':
    case 'tool_executing':
    case 'dynamic_steps_added':
    case 'approval_granted':
    case 'waiting_approval':
      // Hide all internal workflow steps - users don't need to see these
      // Clean processing with M365 Agents SDK
      console.log(`ℹ️ Internal workflow step: ${data.event} - ${data.message}`);
      break;
      
    case 'step_completed':
      // Get the step name from various possible properties
      const stepName = data.step_name || data.tool_name || data.name || 'Step';
      
      if (stepName === 'procurement_rag_agent_tool') {
        // Format the response with better structure and visual appeal
        const formattedResponse = `## 🎯 **Procurement Information**\n\n${data.result}`;
        await context.sendActivity(formattedResponse);
        
        // Check if RAG agent offered email assistance and ask for user consent
        if (data.result && (
          data.result.toLowerCase().includes('would you like assistance drafting an email') ||
          data.result.toLowerCase().includes('i can help you draft an email')
        )) {
          // Store the original user question for email context
          const originalUserQuestion = context.turnState.get('lastUserMessage') || context.activity.text || 'assistance with procurement';
          context.turnState.set('pendingEmailQuestion', originalUserQuestion);
          
          const consentMessage = `\n---\n\n❓ **Need Additional Help?**\n\nWould you like me to draft an email for personalized assistance?\n\n✅ **"yes"** - Draft an email\n❌ **"no"** - I'm all set`;
          await context.sendActivity(consentMessage);
          // No need to store state - we'll detect yes/no responses by their content
          return; // Stop processing here until user responds
        }
      } else if (stepName === 'draft_communication_tool') {
        const emailDraftFormatted = `## 📧 **Email Draft**\n\n${data.result}\n\n---\n\n💬 **Review Your Email**\n\nPlease review the draft above. You can:\n\n✅ **"approve"** - Send as-is\n✏️ **"edit [your changes]"** - Request modifications\n❌ **"cancel"** - Don't send`;
        await context.sendActivity(emailDraftFormatted);
      } else if (stepName === 'send_communication_tool') {
        const emailSentFormatted = `## ✅ **Email Status**\n\n${data.result}`;
        await context.sendActivity(emailSentFormatted);
      } else {
        // Only show step completion for non-RAG steps to avoid duplication
        if (stepName !== 'procurement_rag_agent_tool') {
          console.log(`ℹ️ Step completed: ${stepName}`);
        }
      }
      break;
      
    case 'approval_required':
      // Don't show duplicate approval prompt - the email draft already includes review options
      console.log('📧 Email draft ready for user review');
      break;
      
    case 'workflow_completed':
      // Don't send completion messages - they're unnecessary and create noise
      // The final result/action (email sent, etc.) is sufficient feedback
      console.log(`✅ Workflow completed: ${data.final_result || data.message}`);
      break;
      
    case 'error':
      // Check if this is an email cancellation/rejection (more human response)
      if (data.message && (
        data.message.includes('rejected by user') ||
        data.message.includes('workflow stopped') ||
        data.message.includes('Step rejected')
      )) {
        await context.sendActivity(`😊 **No worries!** Email cancelled.\n\nFeel free to ask any other procurement questions - I'm here to help! 🤝`);
      } else {
        await context.sendActivity(`❌ **Error**: ${data.message}`);
      }
      break;
      
    default:
      // Handle any other events with generic message
      if (data.message) {
        await context.sendActivity(`ℹ️ ${data.message}`);
      }
      break;
  }
}
