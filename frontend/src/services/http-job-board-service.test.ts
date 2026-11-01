import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, HttpJobBoardService } from './http-job-board-service';

function response(body: unknown, status = 200) {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('HttpJobBoardService', () => {
  const service = new HttpJobBoardService();

  beforeEach(() => {
    const values = new Map<string, string>();
    vi.stubGlobal('window', { sessionStorage: {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => values.set(key, value),
      removeItem: (key: string) => values.delete(key),
    } });
    vi.stubGlobal('fetch', vi.fn());
  });

  it('uses the API path and parses bare arrays', async () => {
    vi.mocked(fetch).mockResolvedValue(response([{ id: 'j1', title: 'Engineer' }]));
    await expect(service.listJobs({ keyword: 'engineer' })).resolves.toEqual([{ id: 'j1', title: 'Engineer' }]);
    expect(fetch).toHaveBeenCalledWith('/api/jobs/?keyword=engineer', expect.objectContaining({ headers: expect.any(Headers) }));
  });

  it('unwraps login, stores the bearer token, and attaches it to protected requests', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(response({ access_token: 'token-1', token_type: 'Bearer', user: { id: 'u1', email: 'a@example.com', role: 'candidate' } }))
      .mockResolvedValueOnce(response([]));
    await service.login({ email: 'a@example.com', password: 'secret' });
    await service.listApplications();
    const options = vi.mocked(fetch).mock.calls[1][1] as RequestInit;
    expect(new Headers(options.headers).get('Authorization')).toBe('Bearer token-1');
  });

  it('clears the session and exposes backend detail on unauthorized responses', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(response({ access_token: 'token-1', token_type: 'Bearer', user: { id: 'u1', email: 'a@example.com', role: 'candidate' } }))
      .mockResolvedValueOnce(response({ id: 'u1', email: 'a@example.com', role: 'candidate' }))
      .mockResolvedValueOnce(response({ detail: 'Token is invalid.' }, 401))
      .mockResolvedValueOnce(response({ detail: 'Token is invalid.' }, 401));
    await service.login({ email: 'a@example.com', password: 'secret' });
    await expect(service.getCurrentUser()).resolves.toMatchObject({ id: 'u1' });
    expect(fetch).toHaveBeenLastCalledWith('/api/auth/me/', expect.objectContaining({ headers: expect.any(Headers) }));
    await expect(service.listApplications()).rejects.toMatchObject({ status: 401, detail: 'Token is invalid.', message: 'Token is invalid.' });
    await expect(service.getCurrentUser()).rejects.toMatchObject({ status: 401 });
  });

  it('rejects malformed success payloads and distinguishes status errors', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(response({ nope: true }));
    await expect(service.listCompanies()).rejects.toThrow('Invalid companies response.');
    vi.mocked(fetch).mockResolvedValueOnce(response({}, 409));
    const failed = service.listJobs();
    await expect(failed).rejects.toBeInstanceOf(ApiError);
    await expect(failed).rejects.toMatchObject({ status: 409, message: 'This request conflicts with existing data.' });
  });

  it('fails unsupported methods explicitly instead of falling back to mocks', async () => {
    await expect(service.registerAccount({ name: 'A', email: 'a@example.com', password: 'x', role: 'candidate' })).rejects.toThrow('not supported');
    expect(fetch).not.toHaveBeenCalled();
  });
});
