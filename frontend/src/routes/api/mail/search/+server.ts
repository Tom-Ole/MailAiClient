import { flaskHeaders, flaskUrl, forward } from '$lib/server/proxy';

export async function GET({ request, url }): Promise<Response> {
  const params = new URLSearchParams({
    q:         url.searchParams.get('q')         ?? '',
    folder:    url.searchParams.get('folder')    ?? 'INBOX',
    page:      url.searchParams.get('page')      ?? '1',
    batchSize: url.searchParams.get('batchSize') ?? '50',
  });

  const res = await fetch(flaskUrl('/mail/', params), {
    headers: flaskHeaders(request),
  });
  return forward(res);
};