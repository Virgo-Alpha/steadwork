import type { AccountRegistration, Application, ApplicationInput, ApplicationStatus, CandidateProfile, Company, EmployerDashboard, Job, JobFilters, JobStatus, LoginInput, Notification, User } from '../domain/types';
import type { JobBoardService } from './job-board-service';

const companies: Company[] = [
  { id: 'c-northstar', name: 'Northstar Labs', description: 'Building the quiet infrastructure behind a more open internet.', website: 'northstarlabs.dev', logo: 'N', accent: '#d7eddf' },
  { id: 'c-fieldnote', name: 'Fieldnote', description: 'A thoughtful workspace for teams doing their best work.', website: 'fieldnote.work', logo: 'F', accent: '#f2dfd2' },
  { id: 'c-orbit', name: 'Orbit Health', description: 'Making exceptional care easier to reach, everywhere.', website: 'orbit.health', logo: 'O', accent: '#dce6ed' },
  { id: 'c-cairn', name: 'Cairn Systems', description: 'Reliable data tools for the people who keep the world moving.', website: 'cairn.systems', logo: 'C', accent: '#eee7cc' },
  { id: 'c-studio', name: 'Common Studio', description: 'An independent product studio shaping useful digital things.', website: 'common.studio', logo: 'C', accent: '#e9deeb' },
];
const dateAt = (dayOffset: number) => new Date(Date.now() + dayOffset * 86400000).toISOString().slice(0, 10);
const initialJobs: Job[] = [
  { id: 'job-platform', companyId: 'c-northstar', title: 'Senior Platform Engineer', description: 'Help us build dependable primitives for services used by thousands of teams. You will work across infrastructure and product, partnering with a small, senior team that values clarity over ceremony.', location: 'New York, NY', remotePolicy: 'Hybrid', jobType: 'Full-time', salaryMin: 168000, salaryMax: 218000, currency: 'USD', experienceLevel: 'Senior', skills: ['Kubernetes', 'Go', 'AWS', 'Terraform'], responsibilities: ['Design resilient platform services', 'Improve developer experience', 'Own reliability improvements'], qualifications: ['5+ years building production systems', 'Strong Go or equivalent experience'], benefits: ['Health and dental cover', 'Home office budget', 'Four week sabbatical after year three'], applicationMethod: 'Internal', status: 'Published', postedAt: dateAt(-2), deadline: dateAt(31), applicationCount: 18 },
  { id: 'job-product', companyId: 'c-fieldnote', title: 'Product Designer, Collaboration', description: 'Shape the everyday moments that help distributed teams feel in sync. You will bring craft, curiosity, and a strong point of view to a product with real momentum.', location: 'Brooklyn, NY', remotePolicy: 'Remote', jobType: 'Full-time', salaryMin: 142000, salaryMax: 176000, currency: 'USD', experienceLevel: 'Mid', skills: ['Product Design', 'Figma', 'Research', 'Prototyping'], responsibilities: ['Lead a product area from discovery through launch', 'Build and evolve our design system'], qualifications: ['A portfolio showing thoughtful product decisions'], benefits: ['Flexible hours', 'Learning stipend', 'Equity'], applicationMethod: 'Internal', status: 'Published', postedAt: dateAt(-3), deadline: dateAt(27), applicationCount: 31 },
  { id: 'job-data', companyId: 'c-orbit', title: 'Staff Data Engineer', description: 'Create the data foundations for better care decisions. Work with product, clinical, and engineering partners to build trusted pipelines that make complex systems legible.', location: 'United States', remotePolicy: 'Remote', jobType: 'Full-time', salaryMin: 185000, salaryMax: 232000, currency: 'USD', experienceLevel: 'Lead', skills: ['Python', 'SQL', 'dbt', 'Snowflake'], responsibilities: ['Set technical direction for analytics infrastructure', 'Mentor a growing data team'], qualifications: ['Experience scaling modern data platforms'], benefits: ['Medical coverage', 'Annual retreat', 'Caregiver leave'], applicationMethod: 'External', externalApplyUrl: 'https://orbit.health/careers', status: 'Published', postedAt: dateAt(-4), deadline: dateAt(21), applicationCount: 12 },
  { id: 'job-frontend', companyId: 'c-cairn', title: 'Frontend Engineer', description: 'Make complex operations feel simple. Join a product team that sweats the details and gives engineers room to own the whole experience.', location: 'Boston, MA', remotePolicy: 'Hybrid', jobType: 'Full-time', salaryMin: 128000, salaryMax: 158000, currency: 'USD', experienceLevel: 'Mid', skills: ['React', 'TypeScript', 'CSS', 'Accessibility'], responsibilities: ['Deliver polished workflow experiences', 'Collaborate closely with design and research'], qualifications: ['3+ years shipping React applications'], benefits: ['Commuter support', 'Flexible leave', 'Professional development'], applicationMethod: 'Internal', status: 'Published', postedAt: dateAt(-6), deadline: dateAt(14), applicationCount: 24 },
  { id: 'job-fullstack', companyId: 'c-studio', title: 'Founding Full-stack Engineer', description: 'Build meaningful tools from the first line of code. You will be a close partner to the founders, moving fluidly between product thinking and practical engineering.', location: 'San Francisco, CA', remotePolicy: 'Hybrid', jobType: 'Full-time', salaryMin: 155000, salaryMax: 205000, currency: 'USD', experienceLevel: 'Senior', skills: ['TypeScript', 'React', 'Node.js', 'PostgreSQL'], responsibilities: ['Build and ship core product features', 'Help shape engineering culture'], qualifications: ['You thrive in small, high-trust teams'], benefits: ['Meaningful equity', 'Flexible work', 'Generous parental leave'], applicationMethod: 'Internal', status: 'Published', postedAt: dateAt(-8), deadline: dateAt(19), applicationCount: 9 },
  { id: 'job-junior', companyId: 'c-northstar', title: 'Software Engineer, Early Career', description: 'Start your engineering career alongside generous mentors and a team that values good questions as much as good answers.', location: 'New York, NY', remotePolicy: 'On-site', jobType: 'Full-time', salaryMin: 94000, salaryMax: 122000, currency: 'USD', experienceLevel: 'Entry', skills: ['Python', 'SQL', 'Git'], responsibilities: ['Contribute to customer-facing features', 'Learn our systems with a supportive team'], qualifications: ['Recent graduate or equivalent experience'], benefits: ['Mentorship program', 'Learning budget'], applicationMethod: 'Internal', status: 'Published', postedAt: dateAt(-10), deadline: dateAt(25), applicationCount: 47 },
];
const STORAGE_KEY = 'steadwork-job-board-v2';
type State = { jobs: Job[]; saved: string[]; user: User; profile: CandidateProfile; applications: Application[]; notifications: Notification[] };
const defaultState = (): State => ({
  jobs: structuredClone(initialJobs), saved: ['job-data'],
  user: { id: 'user-maya', name: 'Maya Chen', email: 'maya.chen@example.com', role: 'candidate', emailVerified: true },
  profile: { userId: 'user-maya', headline: 'Product-minded software engineer', location: 'New York, NY', skills: ['React', 'TypeScript', 'Python', 'SQL'], experience: 'Building thoughtful web products for 5 years.', education: 'B.S. Computer Science, University of Vermont', preferences: 'Remote or hybrid · product-led teams', cvFiles: ['Maya-Chen-Resume.pdf', 'Maya-Chen-Engineering-CV.pdf'], defaultCvId: 'Maya-Chen-Resume.pdf' },
  applications: [
    { id: 'app-seed-1', jobId: 'job-frontend', candidateId: 'user-maya', candidateName: 'Maya Chen', candidateEmail: 'maya.chen@example.com', cvName: 'Maya-Chen-Resume.pdf', coverLetter: 'I am excited by Cairn’s focus on making complex systems approachable.', status: 'Under Review', createdAt: dateAt(-5) },
    { id: 'app-seed-2', jobId: 'job-product', candidateId: 'user-maya', candidateName: 'Maya Chen', candidateEmail: 'maya.chen@example.com', cvName: 'Maya-Chen-Resume.pdf', coverLetter: 'I care deeply about collaboration tools that respect people’s attention.', status: 'Applied', createdAt: dateAt(-3) },
    { id: 'app-seed-3', jobId: 'job-platform', candidateId: 'user-ari', candidateName: 'Ari Patel', candidateEmail: 'ari.patel@example.com', cvName: 'Ari-Patel-Resume.pdf', coverLetter: 'The platform reliability work is exactly where I want to focus next.', status: 'Shortlisted', createdAt: dateAt(-2) },
  ],
  notifications: [
    { id: 'note-1', title: 'Your application is under review', body: 'Cairn Systems has started reviewing your Frontend Engineer application.', readAt: undefined, createdAt: dateAt(-2) },
    { id: 'note-2', title: 'A role that fits your skills', body: 'Staff Data Engineer at Orbit Health matches your Python and SQL experience.', readAt: dateAt(-4), createdAt: dateAt(-4) },
  ],
});

