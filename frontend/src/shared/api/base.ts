export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function apiClient<T>(
    path: string,
    options?: RequestInit
): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, options);
    if (!res.ok) {
        throw new Error(`API request failed: ${res.status}`);   
    }
    return res.json();
}