import 'reflect-metadata'
import { ActionProvider, CreateAction } from "@coinbase/agentkit";
import { z } from "zod";

// Define the schema for tweet evaluation
const tweetEvaluationSchema = z.object({
  tweet: z.string(),
  dependencyGraph: z.string(),
});

export class EvaluateTweetsActionProvider extends ActionProvider {
  constructor() {
    super("evaluate-tweets-action-provider", []);
  }

  @CreateAction({
    name: "evaluate-tweet",
    description: "Use AI to analyze if a tweet indicates a security threat.",
    schema: tweetEvaluationSchema,
  })
  async evaluateTweet(
    args: z.infer<typeof tweetEvaluationSchema>
  ): Promise<string> {
    const { tweet, dependencyGraph } = args;
    const analysis = `
    # Threat Analysis for Tweet

    ## Tweet Content
    "${tweet}"


    ## Dependency Graph Overview
    "${dependencyGraph}"
    `;

    return analysis;
  }

  supportsNetwork = () => true;
}

export const evaluateTweetsActionProvider = () =>
  new EvaluateTweetsActionProvider();
