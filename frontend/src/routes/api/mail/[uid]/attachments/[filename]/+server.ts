import { flaskHeaders, flaskUrl } from '$lib/server/proxy';

export async function GET({ request, params, url }: { request: Request; params: { uid: string; filename: string }; url: URL }): Promise<Response> {
  const query = new URLSearchParams({ folder: url.searchParams.get('folder') ?? 'INBOX' });
  const res = await fetch(
    flaskUrl(`/mail/${params.uid}/attachments/${params.filename}`, query),
    { headers: flaskHeaders(request) }
  );

  // Stream the binary back - preserve content-type and content-disposition ~created by claude
  return new Response(res.body, {
    status: res.status,
    headers: {
      'content-type': res.headers.get('content-type') ?? 'application/octet-stream',
      'content-disposition': res.headers.get('content-disposition') ?? `attachment; filename="${params.filename}"`,
    },
  });
};