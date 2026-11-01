import type { AccountRegistration, Application, ApplicationInput, ApplicationStatus, CandidateProfile, Company, EmployerDashboard, Job, JobFilters, JobStatus, LoginInput, Notification, User } from '../domain/types';
import type { JobBoardService } from './job-board-service';

const TOKEN_KEY = 'steadwork.access_token';
const USER_KEY = 'steadwork.user';

export class ApiError extends Error {
  constructor(public readonly status: number, message: string, public readonly detail?: string) {
    super(message);
    this.name = 'ApiError';
  }
}

const storage = () => typeof window === 'undefined' ? undefined : window.sessionStorage;
const object = (value: unknown, label: string): Record<string, unknown> => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error(`Invalid ${label} response.`);
  return value as Record<string, unknown>;
};
const required = (value: unknown, keys: string[], label: string) => {
  const result = object(value, label);
  if (keys.some(key => result[key] === undefined || result[key] === null)) throw new Error(`Invalid ${label} response.`);
  return value;
};
const array = (value: unknown, label: string, keys: string[] = []) => {
  if (!Array.isArray(value)) throw new Error(`Invalid ${label} response.`);
  value.forEach(item => required(item, keys, label));
  return value;
};
const json = (method: string, body?: unknown): RequestInit => ({ method, ...(body !== undefined ? { body: JSON.stringify(body) } : {}) });
const qs = (values: object) => {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (value != null && value !== '') params.set(key, Array.isArray(value) ? value.join(',') : String(value));
  });
  return params.toString();
};

async function request<T>(path: string, init: RequestInit = {}, options: { protected?: boolean; shape?: (value: unknown) => T } = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  if (options.protected) {
    const token = storage()?.getItem(TOKEN_KEY);
    if (token) headers.set('Authorization', `Bearer ${token}`);
  }
  const response = await fetch(`/api${path}`, { ...init, headers });
  if (!response.ok) {
    let detail: string | undefined;
    try {
      const body = await response.json();
      if (body && typeof body.detail === 'string') detail = body.detail;
    } catch { /* non-JSON errors use the status fallback */ }
    if (response.status === 401) {
      storage()?.removeItem(TOKEN_KEY);
      storage()?.removeItem(USER_KEY);
    }
    const fallback = response.status === 400 ? 'The request was invalid.'
      : response.status === 401 ? 'Your session has expired. Please sign in again.'
      : response.status === 403 ? 'You do not have permission to perform this action.'
      : response.status === 404 ? 'The requested resource was not found.'
      : response.status === 409 ? 'This request conflicts with existing data.'
      : `Request failed (${response.status}).`;
    throw new ApiError(response.status, detail || fallback, detail);
  }
  if (response.status === 204) return undefined as T;
  let value: unknown;
  try { value = await response.json(); } catch { throw new Error('The server returned malformed JSON.'); }
  return options.shape ? options.shape(value) : value as T;
}

const one = <T>(label: string, keys: string[]) => (value: unknown) => required(value, keys, label) as T;
const many = <T>(label: string, keys: string[] = []) => (value: unknown) => array(value, label, keys) as T[];
const unsupported = <T = never>(method: string): Promise<T> => Promise.reject(new Error(`${method} is not supported by the backend API.`));
const protectedRequest = <T>(path: string, init: RequestInit = {}, shape?: (value: unknown) => T) => request(path, init, { protected: true, shape });

