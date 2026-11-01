import { beforeEach, describe, expect, it, vi } from 'vitest';
import { hasSessionToken } from './session';

describe('session bootstrap guard', () => {
  beforeEach(() => {
    vi.stubGlobal('window', { sessionStorage: { getItem: vi.fn() } });
  });

  it('only enables protected bootstrap when a bearer token exists', () => {
    expect(hasSessionToken()).toBe(false);
    vi.mocked(window.sessionStorage.getItem).mockReturnValue('token');
    expect(hasSessionToken()).toBe(true);
  });
});
