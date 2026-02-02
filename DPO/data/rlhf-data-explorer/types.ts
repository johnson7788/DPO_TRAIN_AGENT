export type Role = 'system' | 'user' | 'assistant' | 'tool_call' | 'tool_response';

export interface ToolFunction {
  name: string;
  description: string;
  parameters: any;
}

export interface Tool {
  type: string;
  function: ToolFunction;
}

export interface Message {
  role: Role;
  content: string;
}

export interface Metadata {
  qid: string;
  original_qid: string;
  task_type: string;
  question: string;
  ground_truth: string;
  chosen_model: string;
  models: Record<string, string>;
  created_at: string;
}

export interface DataItem {
  tools: Tool[];
  messages: Message[];
  rejected_messages?: Message[];
  metadata: Metadata;
}

export interface ApiResponse {
  total: number;
  data: DataItem;
}