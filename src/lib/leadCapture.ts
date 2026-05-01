export interface LeadInput {
  name: string;
  email: string;
  source: string;
}

export type LeadCaptureResult =
  | { ok: true }
  | {
      ok: false;
      reason: 'no-url' | 'network' | 'http-error' | 'timeout';
      status?: number;
    };

const WEBHOOK_URL: string | undefined = import.meta.env.VITE_GHL_WEBHOOK_URL;
const TIMEOUT_MS = 8000;

export async function captureLead(input: LeadInput): Promise<LeadCaptureResult> {
  if (!WEBHOOK_URL) {
    console.warn(
      '[leadCapture] VITE_GHL_WEBHOOK_URL is not set — lead capture is a no-op. Set the env var on Vercel and redeploy to enable.',
    );
    return { ok: false, reason: 'no-url' };
  }

  const trimmedName = input.name.trim();
  const parts = trimmedName.split(/\s+/);
  const firstName = parts[0] ?? '';
  const lastName = parts.length > 1 ? parts.slice(1).join(' ') : '';

  const body = {
    name: trimmedName,
    firstName,
    lastName,
    email: input.email.trim(),
    source: input.source,
    submittedAt: new Date().toISOString(),
  };

  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const res = await fetch(WEBHOOK_URL, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    if (!res.ok) {
      console.error('[leadCapture] webhook returned non-OK:', res.status);
      return { ok: false, reason: 'http-error', status: res.status };
    }
    return { ok: true };
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      console.error('[leadCapture] webhook timed out after', TIMEOUT_MS, 'ms');
      return { ok: false, reason: 'timeout' };
    }
    console.error('[leadCapture] network error:', err);
    return { ok: false, reason: 'network' };
  } finally {
    window.clearTimeout(timeoutId);
  }
}
