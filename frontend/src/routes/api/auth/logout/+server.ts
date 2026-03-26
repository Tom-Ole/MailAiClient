
export async function POST({ fetch }): Promise<Response> {

    const res = await fetch("http://localhost:5000/auth/logout");

    // return type: {"message": "Logged out"}
    const data = await res.json();

   return new Response(JSON.stringify(data), {
        status: res.status,
        headers: {
            "Content-Type": "application/json"
        }
    });
};