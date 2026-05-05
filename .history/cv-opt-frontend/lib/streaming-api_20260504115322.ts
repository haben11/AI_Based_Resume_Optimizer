/**
 * Streaming API Client
 * 
 * Handles Server-Sent Events (SSE) for real-time resume optimization.
 * Provides progress updates and token streaming.
 * 
 * @author CV Optimizer Team
 * @version 1.0.0
 */

import { useState } from 'react';

export interface ProgressEvent {
  stage: string;
  message: string;
  progress: number;
  data?: Record<string, any>;
}

export interface TokenEvent {
  token: string;
  progress: number;
}

export interface CompleteEvent {
  stage: string;
  message: string;
  progress: number;
  result: {
    optimized_content: string;
    validation: {
      is_valid: boolean;
      quality_score: number;
      issues: Array<{
        severity: string;
        message: string;
        suggestion: string;
      }>;
    };
    hallucination_check?: {
      is_trustworthy: boolean;
      confidence: number;
      hallucination_score: number;
      findings: Array<any>;
    };
  };
}

export interface ErrorEvent {
  stage: string;
  message: string;
  error: string;
}

export interface StreamCallbacks {
  onProgress?: (event: ProgressEvent) => void;
  onToken?: (event: TokenEvent) => void;
  onComplete?: (event: CompleteEvent) => void;
  onError?: (event: ErrorEvent) => void;
}

/**
 * Stream resume optimization with real-time updates.
 * 
 * @param resumeId - Resume UUID
 * @param jobDescription - Job description text
 * @param callbacks - Event callbacks
 * @param accessToken - JWT access token
 * @returns Promise that resolves when stream completes
 */
export async function streamOptimization(
  resumeId: string,
  jobDescription: string,
  callbacks: StreamCallbacks,
  accessToken: string
): Promise<void> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const url = `${apiUrl}/api/v1/optimize/optimize/stream`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      resume_id: resumeId,
      job_description: jobDescription,
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('Response body is not readable');
  }

  const decoder = new TextDecoder();
  let buffer = '';
  let eventType = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        break;
      }

      // Decode chunk
      buffer += decoder.decode(value, { stream: true });

      // Process complete lines
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('event:')) {
          eventType = line.substring(6).trim();
        } else if (line.startsWith('data:')) {
          const dataStr = line.substring(5).trim();
          
          try {
            const data = JSON.parse(dataStr);

            // Dispatch to appropriate callback
            switch (eventType) {
              case 'progress':
                callbacks.onProgress?.(data as ProgressEvent);
                break;
              
              case 'token':
                callbacks.onToken?.(data as TokenEvent);
                break;
              
              case 'complete':
                callbacks.onComplete?.(data as CompleteEvent);
                break;
              
              case 'error':
                callbacks.onError?.(data as ErrorEvent);
                break;
            }
          } catch (e) {
            console.error('Failed to parse SSE data:', e);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * React hook for streaming optimization.
 * 
 * @example
 * ```tsx
 * const { optimize, isStreaming, progress, tokens, result, error } = useStreamingOptimization();
 * 
 * const handleOptimize = async () => {
 *   await optimize(resumeId, jobDescription, accessToken);
 * };
 * ```
 */
export function useStreamingOptimization() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState('');
  const [message, setMessage] = useState('');
  const [tokens, setTokens] = useState('');
  const [result, setResult] = useState<CompleteEvent['result'] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const optimize = async (
    resumeId: string,
    jobDescription: string,
    accessToken: string
  ) => {
    setIsStreaming(true);
    setProgress(0);
    setStage('');
    setMessage('');
    setTokens('');
    setResult(null);
    setError(null);

    try {
      await streamOptimization(
        resumeId,
        jobDescription,
        {
          onProgress: (event) => {
            setProgress(event.progress);
            setStage(event.stage);
            setMessage(event.message);
          },
          onToken: (event) => {
            setTokens((prev) => prev + event.token);
            setProgress(event.progress);
          },
          onComplete: (event) => {
            setResult(event.result);
            setProgress(100);
            setIsStreaming(false);
          },
          onError: (event) => {
            setError(event.message);
            setIsStreaming(false);
          },
        },
        accessToken
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
      setIsStreaming(false);
    }
  };

  const reset = () => {
    setIsStreaming(false);
    setProgress(0);
    setStage('');
    setMessage('');
    setTokens('');
    setResult(null);
    setError(null);
  };

  return {
    optimize,
    reset,
    isStreaming,
    progress,
    stage,
    message,
    tokens,
    result,
    error,
  };
}
