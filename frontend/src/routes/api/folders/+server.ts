import { flaskHeaders, flaskUrl, forward } from '$lib/server/proxy';


export async function GET({ request }): Promise<Response> {
    const res = await fetch(flaskUrl("/folders"), {
        method: "GET",
        headers: flaskHeaders(request),
    });
    
    return forward(res);
}