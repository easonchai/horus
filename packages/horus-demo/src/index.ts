import { createActor } from 'xstate';
import { horusMachine } from './state/machine';
import { services } from './state/services';
import { TwitterPoller } from './mock/tweet-generator';

console.log("Starting Horus DeFi Protection System...");

// Create the main Horus actor
const horusActor = createActor(horusMachine, {
  services
});

// Subscribe to state changes
horusActor.subscribe(state => {
  console.log(`[${new Date().toISOString()}] State: ${state.value}`);

  // Log context for specific states
  if (state.value === 'evaluating') {
    console.log(`Evaluating signal: "${state.context.currentSignal?.content}"`);
  } else if (state.value === 'processing') {
    console.log(`Processing threat: ${state.context.detectedThreat?.description}`);
  } else if (state.value === 'composing') {
    console.log(`Composing actions for: ${state.context.detectedThreat?.affectedProtocols.join(', ')}`);
  } else if (state.value === 'executing') {
    console.log(`Executing ${state.context.actionPlan.length} actions`);
  } else if (state.value === 'completed') {
    console.log(`Completed ${state.context.executionResults.length} actions`);
  } else if (state.value === 'failed') {
    console.log(`Error: ${state.context.error?.message}`);
  }
});

// Start the Horus actor
horusActor.start();

// Create Twitter poller
const twitterPoller = new TwitterPoller((signal) => {
  console.log(`Received signal from Twitter: "${signal.content}"`);

  // Send the signal to the Horus actor
  horusActor.send({
    type: 'SIGNAL_RECEIVED',
    signal
  });
});

// Start polling for tweets
twitterPoller.start(5000); // Poll every 5 seconds

// Handle application shutdown
process.on('SIGINT', () => {
  console.log('Shutting down Horus...');
  twitterPoller.stop();
  process.exit(0);
});

console.log("Horus is now monitoring for security threats...");
