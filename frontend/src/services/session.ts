export const ACCESS_TOKEN_KEY = 'steadwork.access_token';

export function hasSessionToken(): boolean {
  return typeof window !== 'undefined' && Boolean(window.sessionStorage.getItem(ACCESS_TOKEN_KEY));
}
