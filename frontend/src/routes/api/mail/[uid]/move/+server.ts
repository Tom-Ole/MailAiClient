import { flaskHeaders, flaskUrl, forward } from '$lib/server/proxy';

export async function POST({ request, params }: { request: Request; params: { uid: string } }): Promise<Response> {
  const body = await request.json(); // { source, destination }
  const res = await fetch(flaskUrl(`/mail/${params.uid}/move`), {
    method: 'POST',
    headers: flaskHeaders(request),
    body: JSON.stringify(body),
  });
  return forward(res);
};