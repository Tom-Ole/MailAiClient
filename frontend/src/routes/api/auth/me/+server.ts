
export async function GET({ fetch, cookies }): Promise<Response> {

    const res = await fetch("http://localhost:5000/auth/me", {
        method: "GET",
        headers: {
            cookie: cookies.get("session") ? `session=${cookies.get("session")}` : ""
        }
    });

    
    // return type: {
    //     "authenticated": True,
    //     "user": creds["user"],
    //     "imap_host": creds["imap_host"],
    //     "smtp_host": creds["smtp_host"],
    // }
    const data = await res.json();

   return new Response(JSON.stringify(data), {
        status: res.status,
        headers: {
            "Content-Type": "application/json"
        }
    });
};