export class MockJobBoardService implements JobBoardService {
  private state: State;
  constructor(private storage?: Pick<Storage, 'getItem' | 'setItem'>) {
    this.state = this.readState();
  }
  private readState(): State {
    if (this.storage) {
      try { const saved = this.storage.getItem(STORAGE_KEY); if (saved) return { ...defaultState(), ...JSON.parse(saved) }; } catch { /* reset corrupted demo state */ }
    }
    return defaultState();
  }
  private persist() { this.storage?.setItem(STORAGE_KEY, JSON.stringify(this.state)); }
  async listJobs(filters: JobFilters = {}) {
    let rows = this.state.jobs.filter(j => j.status === 'Published');
    const text = filters.keyword?.trim().toLowerCase();
    if (text) rows = rows.filter(j => `${j.title} ${j.description} ${j.skills.join(' ')}`.toLowerCase().includes(text) || this.company(j.companyId).name.toLowerCase().includes(text));
    if (filters.location) rows = rows.filter(j => j.location.toLowerCase().includes(filters.location!.toLowerCase()));
    if (filters.jobType) rows = rows.filter(j => j.jobType === filters.jobType);
    if (filters.remotePolicy) rows = rows.filter(j => j.remotePolicy === filters.remotePolicy);
    if (filters.experienceLevel) rows = rows.filter(j => j.experienceLevel === filters.experienceLevel);
    if (filters.salaryMin) rows = rows.filter(j => j.salaryMax >= filters.salaryMin!);
    if (filters.skills?.length) rows = rows.filter(j => filters.skills!.every(s => j.skills.some(x => x.toLowerCase() === s.toLowerCase())));
    if (filters.companyId) rows = rows.filter(j => j.companyId === filters.companyId);
    if (filters.postedWithin) rows = rows.filter(j => Date.now() - new Date(j.postedAt).getTime() <= filters.postedWithin! * 86400000);
    if (filters.sort === 'salary') rows.sort((a,b) => b.salaryMax - a.salaryMax);
    else rows.sort((a,b) => b.postedAt.localeCompare(a.postedAt));
    return structuredClone(rows);
  }
  async getJob(id: string) { const job = this.state.jobs.find(j => j.id === id); return job && structuredClone(job); }
  async getCompany(id: string) { const c = companies.find(x => x.id === id); return c && structuredClone(c); }
  async listCompanies() { return structuredClone(companies); }
  private company(id: string) { return companies.find(c => c.id === id)!; }
  async recommendJobs() {
    const skills = this.state.profile.skills.map(s => s.toLowerCase());
    return structuredClone(this.state.jobs.filter(j => j.status === 'Published').map(j => ({ j, overlap: j.skills.filter(s => skills.includes(s.toLowerCase())).length })).filter(x => x.overlap > 0).sort((a,b) => b.overlap-a.overlap).map(x => x.j));
  }
  async saveJob(id: string) { if (!this.state.jobs.some(j => j.id === id)) throw new Error('Job not found'); if (!this.state.saved.includes(id)) this.state.saved.push(id); this.persist(); }
  async unsaveJob(id: string) { this.state.saved = this.state.saved.filter(x => x !== id); this.persist(); }
  async listSavedJobs() { return structuredClone(this.state.jobs.filter(j => this.state.saved.includes(j.id))); }
  async getCurrentUser() { return structuredClone(this.state.user); }
  async registerAccount(input: AccountRegistration) {
    if (!input.name.trim() || !input.email.trim() || input.password.length < 8) throw new Error('Enter your name, a valid email, and a password with at least 8 characters.');
    this.state.user = { id: `user-${Date.now()}`, name: input.name.trim(), email: input.email.trim().toLowerCase(), role: input.role, emailVerified: false };
    if (input.role === 'candidate') {
      this.state.profile = { userId: this.state.user.id, headline: '', location: '', skills: [], experience: '', education: '', preferences: '', cvFiles: [], defaultCvId: '' };
    }
    this.persist();
    return structuredClone(this.state.user);
  }
  async login(input: LoginInput) {
    if (!input.email.trim() || !input.password) throw new Error('Enter your email and password.');
    const email = input.email.trim().toLowerCase();
    if (this.state.user.email.toLowerCase() !== email) {
      const name = email.split('@')[0].replace(/[._-]+/g, ' ').replace(/\b\w/g, letter => letter.toUpperCase());
      this.state.user = { id: `user-${Date.now()}`, name, email, role: 'candidate', emailVerified: true };
      this.state.profile = { userId: this.state.user.id, headline: '', location: '', skills: [], experience: '', education: '', preferences: '', cvFiles: [], defaultCvId: '' };
      this.persist();
    }
    return structuredClone(this.state.user);
  }
  async verifyEmail(_token?: string) {
    this.state.user.emailVerified = true;
    this.persist();
    return structuredClone(this.state.user);
  }
  async requestPasswordReset(email: string) {
    if (!email.trim()) throw new Error('Enter an email address.');
  }
  async switchRole(role: 'candidate' | 'company') { this.state.user = role === 'company' ? { id: 'user-company', name: 'Jordan Lee', email: 'jordan@northstarlabs.dev', role: 'company' } : defaultState().user; this.persist(); return structuredClone(this.state.user); }
  async getProfile() { return structuredClone(this.state.profile); }
  async updateProfile(profile: Partial<CandidateProfile>) { this.state.profile = { ...this.state.profile, ...profile }; this.persist(); return structuredClone(this.state.profile); }
  async listApplications() { return structuredClone(this.state.applications.filter(a => a.candidateId === this.state.user.id)); }
  async submitApplication(input: ApplicationInput) {
    const job = this.state.jobs.find(j => j.id === input.jobId);
    if (!job || job.status !== 'Published') throw new Error('This role is no longer accepting applications.');
    const duplicate = this.state.applications.some(a => a.jobId === input.jobId && ((a.candidateId && a.candidateId === this.state.user.id) || a.candidateEmail.toLowerCase() === input.candidateEmail.toLowerCase()));
    if (duplicate) throw new Error('You have already applied to this role.');
    const { isGuest, ...applicationInput } = input;
    const application: Application = { ...applicationInput, id: `app-${Date.now()}`, candidateId: this.state.user.role === 'candidate' && !isGuest ? this.state.user.id : undefined, status: job.applicationMethod === 'External' ? 'External click' : 'Applied', createdAt: new Date().toISOString().slice(0,10) };
    this.state.applications.unshift(application); job.applicationCount++; this.persist(); return structuredClone(application);
  }
  async withdrawApplication(id: string) { const a = this.state.applications.find(x => x.id === id); if (!a) throw new Error('Application not found'); if (!a.candidateId || a.candidateId !== this.state.user.id) throw new Error('Only signed-in candidates can withdraw an application.'); a.status = 'Withdrawn'; this.persist(); return structuredClone(a); }
  async getEmployerDashboard(): Promise<EmployerDashboard> {
    const jobs = this.state.jobs.filter(j => j.companyId === 'c-northstar');
    const apps = this.state.applications.filter(a => jobs.some(j => j.id === a.jobId));
    return { activeJobs: jobs.filter(j => j.status === 'Published').length, totalJobs: jobs.length, applications: apps.length, shortlisted: apps.filter(a => a.status === 'Shortlisted').length, recent: structuredClone(apps.slice(0,4)) };
  }
  async listCompanyJobs() { return structuredClone(this.state.jobs.filter(j => j.companyId === 'c-northstar')); }
  async createJob(input: Partial<Job>) {
    const job: Job = { id: `job-${Date.now()}`, companyId: 'c-northstar', title: input.title || 'Untitled role', description: input.description || '', location: input.location || 'New York, NY', remotePolicy: input.remotePolicy || 'Hybrid', jobType: input.jobType || 'Full-time', salaryMin: Number(input.salaryMin) || 100000, salaryMax: Number(input.salaryMax) || 150000, currency: input.currency || 'USD', experienceLevel: input.experienceLevel || 'Mid', skills: input.skills || [], responsibilities: input.responsibilities || [], qualifications: input.qualifications || [], benefits: input.benefits || [], applicationMethod: input.applicationMethod || 'Internal', externalApplyUrl: input.externalApplyUrl, status: input.status || 'Draft', postedAt: dateAt(0), deadline: input.deadline || dateAt(30), applicationCount: 0 };
    this.state.jobs.unshift(job); this.persist(); return structuredClone(job);
  }
  async updateJob(id: string, input: Partial<Job>) { const i = this.state.jobs.findIndex(j => j.id === id); if (i < 0) throw new Error('Job not found'); this.state.jobs[i] = { ...this.state.jobs[i], ...input }; this.persist(); return structuredClone(this.state.jobs[i]); }
  async setJobStatus(id: string, status: JobStatus) { return this.updateJob(id, { status }); }
  async listApplicants(jobId: string) { return structuredClone(this.state.applications.filter(a => a.jobId === jobId)); }
  async updateApplicationStatus(id: string, status: ApplicationStatus) { const a = this.state.applications.find(x => x.id === id); if (!a) throw new Error('Application not found'); a.status = status; this.state.notifications.unshift({ id: `note-${Date.now()}`, title: 'Application status updated', body: `${a.candidateName} is now marked ${status}.`, createdAt: new Date().toISOString().slice(0,10) }); this.persist(); return structuredClone(a); }
  async listNotifications() { return structuredClone(this.state.notifications); }
  async markNotificationRead(id: string) { const n = this.state.notifications.find(x => x.id === id); if (n) n.readAt = new Date().toISOString(); this.persist(); }
  async resetDemo() { this.state = defaultState(); this.persist(); }
}
