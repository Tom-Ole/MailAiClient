import { flaskHeaders, flaskUrl, forward } from '$lib/server/proxy';

export async function POST({ request, params, url }: { request: Request; params: { uid: string }; url: URL }): Promise<Response> {
  const query = new URLSearchParams({
    folder:    url.searchParams.get('folder')    ?? 'INBOX',
    reply_all: url.searchParams.get('reply_all') ?? 'false',
  });
  const body = await request.json();
  const res = await fetch(flaskUrl(`/mail/${params.uid}/reply`, query), {
    method: 'POST',
    headers: flaskHeaders(request),
    body: JSON.stringify(body),
  });
  return forward(res);
};