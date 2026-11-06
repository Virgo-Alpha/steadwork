export type UserRole = 'candidate' | 'company' | 'admin';
export type JobStatus = 'Draft' | 'Published' | 'Closed' | 'Expired';
export type ApplicationStatus = 'Applied' | 'Under Review' | 'Shortlisted' | 'Rejected' | 'Hired' | 'Withdrawn' | 'External click';

export interface Job {
  id: string; companyId: string; title: string; description: string; location: string; remotePolicy: 'Remote' | 'Hybrid' | 'On-site';
  jobType: 'Full-time' | 'Part-time' | 'Contract' | 'Internship'; salaryMin: number; salaryMax: number; currency: string;
  experienceLevel: 'Entry' | 'Mid' | 'Senior' | 'Lead'; skills: string[]; responsibilities: string[]; qualifications: string[];
  benefits: string[]; applicationMethod: 'Internal' | 'External'; externalApplyUrl?: string; status: JobStatus; postedAt: string;
  deadline: string; applicationCount: number;
}
export interface Company { id: string; name: string; description: string; website: string; logo: string; accent: string; }
export interface User { id: string; name: string; email: string; role: UserRole; emailVerified?: boolean; }
export interface AccountRegistration { name: string; email: string; password: string; role: 'candidate' | 'company'; companyName?: string; }
export interface LoginInput { email: string; password: string; }
export interface CandidateProfile {
  userId: string; headline: string; location: string; skills: string[]; experience: string; education: string;
  preferences: string; cvFiles: string[]; defaultCvId: string;
}
export interface Application {
  id: string; jobId: string; candidateId?: string; candidateName: string; candidateEmail: string; cvName: string;
  coverLetter: string; status: ApplicationStatus; createdAt: string;
}
export interface EmployerApplication extends Application { jobTitle: string; }
export interface EmployerCandidateProfile {
  userId: string; headline: string; location: string; skills: string[]; experience: string; education: string;
}
export interface Notification { id: string; title: string; body: string; readAt?: string; createdAt: string; }
export interface JobFilters {
  keyword?: string; location?: string; jobType?: string; remotePolicy?: string; experienceLevel?: string;
  salaryMin?: number; skills?: string[]; companyId?: string; postedWithin?: number; sort?: 'recent' | 'salary' | 'relevance';
}
export interface EmployerDashboard { companyName: string; activeJobs: number; totalJobs: number; applications: number; shortlisted: number; recent: Application[]; }
export interface ApplicationInput { jobId: string; candidateName: string; candidateEmail: string; cvName: string; coverLetter: string; isGuest?: boolean; }
