// Base API URL for backend and AI endpoints
// In local development, defaults to http://localhost:8000
// In production on Render/Vercel, set VITE_API_URL to your deployed backend URL

let raw = (import.meta.env.VITE_API_URL as string | undefined)?.trim().replace(/\/+$/, '') || 'http://localhost:8000';

// If a domain is passed without protocol (e.g. "my-app.onrender.com"), automatically prepend https://
if (raw && !raw.startsWith('http://') && !raw.startsWith('https://')) {
    raw = `https://${raw}`;
}

export const API_BASE_URL: string = raw;
