import { useState } from 'react';
import { getToken, refreshAccessToken as _refreshToken } from '@/lib/api';

// Re-export the internal refresh helper so streaming can use it
async function refreshAccessToken(): Promise<string | null> {
  try {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/refresh`,
      { method: 'POST', credentials: 'include' }
    );
    if (!res.ok) return null;
    const data = await res.json();
    // Update the shared token store
    const { setToken } = await import('@/lib/api');
    setToken(data.access_token);
    return data.access_token;
  } catch {
    return null;
  }
}

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


export async function streamOptimization(
  resumeId: string,
  jobDescription: string,
  callbacks: StreamCallbacks,
  accessToken: string
): Promise<void> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const url = `${apiUrl}/api/v1/optimize/optimize/stream`;

  const doStream = async (token: string): Promise<boolean> => {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        resume_id: resumeId,
        job_description: jobDescription,
      }),
    });

    // Token expired on the streaming request — refresh and signal retry
    if (response.status === 401) {
      let detail = '';
      try { detail = (await response.clone().json())?.detail ?? ''; } catch {}
      if (detail === 'token_expired') return false; // caller will retry
      throw new Error(`Authentication failed: ${detail}`);
    }

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('Response body is not readable');

    const decoder = new TextDecoder();
    let buffer = '';
    let eventType = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            eventType = line.substring(6).trim();
          } else if (line.startsWith('data:')) {
            const dataStr = line.substring(5).trim();
            try {
              const data = JSON.parse(dataStr);
              switch (eventType) {
                case 'progress': callbacks.onProgress?.(data as ProgressEvent); break;
                case 'token':    callbacks.onToken?.(data as TokenEvent); break;
                case 'complete': callbacks.onComplete?.(data as CompleteEvent); break;
                case 'error':    callbacks.onError?.(data as ErrorEvent); break;
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
    return true; // success
  };

  // First attempt
  const succeeded = await doStream(accessToken);

  if (!succeeded) {
    // Token expired mid-stream — refresh and retry once
    const newToken = await refreshAccessToken();
    if (!newToken) {
      const { removeToken } = await import('@/lib/api');
      removeToken();
      if (typeof window !== 'undefined') window.location.href = '/login';
      throw new Error('Session expired. Please log in again.');
    }
    await doStream(newToken);
  }
}

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

    // Always use the latest token from the store (may have been refreshed)
    const { getToken } = await import('@/lib/api');
    const currentToken = getToken() || accessToken;

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
        currentToken
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
