import type { AccountRegistration, Application, ApplicationInput, ApplicationStatus, CandidateProfile, Company, EmployerDashboard, Job, JobFilters, JobStatus, LoginInput, Notification, User } from '../domain/types';

export interface JobBoardService {
  listJobs(filters?: JobFilters): Promise<Job[]>;
  getJob(id: string): Promise<Job | undefined>;
  getCompany(id: string): Promise<Company | undefined>;
  listCompanies(): Promise<Company[]>;
  recommendJobs(): Promise<Job[]>;
  saveJob(id: string): Promise<void>;
  unsaveJob(id: string): Promise<void>;
  listSavedJobs(): Promise<Job[]>;
  getCurrentUser(): Promise<User>;
  registerAccount(input: AccountRegistration): Promise<User>;
  login(input: LoginInput): Promise<User>;
  logout(): Promise<void>;
  switchRole(role: 'candidate' | 'company'): Promise<User>;
  getProfile(): Promise<CandidateProfile>;
  updateProfile(profile: Partial<CandidateProfile>): Promise<CandidateProfile>;
  listApplications(): Promise<Application[]>;
  submitApplication(input: ApplicationInput): Promise<Application>;
  withdrawApplication(id: string): Promise<Application>;
  getEmployerDashboard(): Promise<EmployerDashboard>;
  listCompanyJobs(): Promise<Job[]>;
  createJob(input: Partial<Job>): Promise<Job>;
  updateJob(id: string, input: Partial<Job>): Promise<Job>;
  setJobStatus(id: string, status: JobStatus): Promise<Job>;
  listApplicants(jobId: string): Promise<Application[]>;
  updateApplicationStatus(id: string, status: ApplicationStatus): Promise<Application>;
  listNotifications(): Promise<Notification[]>;
  markNotificationRead(id: string): Promise<void>;
  resetDemo(): Promise<void>;
}
