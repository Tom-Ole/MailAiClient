const FLASK = "http://localhost:5000";

export function flaskHeaders(request: Request) {
  return {
    "Content-Type": "application/json",
    cookie: request.headers.get("cookie") ?? "",
  };
}

export function flaskUrl(path: string, params?: URLSearchParams) {
  const query = params?.toString();
  return `${FLASK}${path}${query ? `?${query}` : ""}`;
}

export function forward(res: Response, body?: BodyInit | null) {
  const response = new Response(body ?? res.body, { status: res.status });
  response.headers.set("content-type", res.headers.get("content-type") ?? "application/json");
  const cookie = res.headers.get("set-cookie");
  if (cookie) response.headers.set("set-cookie", cookie);
  return response;
}