export class HttpJobBoardService implements JobBoardService {
  listJobs(filters: JobFilters = {}) { return request<Job[]>(`/jobs/?${qs(filters)}`, {}, { shape: many<Job>('jobs', ['id', 'title']) }); }
  getJob(id: string) { return request<Job>(`/jobs/${id}/`, {}, { shape: one<Job>('job', ['id', 'title']) }); }
  getCompany(id: string) { return request<Company>(`/companies/${id}/`, {}, { shape: one<Company>('company', ['id', 'name']) }); }
  listCompanies() { return request<Company[]>('/companies/', {}, { shape: many<Company>('companies', ['id', 'name']) }); }
  recommendJobs() { return unsupported('Job recommendations'); }
  saveJob(id: string) { return protectedRequest<void>('/saved-jobs/', json('POST', { jobId: id })); }
  unsaveJob(id: string) { return protectedRequest<void>(`/saved-jobs/${id}/`, json('DELETE')); }
  listSavedJobs() { return protectedRequest<Job[]>('/saved-jobs/', {}, many<Job>('saved jobs', ['id', 'title'])); }
  getCurrentUser() {
    return protectedRequest<User>('/auth/me/', {}, value => {
      const user = one<User>('user', ['id', 'email', 'role'])(value);
      storage()?.setItem(USER_KEY, JSON.stringify(user));
      return user;
    });
  }
  registerAccount(_input: AccountRegistration) { return unsupported('Account registration'); }
  async login(input: LoginInput) {
    const envelope = await request<unknown>('/auth/login/', json('POST', input));
    const body = object(envelope, 'login');
    const token = body.access_token;
    if (typeof token !== 'string' || !token || typeof body.token_type !== 'string') throw new Error('Invalid login response.');
    const user = one<User>('user', ['id', 'email', 'role'])(body.user);
    storage()?.setItem(TOKEN_KEY, token);
    storage()?.setItem(USER_KEY, JSON.stringify(user));
    return user;
  }
  verifyEmail(_token?: string) { return unsupported('Email verification'); }
  requestPasswordReset(_email: string) { return unsupported('Password reset'); }
  switchRole(_role: 'candidate' | 'company') { return unsupported('Demo role switching'); }
  getProfile() { return protectedRequest<CandidateProfile>('/candidate/profile/', {}, one<CandidateProfile>('profile', ['userId'])); }
  updateProfile(profile: Partial<CandidateProfile>) { return protectedRequest<CandidateProfile>('/candidate/profile/', json('PATCH', profile), one<CandidateProfile>('profile', ['userId'])); }
  listApplications() { return protectedRequest<Application[]>('/candidate/applications/', {}, many<Application>('applications', ['id', 'jobId'])); }
  submitApplication(input: ApplicationInput) {
    const { isGuest, ...application } = input;
    return (isGuest ? request<Application>('/applications/guest/', json('POST', application), { shape: one<Application>('application', ['id', 'jobId']) }) : protectedRequest<Application>('/applications/', json('POST', application), one<Application>('application', ['id', 'jobId'])));
  }
  withdrawApplication(id: string) { return protectedRequest<Application>(`/applications/${id}/withdraw/`, json('POST'), one<Application>('application', ['id', 'jobId'])); }
  getEmployerDashboard() { return protectedRequest<EmployerDashboard>('/employer/dashboard/', {}, one<EmployerDashboard>('dashboard', ['activeJobs', 'totalJobs', 'applications', 'shortlisted', 'recent'])); }
  listCompanyJobs() { return protectedRequest<Job[]>('/employer/jobs/', {}, many<Job>('company jobs', ['id', 'title'])); }
  createJob(input: Partial<Job>) { return protectedRequest<Job>('/employer/jobs/', json('POST', input), one<Job>('job', ['id', 'title'])); }
  updateJob(id: string, input: Partial<Job>) { return protectedRequest<Job>(`/employer/jobs/${id}/`, json('PATCH', input), one<Job>('job', ['id', 'title'])); }
  setJobStatus(id: string, status: JobStatus) { return protectedRequest<Job>(`/employer/jobs/${id}/status/`, json('POST', { status }), one<Job>('job', ['id', 'title'])); }
  listApplicants(id: string) { return protectedRequest<Application[]>(`/employer/jobs/${id}/applications/`, {}, many<Application>('applicants', ['id', 'jobId'])); }
  updateApplicationStatus(id: string, status: ApplicationStatus) { return protectedRequest<Application>(`/employer/applications/${id}/status/`, json('POST', { status }), one<Application>('application', ['id', 'jobId'])); }
  listNotifications() { return protectedRequest<Notification[]>('/notifications/', {}, many<Notification>('notifications', ['id', 'title', 'body'])); }
  markNotificationRead(id: string) { return protectedRequest<void>(`/notifications/${id}/read/`, json('POST')); }
  resetDemo() { return unsupported('Demo reset'); }
}
