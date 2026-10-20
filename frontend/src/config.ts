// Base API URL for AI engine & backend
// In local development, defaults to http://localhost:8001 (or 8000)
// When your AI is hosted on Render, set VITE_AI_API_URL in frontend/.env to your Render URL

let raw = (
  import.meta.env.VITE_AI_API_URL as string | undefined ||
  import.meta.env.VITE_API_URL as string | undefined
)?.trim().replace(/\/+$/, '') || 'http://localhost:8001';

// If domain is passed without protocol (e.g. "my-ai-copilot.onrender.com"), automatically prepend https://
if (raw && !raw.startsWith('http://') && !raw.startsWith('https://')) {
    raw = `https://${raw}`;
}

export const API_BASE_URL: string = raw;
