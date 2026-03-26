import { flaskHeaders, flaskUrl, forward } from '$lib/server/proxy';

// GET /api/mail/[uid]?folder=INBOX
export async function GET({ request, params, url }: { request: Request; params: { uid: string }; url: URL }): Promise<Response> {
  const query = new URLSearchParams({ folder: url.searchParams.get('folder') ?? 'INBOX' });
  const res = await fetch(flaskUrl(`/mail/${params.uid}`, query), {
    headers: flaskHeaders(request),
  });
  return forward(res);
};

// PATCH /api/mail/[uid]  — { is_read, is_flagged }
export async function PATCH({ request, params, url }: { request: Request; params: { uid: string }; url: URL }): Promise<Response> {
  const query = new URLSearchParams({ folder: url.searchParams.get('folder') ?? 'INBOX' });
  const body = await request.json();
  const res = await fetch(flaskUrl(`/mail/${params.uid}`, query), {
    method: 'PATCH',
    headers: flaskHeaders(request),
    body: JSON.stringify(body),
  });
  return forward(res);
};

// DELETE /api/mail/[uid]?folder=INBOX
export async function DELETE({ request, params, url }: { request: Request; params: { uid: string }; url: URL }): Promise<Response> {
  const query = new URLSearchParams({ folder: url.searchParams.get('folder') ?? 'INBOX' });
  const res = await fetch(flaskUrl(`/mail/${params.uid}`, query), {
    method: 'DELETE',
    headers: flaskHeaders(request),
  });
  return forward(res);
};