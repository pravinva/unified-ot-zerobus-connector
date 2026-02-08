function isJsonContentType(ct: string | null): boolean {
  // Accept `application/json` plus vendor types like `application/problem+json`
  // and WoT TD responses like `application/td+json`.
  return (ct ?? "").toLowerCase().includes("json");
}

async function parseBody(resp: Response): Promise<unknown> {
  const ct = resp.headers.get("content-type");
  if (isJsonContentType(ct)) return await resp.json();
  return await resp.text();
}

export async function apiFetch(path: string, options: RequestInit = {}): Promise<unknown> {
  const resp = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers ?? {}) },
    ...options,
  });

  const body = await parseBody(resp);

  if (!resp.ok) {
    const msg =
      typeof body === "string"
        ? body
        : typeof (body as any)?.message === "string"
          ? (body as any).message
          : typeof (body as any)?.error === "string"
            ? (body as any).error
            : `HTTP ${resp.status}`;
    throw new Error(msg);
  }

  return body;
}

export async function apiJson<T>(path: string, options?: RequestInit): Promise<T> {
  return (await apiFetch(path, options)) as T;
}

