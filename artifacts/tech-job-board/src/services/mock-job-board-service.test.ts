import { describe, expect, it, beforeEach } from 'vitest';
import { MockJobBoardService } from './mock-job-board-service';

describe('MockJobBoardService', () => {
  let service: MockJobBoardService;
  beforeEach(() => { service = new MockJobBoardService(); });
  it('searches and filters published jobs', async () => {
    expect((await service.listJobs({ keyword: 'platform' })).map(j => j.id)).toContain('job-platform');
    expect((await service.listJobs({ remotePolicy: 'Remote', salaryMin: 180000 })).map(j => j.id)).toEqual(['job-data']);
  });
  it('persists saved jobs through storage', async () => {
    const data = new Map<string, string>();
    const store = { getItem: (k: string) => data.get(k) ?? null, setItem: (k: string, v: string) => data.set(k,v) } as Storage;
    const first = new MockJobBoardService(store);
    await first.saveJob('job-platform');
    const second = new MockJobBoardService(store);
    expect((await second.listSavedJobs()).map(j => j.id)).toContain('job-platform');
  });
  it('persists candidate CVs and the default selection through storage', async () => {
    const data = new Map<string, string>();
    const store = { getItem: (k: string) => data.get(k) ?? null, setItem: (k: string, v: string) => data.set(k, v) } as Storage;
    const first = new MockJobBoardService(store);
    await first.updateProfile({ cvFiles: ['Maya-Chen-Resume.pdf', 'Platform-Resume.pdf'], defaultCvId: 'Platform-Resume.pdf' });
    const second = new MockJobBoardService(store);
    await expect(second.getProfile()).resolves.toMatchObject({ cvFiles: ['Maya-Chen-Resume.pdf', 'Platform-Resume.pdf'], defaultCvId: 'Platform-Resume.pdf' });
  });
  it('supports mock registration and verification without storing a password', async () => {
    const data = new Map<string, string>();
    const store = { getItem: (k: string) => data.get(k) ?? null, setItem: (k: string, v: string) => data.set(k, v) } as Storage;
    const service = new MockJobBoardService(store);
    const user = await service.registerAccount({ name: 'Taylor Reed', email: 'taylor@example.com', password: 'demo-password-123', role: 'company' });
    expect(user).toMatchObject({ name: 'Taylor Reed', role: 'company', emailVerified: false });
    expect([...data.values()].join(' ')).not.toContain('demo-password-123');
    await expect(service.verifyEmail()).resolves.toMatchObject({ emailVerified: true });
    await expect(service.requestPasswordReset('taylor@example.com')).resolves.toBeUndefined();
  });
  it('prevents duplicate applications and supports status updates', async () => {
    await expect(service.submitApplication({ jobId: 'job-platform', candidateName: 'Maya Chen', candidateEmail: 'maya.chen@example.com', cvName: 'cv.pdf', coverLetter: '' })).resolves.toMatchObject({ status: 'Applied' });
    await expect(service.submitApplication({ jobId: 'job-platform', candidateName: 'Maya Chen', candidateEmail: 'maya.chen@example.com', cvName: 'cv.pdf', coverLetter: '' })).rejects.toThrow('already applied');
    const app = (await service.listApplicants('job-product'))[0];
    await expect(service.updateApplicationStatus(app.id, 'Shortlisted')).resolves.toMatchObject({ status: 'Shortlisted' });
  });
  it('accepts guest applications without adding them to the candidate tracker', async () => {
    const input = { jobId: 'job-fullstack', candidateName: 'Guest Candidate', candidateEmail: 'guest@example.com', cvName: 'guest-resume.pdf', coverLetter: '', isGuest: true };
    const application = await service.submitApplication(input);
    expect(application.candidateId).toBeUndefined();
    expect((await service.listApplications()).some(item => item.id === application.id)).toBe(false);
    await expect(service.submitApplication(input)).rejects.toThrow('already applied');
  });
  it('supports create, publish, close and reopen lifecycle', async () => {
    const job = await service.createJob({ title: 'Systems Engineer', skills: ['Go'] });
    expect(job.status).toBe('Draft');
    await service.setJobStatus(job.id, 'Published');
    expect((await service.listJobs({ keyword: 'Systems' })).some((published) => published.id === job.id)).toBe(true);
    await service.setJobStatus(job.id, 'Closed');
    expect((await service.listJobs({ keyword: 'Systems' })).some((published) => published.id === job.id)).toBe(false);
    await service.setJobStatus(job.id, 'Published');
    expect((await service.getJob(job.id))?.status).toBe('Published');
  });
});
