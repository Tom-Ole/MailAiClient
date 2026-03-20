// routes/api/mail/server.ts

export interface MailDTO {
    message_id: string,
    sender: string,
    receiver: string,
    subject: string,
    date: string,
    body: string,
}

export interface MailDtoRes {
    mails: MailDTO[]
}

export async function GET({url, fetch}) {
    const page = url.searchParams.get("page") ?? "1";
    const batchSize = url.searchParams.get("batchSize") ?? "50";

    const res = await fetch(`http://localhost:5000/mail/?page=${page}&batchSize=${batchSize}`);

    if (!res.ok) {
        console.log(res);

        return new Response("", {status: 500})
    }

    const data = await res.json() as MailDtoRes


    return new Response(JSON.stringify(data), {
        headers: { "Content-Type": "application/json"}
    });
};