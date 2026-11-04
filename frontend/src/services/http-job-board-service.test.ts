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

  it('bootstraps the current user from the authenticated endpoint even without cached user data', async () => {
    vi.mocked(fetch).mockResolvedValue(response({ id: 'u2', email: 'b@example.com', role: 'admin' }));
    await expect(service.getCurrentUser()).resolves.toEqual({ id: 'u2', email: 'b@example.com', role: 'admin' });
    expect(fetch).toHaveBeenCalledWith('/api/auth/me/', expect.objectContaining({ headers: expect.any(Headers) }));
  });

  it('clears the session and maps protected unauthorized responses to a sign-in message', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(response({ access_token: 'token-1', token_type: 'Bearer', user: { id: 'u1', email: 'a@example.com', role: 'candidate' } }))
      .mockResolvedValueOnce(response({ id: 'u1', email: 'a@example.com', role: 'candidate' }))
      .mockResolvedValueOnce(response({ detail: 'Token is invalid.' }, 401))
      .mockResolvedValueOnce(response({ detail: 'Token is invalid.' }, 401));
    await service.login({ email: 'a@example.com', password: 'secret' });
    await expect(service.getCurrentUser()).resolves.toMatchObject({ id: 'u1' });
    expect(fetch).toHaveBeenLastCalledWith('/api/auth/me/', expect.objectContaining({ headers: expect.any(Headers) }));
    await expect(service.listApplications()).rejects.toMatchObject({ status: 401, detail: 'Token is invalid.', message: 'Please sign in to continue.' });
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

  it('registers through the API and stores the returned session', async () => {
    vi.mocked(fetch).mockResolvedValue(response({ access_token: 'registration-token', token_type: 'Bearer', user: { id: 'u1', name: 'A', email: 'a@example.com', role: 'candidate', emailVerified: false } }, 201));
    await expect(service.registerAccount({ name: 'A', email: 'a@example.com', password: 'long-password', role: 'candidate' })).resolves.toMatchObject({ name: 'A', emailVerified: false });
    expect(new Headers(vi.mocked(fetch).mock.calls[0][1]?.headers).get('Content-Type')).toBe('application/json');
    expect(window.sessionStorage.getItem('steadwork.access_token')).toBe('registration-token');
  });

  it('calls verification and password reset endpoints with the correct payloads', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(response({ id: 'u1', name: 'A', email: 'a@example.com', role: 'candidate', emailVerified: true }))
      .mockResolvedValueOnce(response({ detail: 'If an account exists, a message was sent.' }, 202))
      .mockResolvedValueOnce(response(undefined, 204));
    await expect(service.verifyEmail('verify-token')).resolves.toMatchObject({ emailVerified: true });
    await service.requestPasswordReset('a@example.com');
    await service.completePasswordReset('reset-token', 'a-new-password');
    expect(JSON.parse(vi.mocked(fetch).mock.calls[0][1]?.body as string)).toEqual({ token: 'verify-token' });
    expect(JSON.parse(vi.mocked(fetch).mock.calls[1][1]?.body as string)).toEqual({ email: 'a@example.com' });
    expect(JSON.parse(vi.mocked(fetch).mock.calls[2][1]?.body as string)).toEqual({ token: 'reset-token', password: 'a-new-password' });
  });

  it('clears the local session after requesting server-side logout', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(response({ access_token: 'logout-token', token_type: 'Bearer', user: { id: 'u1', email: 'a@example.com', role: 'candidate' } }))
      .mockResolvedValueOnce(response(undefined, 204));
    await service.login({ email: 'a@example.com', password: 'secret' });
    await service.logout();
    expect(vi.mocked(fetch).mock.calls[1][0]).toBe('/api/auth/logout/');
    expect(window.sessionStorage.getItem('steadwork.access_token')).toBeNull();
  });

  it('turns network and server failures into safe actionable messages', async () => {
    vi.mocked(fetch).mockRejectedValueOnce(new TypeError('Failed to fetch'));
    await expect(service.listJobs()).rejects.toMatchObject({ status: 0, message: 'Could not connect to Steadwork. Check your connection and try again.' });
    vi.mocked(fetch).mockResolvedValueOnce(response({ detail: 'database password leaked' }, 500));
    await expect(service.listJobs()).rejects.toMatchObject({ status: 500, message: 'Something went wrong on the server. Please try again.', detail: 'database password leaked' });
  });
});
