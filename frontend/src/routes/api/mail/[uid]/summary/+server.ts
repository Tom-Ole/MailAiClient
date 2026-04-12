import { flaskHeaders, flaskUrl } from "$lib/server/proxy";

export async function GET({ request, params, fetch, url }): Promise<Response> {
  const query = new URLSearchParams({
    folder: url.searchParams.get("folder") ?? "INBOX",
  });
  const res = await fetch(flaskUrl(`/ai/summary/${params.uid}`, query), {
    headers: flaskHeaders(request),
  }); // returns  { summary: string, uid: string, folder: string }


  const data = await res.json();
  console.log("Summary response:", data);

  if (!res.ok) {
    return new Response(JSON.stringify({ summary: "Error occurred while fetching summary" }), {
      status: res.status,
      headers: {
        "Content-Type": "application/json",
      },
    });
  }

  return new Response(JSON.stringify(data), {
    status: res.status,
    headers: {
      "Content-Type": "application/json",
    },
  });
}
