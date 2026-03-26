import { flaskHeaders, flaskUrl, forward } from '$lib/server/proxy';

export async function GET({ request, params, url }: { request: Request; params: { uid: string }; url: URL }): Promise<Response> {
  const query = new URLSearchParams({ folder: url.searchParams.get('folder') ?? 'INBOX' });
  const res = await fetch(flaskUrl(`/mail/${params.uid}/attachments`, query), {
    headers: flaskHeaders(request),
  });
  return forward(res);
};