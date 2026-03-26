import { flaskHeaders, flaskUrl, forward } from '$lib/server/proxy';

export async function POST({ request }): Promise<Response> {
  const body = await request.json();
  const res = await fetch(flaskUrl('/mail/send'), {
    method: 'POST',
    headers: flaskHeaders(request),
    body: JSON.stringify(body),
  });
  return forward(res);
};