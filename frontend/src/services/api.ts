export type Sentiment = 'Positive' | 'Negative'

export interface PredictionResponse {
  sentiment: Sentiment
  confidence: number | null
  model: string
  cleaned_text?: string | null
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function predictSentiment(text: string): Promise<PredictionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })

  if (!response.ok) {
    let message = 'The sentiment model is unavailable right now.'
    try {
      const payload = await response.json()
      if (typeof payload.detail === 'string') message = payload.detail
    } catch {
      // Keep the user-facing fallback message.
    }
    throw new Error(message)
  }

  return response.json() as Promise<PredictionResponse>
}
