export const ACCESS_TOKEN_KEY = 'steadwork.access_token';

export function hasSessionToken(): boolean {
  return typeof window !== 'undefined' && Boolean(window.sessionStorage.getItem(ACCESS_TOKEN_KEY));
}

export function clearSession(): void {
  if (typeof window !== 'undefined') {
    window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    window.sessionStorage.removeItem('steadwork.user');
  }
}
