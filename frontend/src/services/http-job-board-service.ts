import type { AccountRegistration, Application, ApplicationInput, ApplicationStatus, CandidateProfile, Company, EmployerDashboard, Job, JobFilters, JobStatus, LoginInput, Notification, User } from '../domain/types';
import type { JobBoardService } from './job-board-service';

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api${path}`, { ...init, credentials: 'include', headers: { 'Content-Type': 'application/json', ...init.headers } });
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
const json = (method: string, body?: unknown): RequestInit => ({ method, ...(body ? { body: JSON.stringify(body) } : {}) });
const qs = (values: object) => { const params = new URLSearchParams(); Object.entries(values).forEach(([k,v]) => { if (v != null && v !== '') params.set(k, Array.isArray(v) ? v.join(',') : String(v)); }); return params.toString(); };

/** Thin adapter for the proposed Django REST API. No live server is configured in this release. */
export class HttpJobBoardService implements JobBoardService {
  listJobs(f: JobFilters = {}) { return request<Job[]>(`/jobs/?${qs(f)}`); }
  getJob(id: string) { return request<Job>(`/jobs/${id}/`); }
  getCompany(id: string) { return request<Company>(`/companies/${id}/`); }
  listCompanies() { return request<Company[]>('/companies/'); }
  recommendJobs() { return request<Job[]>('/jobs/recommended/'); }
  saveJob(id: string) { return request<void>(`/saved-jobs/`, json('POST', { jobId: id })); }
  unsaveJob(id: string) { return request<void>(`/saved-jobs/${id}/`, json('DELETE')); }
  listSavedJobs() { return request<Job[]>('/saved-jobs/'); }
  getCurrentUser() { return request<User>('/auth/me/'); }
  registerAccount(input: AccountRegistration) { return request<User>('/auth/register/', json('POST', input)); }
  login(input: LoginInput) { return request<User>('/auth/login/', json('POST', input)); }
  verifyEmail(token?: string) { return request<User>('/auth/verify-email/', json('POST', { token })); }
  requestPasswordReset(email: string) { return request<void>('/auth/password-reset/', json('POST', { email })); }
  switchRole(role: 'candidate' | 'company') { return request<User>('/auth/demo-role/', json('POST', { role })); }
  getProfile() { return request<CandidateProfile>('/candidate/profile/'); }
  updateProfile(profile: Partial<CandidateProfile>) { return request<CandidateProfile>('/candidate/profile/', json('PATCH', profile)); }
  listApplications() { return request<Application[]>('/candidate/applications/'); }
  submitApplication(input: ApplicationInput) {
    const { isGuest, ...application } = input;
    return request<Application>(isGuest ? '/applications/guest/' : '/applications/', json('POST', application));
  }
  withdrawApplication(id: string) { return request<Application>(`/applications/${id}/withdraw/`, json('POST')); }
  getEmployerDashboard() { return request<EmployerDashboard>('/employer/dashboard/'); }
  listCompanyJobs() { return request<Job[]>('/employer/jobs/'); }
  createJob(input: Partial<Job>) { return request<Job>('/employer/jobs/', json('POST', input)); }
  updateJob(id: string, input: Partial<Job>) { return request<Job>(`/employer/jobs/${id}/`, json('PATCH', input)); }
  setJobStatus(id: string, status: JobStatus) { return request<Job>(`/employer/jobs/${id}/status/`, json('POST', { status })); }
  listApplicants(id: string) { return request<Application[]>(`/employer/jobs/${id}/applications/`); }
  updateApplicationStatus(id: string, status: ApplicationStatus) { return request<Application>(`/employer/applications/${id}/status/`, json('POST', { status })); }
  listNotifications() { return request<Notification[]>('/notifications/'); }
  markNotificationRead(id: string) { return request<void>(`/notifications/${id}/read/`, json('POST')); }
  resetDemo() { return Promise.resolve(); }
}
