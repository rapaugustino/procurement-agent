import { ActivityTypes } from "@microsoft/agents-activity";
import { AgentApplication, MemoryStorage, TurnContext } from "@microsoft/agents-hosting";
import config from "./config";

// Create the main application object
const storage = new MemoryStorage();
const agentApp = new AgentApplication({
  storage,
  ai: {
    planner: {
      name: "AssistantsPlanner",
      options: {
        apiKey: config.openAIKey,
        apiVersion: config.openAIApiVersion,
        endpoint: config.openAIEndpoint,
        model: config.openAIModelName,
      },
    },
  },
});

// Define application turn state
export interface ApplicationTurnState {
  conversation: {
    lastUserMessage?: string;
  };
}

// Handle incoming messages
agentApp.activity(ActivityTypes.Message, async (context: TurnContext) => {
  const userMessage = context.activity.text;
  const userName = context.activity.from?.name || 'Teams User';
  const conversationId = context.activity.conversation?.id || 'unknown';
  
  console.log('💬 Processing message:', userMessage);
  
  try {
    // Simple request to backend RAG agent
    const requestBody = {
      question: userMessage,
      conversation_id: conversationId,
      user_name: userName
    };
    
    console.log('📡 Sending to backend:', requestBody);
    
    // Call backend RAG agent with streaming
    const response = await fetch(`${config.backendUrl}/agents/query/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }
    
    // Handle streaming response
    await handleStreamingResponse(context, response);
    
  } catch (error) {
    console.error('❌ Error:', error);
    await context.sendActivity(
      `❌ I'm having trouble connecting to my knowledge base right now.\n\n` +
      `Please try again in a moment, or contact Richard Pallangyo directly at rpallang@uw.edu for immediate assistance.`
    );
  }
});

// Handle streaming response from backend
async function handleStreamingResponse(context: TurnContext, response: Response) {
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  
  if (!reader) {
    throw new Error('No response body available');
  }
  
  let buffer = '';
  let fullResponse = '';
  
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.substring(6));
            
            // Handle different event types
            if (data.type === 'chunk' && data.content) {
              fullResponse += data.content;
            } else if (data.type === 'completed' && data.response) {
              fullResponse = data.response;
              break;
            }
          } catch (parseError) {
            console.log('⚠️ Could not parse SSE data:', line);
          }
        }
      }
    }
    
    // Send the complete response
    if (fullResponse.trim()) {
      await context.sendActivity(fullResponse);
    } else {
      await context.sendActivity('❌ I received an empty response. Please try rephrasing your question.');
    }
    
  } catch (error) {
    console.error('❌ Streaming error:', error);
    await context.sendActivity('❌ There was an error processing the response. Please try again.');
  } finally {
    reader.releaseLock();
  }
}

export default agentApp;
