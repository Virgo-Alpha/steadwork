import { useEffect, useState, type CSSProperties, type FormEvent, type ReactNode } from 'react';
import { Link, Route, Switch, useLocation, useParams, Router as WouterRouter } from 'wouter';
import { ArrowDownUp, ArrowLeft, ArrowRight, Bell, Bookmark, BriefcaseBusiness, Check, CircleUserRound, ClipboardList, ExternalLink, Filter, MapPin, Search, Sparkles, TrendingUp, Users, X } from 'lucide-react';
import { jobBoardService as service } from '@/services';
import { hasSessionToken } from '@/services/session';
import type { Application, ApplicationStatus, CandidateProfile, Job, JobFilters, JobStatus, Notification, User } from '@/domain/types';

function useLoad<T>(loader: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);
  const reload = () => setTick(t => t + 1);
  useEffect(() => { let live = true; setLoading(true); loader().then(x => { if (live) { setData(x); setError(''); } }).catch(e => { if (live) setError(e instanceof Error ? e.message : 'Something went wrong'); }).finally(() => live && setLoading(false)); return () => { live = false; }; // loader is intentionally refreshed by route/tick
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);
  return { data, error, loading, reload, setData };
}
function isEmployerRole(role: User['role'] | string) {
  return role === 'company' || role === 'recruiter' || role === 'admin';
}
function Notice({ text, close }: { text: string; close: () => void }) {
  if (!text) return null;
  return <div className="toast-note" role="status" data-testid="status-feedback" style={{ position: 'fixed', zIndex: 50, right: 20, bottom: 20, maxWidth: 360, display: 'flex', gap: 12, alignItems: 'center', background: 'hsl(var(--foreground))', color: 'hsl(var(--background))', padding: '13px 16px', borderRadius: 9, boxShadow: '0 14px 40px #18233330' }}>{text}<button data-testid="button-dismiss-feedback" onClick={close} aria-label="Dismiss"><X size={15}/></button></div>;
}
function AppShell({ children }: { children: ReactNode }) {
  const [path, setLocation] = useLocation();
  const user = useLoad<User | null>(() => hasSessionToken() ? service.getCurrentUser() : Promise.resolve(null), [path]);
  const [toast, setToast] = useState('');
  const [role, setRole] = useState<'candidate' | 'company'>('candidate');
  const mockMode = import.meta.env.VITE_DATA_MODE === 'mock';
  useEffect(() => { user.data && setRole(isEmployerRole(user.data.role) ? 'company' : 'candidate'); }, [user.data]);
  useEffect(() => {
    const onUnauthorized = () => {
      if (!['/login', '/register', '/forgot-password', '/verify-email'].includes(path)) setLocation(`/login?returnTo=${encodeURIComponent(path)}`);
    };
    window.addEventListener('steadwork:unauthorized', onUnauthorized);
    return () => window.removeEventListener('steadwork:unauthorized', onUnauthorized);
  }, [path, setLocation]);
  const updateRole = async (next: 'candidate' | 'company') => {
    try {
      const updated = await service.switchRole(next);
      user.setData(updated);
      setRole(next);
      setToast(`Demo switched to ${next === 'company' ? 'hiring team' : 'candidate'} view`);
    } catch (reason) {
      setToast(reason instanceof Error ? reason.message : 'Unable to switch role.');
    }
  };
  const nav = [
    { href: '/', label: 'Find roles', icon: Search }, { href: '/saved', label: 'Saved', icon: Bookmark },
    { href: '/applications', label: 'Applications', icon: ClipboardList }, { href: '/profile', label: 'My profile', icon: CircleUserRound },
  ];
  return <div className="app-shell">
    <header className="topbar">
      <div className="main-wrap" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 24 }}>
        <Link href="/" data-testid="link-brand" style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
          <span className="brand-mark">S</span><span style={{ fontFamily: 'var(--app-font-serif)', fontSize: 19, fontWeight: 800, letterSpacing: '-.06em' }}>steadwork<span style={{ color: 'hsl(var(--primary))' }}>.</span></span>
        </Link>
        <nav className="desktop-nav" style={{ display: 'flex', alignItems: 'center', gap: 28, flex: 1, marginLeft: 28 }}>
          {nav.map(({ href, label }) => <Link key={href} href={href} className={`nav-link ${path === href ? 'active' : ''}`} data-testid={`nav-${label.toLowerCase().replaceAll(' ', '-')}`} style={{ fontSize: 13, fontWeight: path === href ? 700 : 500 }}>{label}</Link>)}
          {role === 'company' && <><Link href="/employer" className={`nav-link ${path === '/employer' ? 'active' : ''}`} data-testid="nav-employer" style={{ fontSize: 13, fontWeight: 600 }}>Hiring overview</Link><Link href="/employer/jobs" className={`nav-link ${path.startsWith('/employer/jobs') ? 'active' : ''}`} data-testid="nav-manage-jobs" style={{ fontSize: 13 }}>Manage roles</Link></>}
        </nav>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div className="auth-links" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {hasSessionToken() ? <><span className="nav-link" data-testid="label-current-user" style={{ fontSize: 12 }}>{user.data?.name || user.data?.email || 'Account'}</span><button className="nav-link" data-testid="button-sign-out" onClick={async () => { await service.logout(); setLocation('/login'); }}>Sign out</button></> : <><Link href="/login" className="nav-link" data-testid="link-sign-in" style={{ fontSize: 12 }}>Sign in</Link><Link href="/register" className="btn btn-primary" data-testid="link-create-account" style={{ minHeight: 36, padding: '0 12px', fontSize: 11 }}>Create account</Link></>}
          </div>
          <Link href="/notifications" className="btn btn-quiet" data-testid="link-notifications" style={{ width: 38, height: 38, minHeight: 38, padding: 0 }} aria-label="Notifications"><Bell size={18}/></Link>
          {mockMode && <label className="role-switch" style={{ display: 'flex', alignItems: 'center', gap: 6, borderLeft: '1px solid hsl(var(--border))', paddingLeft: 12 }}>
            <span className="eyebrow" style={{ letterSpacing: '.04em', whiteSpace: 'nowrap' }}>Demo as</span>
            <select aria-label="Switch demo role" data-testid="select-demo-role" value={role} onChange={e => updateRole(e.target.value as 'candidate' | 'company')} style={{ border: 0, background: 'transparent', fontSize: 12, fontWeight: 700, color: 'hsl(var(--foreground))', outline: 'none' }}>
              <option value="candidate">Candidate</option><option value="company">Hiring team</option>
            </select>
          </label>}
        </div>
      </div>
      <div className="mobile-nav" style={{ display: 'none', borderTop: '1px solid hsl(var(--border))', justifyContent: 'space-around', padding: '9px 4px', background: 'hsl(var(--background))' }}>
        {[...nav.slice(0,3), nav[3], ...(role === 'company' ? [{ href: '/employer', label: 'Hiring', icon: BriefcaseBusiness }] : [])].map(({ href, label, icon: Icon }) => <Link key={href} href={href} className="nav-link" data-testid={`mobile-nav-${label}`} style={{ display: 'grid', justifyItems: 'center', fontSize: 10, gap: 3 }}><Icon size={17}/>{label}</Link>)}
        <Link href="/login" className="nav-link" data-testid="mobile-nav-account" style={{ display: 'grid', justifyItems: 'center', fontSize: 10, gap: 3 }}><CircleUserRound size={17}/>Account</Link>
      </div>
    </header>
    <main>{children}</main>
    <footer style={{ borderTop: '1px solid hsl(var(--border))', marginTop: 80, padding: '24px 0', color: 'hsl(var(--muted-foreground))', fontSize: 12 }}>
      <div className="main-wrap" style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}><span>steadwork — thoughtful work starts here.</span>{mockMode && <button className="nav-link" data-testid="button-reset-demo" onClick={async () => { try { await service.resetDemo(); setToast('Demo data restored to its starting point'); setLocation('/'); } catch (reason) { setToast(reason instanceof Error ? reason.message : 'Unable to reset demo data.'); } }}>Reset demo data</button>}</div>
    </footer>
    <Notice text={toast} close={() => setToast('')}/>
  </div>;
}
function ProtectedPage({ children, role }: { children: ReactNode; role?: 'candidate' | 'company' }) {
  const [path] = useLocation();
  const auth = useLoad<User | null>(() => hasSessionToken() ? service.getCurrentUser() : Promise.resolve(null));
  const returnTo = path.startsWith('/') && !path.startsWith('//') ? path : '/';
  if (!hasSessionToken()) return <div className="main-wrap page-enter" style={{ paddingTop: 55, maxWidth: 700 }}><div className="surface" style={{ padding: 32, textAlign: 'center' }}><h1 className="font-display">Sign in to continue</h1><p style={{ color: 'hsl(var(--muted-foreground))' }}>Sign in to see your account information and continue where you left off.</p><Link className="btn btn-primary" href={`/login?returnTo=${encodeURIComponent(returnTo)}`} data-testid="link-protected-sign-in">Sign in</Link></div></div>;
  if (auth.loading) return <div className="main-wrap" style={{ paddingTop: 45 }}><div className="surface skeleton" style={{ height: 180 }} aria-label="Checking your session"/></div>;
  if (auth.error || !auth.data) return <div className="main-wrap page-enter" style={{ paddingTop: 55, maxWidth: 700 }}><div className="surface" style={{ padding: 32, textAlign: 'center' }}><h1 className="font-display">Please sign in again</h1><p style={{ color: 'hsl(var(--muted-foreground))' }}>Your session is no longer valid. Sign in to continue.</p><Link className="btn btn-primary" href={`/login?returnTo=${encodeURIComponent(returnTo)}`} data-testid="link-expired-session-sign-in">Sign in</Link></div></div>;
  if ((role === 'candidate' && auth.data.role !== 'candidate') || (role === 'company' && !isEmployerRole(auth.data.role))) return <div className="main-wrap page-enter" style={{ paddingTop: 55, maxWidth: 700 }}><div className="surface" style={{ padding: 32, textAlign: 'center' }}><h1 className="font-display">You do not have access to this page</h1><p style={{ color: 'hsl(var(--muted-foreground))' }}>This area is for {role === 'candidate' ? 'candidate' : 'hiring team'} accounts.</p><Link href="/" className="btn btn-outline">Back to roles</Link></div></div>;
  return <>{children}</>;
}
function PageTitle({ kicker, title, subtitle, side }: { kicker?: string; title: string; subtitle?: string; side?: ReactNode }) {
  return <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'end', gap: 18, flexWrap: 'wrap', marginBottom: 28 }}><div>{kicker && <div className="eyebrow" style={{ marginBottom: 10 }}>{kicker}</div>}<h1 className="font-display" style={{ fontSize: 'clamp(30px, 4vw, 42px)', lineHeight: 1.08, letterSpacing: '-.055em', margin: 0 }}>{title}</h1>{subtitle && <p style={{ color: 'hsl(var(--muted-foreground))', margin: '10px 0 0', fontSize: 14 }}>{subtitle}</p>}</div>{side}</div>;
}
function formatSalary(job: Job) { return `$${Math.round(job.salaryMin/1000)}k–$${Math.round(job.salaryMax/1000)}k`; }
function CompanyMark({ name, logo, accent }: { name: string; logo: string; accent: string }) {
  return <div aria-label={`${name} logo`} style={{ flex: '0 0 auto', width: 46, height: 46, display: 'grid', placeItems: 'center', borderRadius: 12, background: accent, color: 'hsl(var(--foreground))', fontFamily: 'var(--app-font-serif)', fontSize: 20, fontWeight: 800 }}>{logo}</div>;
}
function JobCard({ job, saved = false, onSave }: { job: Job; saved?: boolean; onSave?: (id: string) => void }) {
  const company = useLoad(() => service.getCompany(job.companyId), [job.companyId]);
  return <article className="surface job-row" data-testid={`card-job-${job.id}`} style={{ padding: '19px 20px', display: 'grid', gridTemplateColumns: 'auto 1fr auto', gap: 15, alignItems: 'start' }}>
    <CompanyMark name={company.data?.name || 'Company'} logo={company.data?.logo || '?'} accent={company.data?.accent || '#e2e7e0'}/>
    <div style={{ minWidth: 0 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 9, flexWrap: 'wrap' }}>
        <Link href={`/jobs/${job.id}`} data-testid={`link-job-${job.id}`} style={{ fontFamily: 'var(--app-font-serif)', fontWeight: 800, fontSize: 17, letterSpacing: '-.025em' }}>{job.title}</Link>
        <span className="tag">{job.remotePolicy}</span>
      </div>
      <div style={{ color: 'hsl(var(--muted-foreground))', fontSize: 12, marginTop: 5 }}>{company.error ? <span role="alert">{company.error}</span> : company.data?.name || 'Loading company'} <span style={{ margin: '0 5px' }}>·</span> {job.location} <span style={{ margin: '0 5px' }}>·</span> {job.jobType}</div>
      <div style={{ color: 'hsl(var(--foreground))', fontSize: 12, fontWeight: 700, marginTop: 11 }}>{formatSalary(job)} <span style={{ color: 'hsl(var(--muted-foreground))', fontWeight: 500 }}>· {job.experienceLevel} level</span></div>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 12 }}>{job.skills.slice(0,4).map(skill => <span key={skill} className="tag">{skill}</span>)}</div>
    </div>
    <div style={{ display: 'grid', justifyItems: 'end', gap: 14 }}>
      {onSave && <button aria-label={saved ? 'Remove saved job' : 'Save job'} data-testid={`button-save-${job.id}`} className="btn btn-quiet" onClick={() => onSave(job.id)} style={{ padding: 4, minHeight: 30, color: saved ? 'hsl(var(--primary))' : 'hsl(var(--muted-foreground))' }}><Bookmark size={18} fill={saved ? 'currentColor' : 'none'}/></button>}
      <span className="font-mono" style={{ color: 'hsl(var(--muted-foreground))', fontSize: 10 }}>{new Date(job.postedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
    </div>
  </article>;
}
function HomePage() {
  const [, setLocation] = useLocation();
  const [form, setForm] = useState<JobFilters>({ sort: 'recent' });
  const [draftKeyword, setDraftKeyword] = useState('');
  const [skillsText, setSkillsText] = useState('');
  const [savedIds, setSavedIds] = useState<string[]>([]);
  const [error, setError] = useState('');
  const mockMode = import.meta.env.VITE_DATA_MODE === 'mock';
  const { data: currentUser } = useLoad(() => mockMode || hasSessionToken() ? service.getCurrentUser() : Promise.resolve(null));
  const canUseCandidateFeatures = mockMode ? currentUser?.role !== 'company' : !hasSessionToken() || currentUser?.role === 'candidate';
  const { data: jobs, loading, reload } = useLoad(() => service.listJobs(form), [JSON.stringify(form)]);
  const { data: saved, error: savedError, reload: reloadSaved } = useLoad(() => (mockMode || hasSessionToken()) && canUseCandidateFeatures ? service.listSavedJobs() : Promise.resolve([]), [canUseCandidateFeatures]);
  const { data: recommended, error: recommendationError, reload: reloadRecommendations } = useLoad(() => (mockMode || hasSessionToken() && currentUser?.role === 'candidate') ? service.recommendJobs() : Promise.resolve([]), [currentUser?.role]);
  const { data: companies } = useLoad(() => service.listCompanies());
  useEffect(() => setSavedIds(saved?.map(x => x.id) || []), [saved]);
  const change = (key: keyof JobFilters, value: string) => setForm(prev => ({ ...prev, [key]: value || undefined }));
  const searchSubmit = (e: FormEvent) => { e.preventDefault(); setForm(prev => ({ ...prev, keyword: draftKeyword || undefined, skills: skillsText.split(',').map(s => s.trim()).filter(Boolean) })); };
  const save = async (id: string) => { if (!hasSessionToken()) { setLocation(`/login?returnTo=${encodeURIComponent(window.location.pathname)}`); return; } try { if (savedIds.includes(id)) { await service.unsaveJob(id); setSavedIds(x => x.filter(i => i !== id)); } else { await service.saveJob(id); setSavedIds(x => [...x, id]); } } catch(e) { setError(e instanceof Error ? e.message : 'Could not update saved jobs'); } };
  return <div className="main-wrap page-enter" style={{ paddingTop: 34 }}>
    <section style={{ position: 'relative', overflow: 'hidden', borderRadius: 18, padding: '38px clamp(24px, 5vw, 56px)', color: 'hsl(42 34% 96%)', background: 'hsl(215 33% 19%)', marginBottom: 34 }}>
      <div style={{ position: 'absolute', right: '-5%', top: '-70%', width: 430, height: 430, border: '1px solid hsl(158 42% 58% / .28)', borderRadius: '50%' }}></div><div style={{ position: 'absolute', right: '7%', top: '-35%', width: 300, height: 300, border: '1px solid hsl(158 42% 58% / .22)', borderRadius: '50%' }}></div>
      <div className="eyebrow" style={{ color: 'hsl(158 42% 68%)' }}>A better way to find your next</div>
      <h1 className="font-display" style={{ maxWidth: 680, fontSize: 'clamp(36px, 6vw, 59px)', lineHeight: 1.02, letterSpacing: '-.06em', margin: '15px 0 13px' }}>Work that fits.<br/><span style={{ color: 'hsl(158 42% 68%)' }}>People who get it.</span></h1>
      <p style={{ fontSize: 14, lineHeight: 1.7, color: 'hsl(42 20% 82%)', maxWidth: 450, margin: '0 0 26px' }}>A considered collection of technology roles from teams who care how work gets done.</p>
      <form className="hero-search" onSubmit={searchSubmit} style={{ position: 'relative', zIndex: 1, background: 'hsl(var(--card))', borderRadius: 10, padding: 8, display: 'grid', gap: 8, maxWidth: 800 }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: 9, padding: '0 10px', color: 'hsl(var(--muted-foreground))' }}><Search size={17}/><input aria-label="Search job titles and skills" data-testid="input-keyword" className="field" style={{ border: 0, boxShadow: 'none', paddingLeft: 0 }} placeholder="Role, company or skill" value={draftKeyword} onChange={e => setDraftKeyword(e.target.value)}/></label>
        <label style={{ display: 'flex', alignItems: 'center', gap: 9, padding: '0 10px', color: 'hsl(var(--muted-foreground))', borderLeft: '1px solid hsl(var(--border))' }}><MapPin size={17}/><input aria-label="Location" data-testid="input-location" className="field" style={{ border: 0, boxShadow: 'none', paddingLeft: 0 }} placeholder="City or remote" value={form.location || ''} onChange={e => change('location', e.target.value)}/></label>
        <button className="btn btn-primary" data-testid="button-search-jobs"><Search size={15}/> Find roles</button>
      </form>
      <div style={{ marginTop: 13, fontSize: 11, color: 'hsl(42 20% 78%)' }}>Thoughtful work. Clear expectations. No endless scroll.</div>
    </section>
    <section className="discovery-grid" style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 270px', gap: 27, alignItems: 'start' }}>
      <div>
        <PageTitle kicker="The shortlist" title="Roles worth a closer look" subtitle={`${jobs?.length ?? 0} open positions from teams building with care.`} side={<label style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 12, color: 'hsl(var(--muted-foreground))' }}><ArrowDownUp size={15}/><select aria-label="Sort jobs" data-testid="select-sort" className="field" style={{ width: 145, minHeight: 36, padding: '6px 8px' }} value={form.sort || 'recent'} onChange={e => change('sort', e.target.value)}><option value="recent">Most recent</option><option value="salary">Salary: high first</option></select></label>}/>
        {error && <ErrorState message={error} retry={() => setError('')}/>}
        {savedError && <ErrorState message={savedError} retry={reloadSaved}/>}
        {loading ? <JobSkeleton/> : jobs?.length ? <div style={{ display: 'grid', gap: 12 }}>{jobs.map(job => <JobCard key={job.id} job={job} saved={savedIds.includes(job.id)} onSave={canUseCandidateFeatures ? save : undefined}/>)}</div> : <EmptyState title="No roles match just yet" body="Try widening your filters or removing a skill to see more possibilities." action={<button className="btn btn-outline" onClick={() => { setForm({ sort: 'recent' }); setDraftKeyword(''); setSkillsText(''); }}>Clear all filters</button>}/>}
      </div>
      <aside style={{ display: 'grid', gap: 16 }}>
        <div className="surface" style={{ padding: 17 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}><Filter size={16} color="hsl(var(--primary))"/><strong style={{ fontSize: 14 }}>Narrow your search</strong></div>
          <div style={{ display: 'grid', gap: 13 }}>
            <FilterSelect label="Job type" test="filter-job-type" value={form.jobType || ''} onChange={v => change('jobType', v)} options={['Full-time','Part-time','Contract','Internship']}/>
            <FilterSelect label="Work style" test="filter-remote" value={form.remotePolicy || ''} onChange={v => change('remotePolicy', v)} options={['Remote','Hybrid','On-site']}/>
            <FilterSelect label="Experience" test="filter-experience" value={form.experienceLevel || ''} onChange={v => change('experienceLevel', v)} options={['Entry','Mid','Senior','Lead']}/>
            <FilterSelect label="Company" test="filter-company" value={form.companyId || ''} onChange={v => change('companyId', v)} options={(companies || []).map(c => c.name)} values={(companies || []).map(c => c.id)}/>
            <label style={{ display: 'grid', gap: 5, fontSize: 11, fontWeight: 700 }}>Minimum salary<input type="number" min="0" className="field" data-testid="filter-salary" placeholder="$100,000+" value={form.salaryMin || ''} onChange={e => setForm(p => ({ ...p, salaryMin: Number(e.target.value) || undefined }))}/></label>
            <label style={{ display: 'grid', gap: 5, fontSize: 11, fontWeight: 700 }}>Posted within<select className="field" data-testid="filter-date" value={form.postedWithin || ''} onChange={e => setForm(p => ({ ...p, postedWithin: Number(e.target.value) || undefined }))}><option value="">Any time</option><option value="7">Past week</option><option value="30">Past month</option></select></label>
            <label style={{ display: 'grid', gap: 5, fontSize: 11, fontWeight: 700 }}>Skills (comma separated)<input className="field" data-testid="filter-skills" placeholder="React, Python" value={skillsText} onChange={e => setSkillsText(e.target.value)} onBlur={() => setForm(p => ({ ...p, skills: skillsText.split(',').map(s => s.trim()).filter(Boolean) }))}/></label>
            <button className="btn btn-outline" data-testid="button-apply-filters" onClick={() => setForm(p => ({ ...p, skills: skillsText.split(',').map(s => s.trim()).filter(Boolean) }))}>Apply filters <ArrowRight size={14}/></button>
          </div>
        </div>
        {((mockMode && canUseCandidateFeatures) || hasSessionToken() && currentUser?.role === 'candidate') && <div className="surface" style={{ padding: 17, background: 'hsl(158 37% 92%)', borderColor: 'hsl(158 25% 82%)' }}>
          <div className="eyebrow" style={{ display: 'flex', alignItems: 'center', gap: 6 }}><Sparkles size={13}/> Picked for you</div>
          <p style={{ fontFamily: 'var(--app-font-serif)', fontWeight: 800, margin: '7px 0 12px' }}>A few good fits</p>
          {recommendationError ? <ErrorState message={recommendationError} retry={reloadRecommendations}/> : <>{(recommended || []).slice(0,2).map(j => <Link href={`/jobs/${j.id}`} key={j.id} data-testid={`recommend-${j.id}`} style={{ display: 'block', fontSize: 12, padding: '9px 0', borderTop: '1px solid hsl(158 25% 82%)' }}>{j.title}<span style={{ display: 'block', fontSize: 10, marginTop: 4, color: 'hsl(var(--muted-foreground))' }}>{j.skills.slice(0,2).join(' · ')}</span></Link>)}{!recommended?.length && <small>Add skills to your profile for tailored recommendations.</small>}</>}
        </div>}
      </aside>
    </section>
  </div>;
}
function FilterSelect({ label, test, value, onChange, options, values }: { label: string; test: string; value: string; onChange: (v: string) => void; options: string[]; values?: string[] }) {
  return <label style={{ display: 'grid', gap: 5, fontSize: 11, fontWeight: 700 }}>{label}<select className="field" data-testid={test} value={value} onChange={e => onChange(e.target.value)}><option value="">Any</option>{options.map((o,i) => <option key={o} value={values?.[i] || o}>{o}</option>)}</select></label>;
}
function JobSkeleton() { return <div style={{ display: 'grid', gap: 12 }} aria-label="Loading roles">{[1,2,3].map(x => <div key={x} className="surface" style={{ height: 145, padding: 20, display: 'flex', gap: 14 }}><div className="skeleton" style={{ width: 46, height: 46, borderRadius: 12 }}/><div style={{ flex: 1 }}><div className="skeleton" style={{ height: 17, width: '45%', borderRadius: 5 }}/><div className="skeleton" style={{ height: 12, width: '30%', borderRadius: 5, marginTop: 12 }}/><div className="skeleton" style={{ height: 12, width: '65%', borderRadius: 5, marginTop: 20 }}/></div></div>)}</div>; }
function EmptyState({ title, body, action }: { title: string; body: string; action?: ReactNode }) { return <div className="surface" style={{ textAlign: 'center', padding: '44px 24px', borderStyle: 'dashed' }}><div style={{ margin: '0 auto 13px', width: 44, height: 44, display: 'grid', placeItems: 'center', borderRadius: '50%', background: 'hsl(var(--secondary))', color: 'hsl(var(--primary))' }}><Search size={19}/></div><h3 className="font-display" style={{ margin: 0, fontSize: 20 }}>{title}</h3><p style={{ color: 'hsl(var(--muted-foreground))', fontSize: 13, margin: '8px auto 18px', maxWidth: 400 }}>{body}</p>{action}</div>; }
function ErrorState({ message, retry }: { message: string; retry: () => void }) { return <div role="alert" className="surface" style={{ padding: 18, borderColor: 'hsl(var(--destructive) / .4)', color: 'hsl(var(--destructive))' }}>{message} <button className="btn btn-outline" onClick={retry} style={{ marginLeft: 10 }}>Try again</button></div>; }
function JobDetailPage() {
  const { id = '' } = useParams();
  const [, setLocation] = useLocation();
  const mockMode = import.meta.env.VITE_DATA_MODE === 'mock';
  const { data: job, loading, reload } = useLoad(() => service.getJob(id), [id]);
  const { data: user } = useLoad(() => hasSessionToken() || mockMode ? service.getCurrentUser() : Promise.resolve(null));
  const { data: profile } = useLoad(() => user?.role === 'candidate' ? service.getProfile() : Promise.resolve(null), [user?.role]);
  const [company, setCompany] = useState<{ name: string; description: string; website: string; logo: string; accent: string } | null>(null);
  const [saved, setSaved] = useState(false);
  const [applyOpen, setApplyOpen] = useState(false);
  const [applyAsGuest, setApplyAsGuest] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [err, setErr] = useState('');
  useEffect(() => { if (job) service.getCompany(job.companyId).then(c => c && setCompany(c)).catch(reason => setFeedback(reason instanceof Error ? reason.message : 'Could not load company details.')); }, [job]);
  useEffect(() => {
    if (user?.role !== 'candidate') return;
    service.listSavedJobs().then(xs => setSaved(xs.some(x => x.id === id))).catch(reason => setFeedback(reason instanceof Error ? reason.message : 'Could not load saved roles.'));
  }, [id, user?.role]);
  if (loading) return <div className="main-wrap" style={{ paddingTop: 50 }}><JobSkeleton/></div>;
  if (!job) return <div className="main-wrap page-enter" style={{ paddingTop: 50 }}><EmptyState title="This role has moved on" body="The listing may have closed or the link may be out of date." action={<Link className="btn btn-primary" href="/">Browse open roles</Link>}/></div>;
  const toggleSaved = async () => { if (!hasSessionToken() && !mockMode) { setLocation(`/login?returnTo=${encodeURIComponent(`/jobs/${id}`)}`); return; } try { if (saved) await service.unsaveJob(id); else await service.saveJob(id); setSaved(!saved); setFeedback(saved ? 'Removed from your saved roles' : 'Saved for later'); } catch (reason) { setFeedback(reason instanceof Error ? reason.message : 'Could not update saved roles.'); } };
  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault(); const form = new FormData(e.currentTarget);
    try {
      if (job.applicationMethod === 'External' && job.externalApplyUrl) window.open(job.externalApplyUrl, '_blank', 'noopener,noreferrer');
      await service.submitApplication({ jobId: job.id, candidateName: String(form.get('name')), candidateEmail: String(form.get('email')), cvName: String(form.get('cv')), coverLetter: String(form.get('cover')), isGuest: applyAsGuest });
      setApplyOpen(false); setFeedback(job.applicationMethod === 'External' ? 'Application click recorded. Continue on the company site.' : 'Your application is in. You can track it in Applications.');
    } catch (e) { setErr(e instanceof Error ? e.message : 'Could not submit application'); }
  };
  const companyInfo = company || { name: 'Loading company', description: '', website: '', logo: '?', accent: '#eee' };
  return <div className="main-wrap page-enter" style={{ paddingTop: 34 }}>
    <Link href="/" className="nav-link" data-testid="link-back-to-search" style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 12, marginBottom: 22 }}><ArrowLeft size={15}/> All roles</Link>
    <section className="surface" style={{ padding: 'clamp(22px, 4vw, 38px)', display: 'grid', gridTemplateColumns: '1fr auto', gap: 24, alignItems: 'start' }}>
      <div>
        <div style={{ display: 'flex', gap: 15, alignItems: 'center', marginBottom: 23 }}><CompanyMark name={companyInfo.name} logo={companyInfo.logo} accent={companyInfo.accent}/><div><div className="eyebrow">{companyInfo.name}</div><div style={{ fontSize: 12, color: 'hsl(var(--muted-foreground))', marginTop: 4 }}>{companyInfo.website}</div></div></div>
        <div className="eyebrow">Open role · {job.experienceLevel}</div><h1 className="font-display" data-testid="text-job-title" style={{ fontSize: 'clamp(34px, 5vw, 52px)', lineHeight: 1.03, letterSpacing: '-.06em', margin: '10px 0 12px' }}>{job.title}</h1>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', color: 'hsl(var(--muted-foreground))', fontSize: 12 }}><span>{job.location}</span><span>·</span><span>{job.remotePolicy}</span><span>·</span><span>{job.jobType}</span><span>·</span><span>{formatSalary(job)}</span></div>
      </div>
      <div style={{ display: 'flex', gap: 9, flexWrap: 'wrap' }}>{(!hasSessionToken() && !mockMode || user?.role === 'candidate') && <button className="btn btn-outline" data-testid="button-detail-save" onClick={toggleSaved}><Bookmark size={15} fill={saved ? 'currentColor' : 'none'}/>{saved ? 'Saved' : 'Save role'}</button>}<button className="btn btn-primary" data-testid="button-open-application" onClick={() => { setApplyAsGuest(isEmployerRole(user?.role || '')); setApplyOpen(true); }}>Apply now <ArrowRight size={15}/></button></div>
    </section>
    {feedback && <div className="surface" role="status" data-testid="status-application-feedback" style={{ padding: 13, marginTop: 12, color: 'hsl(var(--primary))' }}>{feedback}</div>}
    {err && <ErrorState message={err} retry={() => setErr('')}/>}
    <div className="detail-layout" style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) 280px', gap: 28, marginTop: 27 }}>
      <article style={{ display: 'grid', gap: 24, alignContent: 'start' }}>
        <InfoSection title="The opportunity"><p>{job.description}</p></InfoSection>
        <InfoSection title="What you'll work on"><ul>{job.responsibilities.map(x => <li key={x}>{x}</li>)}</ul></InfoSection>
        <InfoSection title="What you bring"><ul>{job.qualifications.map(x => <li key={x}>{x}</li>)}</ul></InfoSection>
        <InfoSection title="What the team offers"><div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>{job.benefits.map(x => <span className="tag" key={x}>{x}</span>)}</div></InfoSection>
      </article>
      <aside style={{ display: 'grid', alignContent: 'start', gap: 14 }}>
        <div className="surface" style={{ padding: 18 }}><div className="eyebrow">Good to know</div><h3 className="font-display" style={{ fontSize: 18, margin: '7px 0 14px' }}>Clear details, right up front.</h3><DetailLine label="Salary" value={formatSalary(job)}/><DetailLine label="Work style" value={job.remotePolicy}/><DetailLine label="Posted" value={new Date(job.postedAt).toLocaleDateString('en-US', { month: 'long', day: 'numeric' })}/><DetailLine label="Apply by" value={new Date(job.deadline).toLocaleDateString('en-US', { month: 'long', day: 'numeric' })}/></div>
        <div className="surface" style={{ padding: 18 }}><div className="eyebrow">Skills in the mix</div><div style={{ display: 'flex', flexWrap: 'wrap', gap: 7, marginTop: 13 }}>{job.skills.map(s => <span className="tag" key={s}>{s}</span>)}</div></div>
        <div className="surface" style={{ padding: 18, background: 'hsl(var(--secondary))' }}><strong style={{ fontSize: 13 }}>{companyInfo.name}</strong><p style={{ fontSize: 12, lineHeight: 1.6, color: 'hsl(var(--muted-foreground))' }}>{companyInfo.description}</p><a href={`https://${companyInfo.website}`} target="_blank" rel="noreferrer" className="nav-link" data-testid="link-company-website" style={{ display: 'inline-flex', gap: 6, alignItems: 'center', fontSize: 11 }}>Company website <ExternalLink size={13}/></a></div>
      </aside>
    </div>
    {applyOpen && <div role="dialog" aria-modal="true" aria-labelledby="apply-heading" style={modalBackdrop}><form className="surface" onSubmit={submit} style={{ width: 'min(520px, 100%)', padding: 24, display: 'grid', gap: 13, boxShadow: '0 22px 80px #18233338' }}><div style={{ display: 'flex', justifyContent: 'space-between' }}><div><div className="eyebrow">{job.applicationMethod === 'External' ? 'Track your interest' : 'A good next step'}</div><h2 id="apply-heading" className="font-display" style={{ margin: '5px 0', fontSize: 25 }}>Apply to {job.title}</h2></div><button type="button" className="btn btn-quiet" data-testid="button-close-application" onClick={() => setApplyOpen(false)}><X size={18}/></button></div>
      <label style={{ display: 'flex', gap: 9, alignItems: 'flex-start', fontSize: 12, color: 'hsl(var(--muted-foreground))' }}><input type="checkbox" data-testid="checkbox-guest-application" checked={applyAsGuest} onChange={e => setApplyAsGuest(e.target.checked)}/><span><strong>Apply as a guest</strong><br/>You’ll receive a confirmation, but won’t be able to track this application.</span></label><label className="form-label">Your name<input key={applyAsGuest ? 'guest-name' : 'candidate-name'} className="field" required name="name" defaultValue={applyAsGuest ? '' : user?.name || ''} data-testid="input-applicant-name"/></label><label className="form-label">Email address<input key={applyAsGuest ? 'guest-email' : 'candidate-email'} className="field" required type="email" name="email" defaultValue={applyAsGuest ? '' : user?.email || ''} data-testid="input-applicant-email"/></label><label className="form-label">Resume filename (metadata only)<select className="field" name="cv" data-testid="select-cv" defaultValue={profile?.defaultCvId || profile?.cvFiles[0] || ''}>{(profile?.cvFiles || []).map(cv => <option key={cv} value={cv}>{cv}</option>)}</select></label><label className="form-label">A note for the team (optional)<textarea className="field" rows={4} name="cover" placeholder="What caught your eye about this role?" data-testid="input-cover-letter"/></label><div style={{ display: 'flex', justifyContent: 'end', gap: 8 }}><button type="button" className="btn btn-outline" onClick={() => setApplyOpen(false)}>Not now</button><button className="btn btn-primary" data-testid="button-submit-application">{job.applicationMethod === 'External' ? 'Continue to company' : 'Send application'} <ArrowRight size={14}/></button></div>
    </form></div>}
  </div>;
}
function InfoSection({ title, children }: { title: string; children: ReactNode }) { return <section><h2 className="font-display" style={{ fontSize: 22, margin: '0 0 10px', letterSpacing: '-.04em' }}>{title}</h2><div style={{ color: 'hsl(var(--muted-foreground))', fontSize: 14, lineHeight: 1.75 }}>{children}</div></section>; }
function DetailLine({ label, value }: { label: string; value: string }) { return <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, borderTop: '1px solid hsl(var(--border))', padding: '10px 0', fontSize: 11 }}><span style={{ color: 'hsl(var(--muted-foreground))' }}>{label}</span><strong>{value}</strong></div>; }
const modalBackdrop: CSSProperties = { position: 'fixed', zIndex: 40, inset: 0, display: 'grid', placeItems: 'center', padding: 16, background: 'hsl(215 31% 12% / .48)' };
function SavedPage() {
  const { data, loading, error, reload } = useLoad(() => hasSessionToken() ? service.listSavedJobs() : Promise.resolve([]));
  const [saved, setSaved] = useState<Job[]>([]);
  const [notice, setNotice] = useState('');
  useEffect(() => setSaved(data || []), [data]);
  const remove = async (id: string) => { try { await service.unsaveJob(id); setSaved(x => x.filter(j => j.id !== id)); } catch (reason) { setNotice(reason instanceof Error ? reason.message : 'Could not remove saved role.'); } };
  return <div className="main-wrap page-enter" style={{ paddingTop: 42, maxWidth: 850 }}><PageTitle kicker="For later" title="Your saved roles" subtitle="Good possibilities, kept in one place."/>
    {notice && <div role="alert" style={{ marginBottom: 12, color: 'hsl(var(--destructive))', fontSize: 12 }}>{notice}</div>}
    {loading ? <JobSkeleton/> : error ? <ErrorState message={error} retry={reload}/> : saved.length ? <div style={{ display: 'grid', gap: 12 }}>{saved.map(j => <JobCard key={j.id} job={j} saved onSave={remove}/>)}</div> : <EmptyState title="Nothing saved yet" body="When a role catches your eye, save it here and come back when you're ready." action={<Link href="/" className="btn btn-primary">Explore roles <ArrowRight size={14}/></Link>}/>}
  </div>;
}
function ApplicationsPage() {
  const { data, loading, error, reload } = useLoad(() => service.listApplications());
  const [applications, setApplications] = useState<Application[]>([]);
  const [filter, setFilter] = useState('All');
  useEffect(() => setApplications(data || []), [data]);
  const withdraw = async (id: string) => { if (!window.confirm('Withdraw this application? This cannot be undone.')) return; try { const a = await service.withdrawApplication(id); setApplications(xs => xs.map(x => x.id === id ? a : x)); } catch(e) { window.alert(e instanceof Error ? e.message : 'Could not withdraw'); } };
  const filtered = applications.filter(a => filter === 'All' || a.status === filter);
  return <div className="main-wrap page-enter" style={{ paddingTop: 42, maxWidth: 950 }}><PageTitle kicker="Your search, organized" title="Application tracker" subtitle="A clear view of where things stand." side={<select className="field" style={{ width: 170 }} data-testid="filter-application-status" value={filter} onChange={e => setFilter(e.target.value)}><option>All</option>{['Applied','Under Review','Shortlisted','Rejected','Hired','Withdrawn','External click'].map(x => <option key={x}>{x}</option>)}</select>}/>
    {loading ? <div className="surface skeleton" style={{ height: 180 }}/> : error ? <ErrorState message={error} retry={reload}/> : filtered.length ? <div className="surface" style={{ overflow: 'hidden' }}>{filtered.map((a,i) => {
      return <ApplicationRow key={a.id} application={a} last={i === filtered.length - 1} onWithdraw={() => withdraw(a.id)}/>;
    })}</div> : <EmptyState title="A fresh page" body="Your applications will show up here when you apply. We'll keep every update easy to find." action={<Link className="btn btn-primary" href="/">Find a role <ArrowRight size={14}/></Link>}/>}
  </div>;
}
function ApplicationRow({ application, last, onWithdraw }: { application: Application; last: boolean; onWithdraw: () => void }) {
  const { data: job } = useLoad(() => service.getJob(application.jobId), [application.jobId]);
  const color = application.status === 'Shortlisted' || application.status === 'Hired' ? 'green' : application.status === 'Rejected' || application.status === 'Withdrawn' ? 'red' : application.status === 'Under Review' ? 'orange' : '';
  return <div data-testid={`row-application-${application.id}`} style={{ display: 'grid', gridTemplateColumns: '1fr auto', padding: '18px 20px', gap: 15, borderBottom: last ? 0 : '1px solid hsl(var(--border))', alignItems: 'center' }}><div><Link href={`/jobs/${application.jobId}`} style={{ fontFamily: 'var(--app-font-serif)', fontSize: 16, fontWeight: 800 }}>{job?.title || 'Role application'}</Link><div style={{ fontSize: 12, color: 'hsl(var(--muted-foreground))', marginTop: 5 }}>{application.candidateName} · {new Date(application.createdAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</div></div><div style={{ display: 'flex', alignItems: 'center', gap: 12 }}><span className={`status-pill ${color}`} data-testid={`status-application-${application.id}`}>{application.status}</span>{application.status !== 'Withdrawn' && application.status !== 'External click' && <button className="btn btn-quiet" data-testid={`button-withdraw-${application.id}`} onClick={onWithdraw} style={{ fontSize: 11 }}>Withdraw</button>}</div></div>;
}
function ProfilePage() {
  const { data, loading, error, reload } = useLoad(() => hasSessionToken() ? service.getProfile() : Promise.resolve(null));
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [message, setMessage] = useState('');
  useEffect(() => { data && setProfile(data); }, [data]);
  if (loading || !profile) return <div className="main-wrap" style={{ paddingTop: 45 }}><div className="surface skeleton" style={{ height: 360 }}/></div>;
  if (error) return <div className="main-wrap" style={{ paddingTop: 45 }}><ErrorState message={error} retry={reload}/></div>;
  const save = async (e: FormEvent) => { e.preventDefault(); try { await service.updateProfile(profile); setMessage('Profile saved — your recommendations now reflect these details.'); } catch { setMessage('We could not save your profile. Please try again.'); } };
  const setField = (key: keyof CandidateProfile, value: string | string[]) => setProfile(p => p ? { ...p, [key]: value } : p);
  const addCv = async (file: File | undefined) => {
    if (!file || profile.cvFiles.includes(file.name)) return;
    const cvFiles = [...profile.cvFiles, file.name];
    const defaultCvId = profile.defaultCvId || file.name;
    try {
      await service.updateProfile({ cvFiles, defaultCvId });
      setProfile(current => current ? { ...current, cvFiles, defaultCvId } : current);
      setMessage(`Added ${file.name} to the demo CV library. Only the filename is saved; file upload is not connected yet.`);
    } catch {
      setMessage('The CV could not be added. Please try again.');
    }
  };
  const removeCv = async (filename: string) => {
    const cvFiles = profile.cvFiles.filter(cv => cv !== filename);
    const defaultCvId = profile.defaultCvId === filename ? cvFiles[0] || '' : profile.defaultCvId;
    try {
      await service.updateProfile({ cvFiles, defaultCvId });
      setProfile(current => current ? { ...current, cvFiles, defaultCvId } : current);
      setMessage(`${filename} removed from the demo CV library.`);
    } catch {
      setMessage('The CV could not be removed. Please try again.');
    }
  };
  return <div className="main-wrap page-enter" style={{ paddingTop: 42, maxWidth: 830 }}><PageTitle kicker="Your foundation" title="A profile that grows with you" subtitle="Start with the essentials. Add detail as it becomes useful."/>
    <form className="surface" onSubmit={save} style={{ padding: 'clamp(20px, 4vw, 32px)', display: 'grid', gap: 17 }}>
      <label className="form-label">Professional headline<input className="field" data-testid="input-profile-headline" value={profile.headline} onChange={e => setField('headline', e.target.value)} placeholder="e.g. Product-minded engineer"/></label>
      <label className="form-label">Location<input className="field" data-testid="input-profile-location" value={profile.location} onChange={e => setField('location', e.target.value)}/></label>
      <label className="form-label">Skills <span style={{ fontWeight: 400, color: 'hsl(var(--muted-foreground))' }}>Separate with commas; used for recommendations.</span><input className="field" data-testid="input-profile-skills" value={profile.skills.join(', ')} onChange={e => setField('skills', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}/></label>
      <label className="form-label">Experience<textarea className="field" rows={4} data-testid="input-profile-experience" value={profile.experience} onChange={e => setField('experience', e.target.value)} placeholder="A few lines about the work you've done"/></label>
      <label className="form-label">Education<input className="field" data-testid="input-profile-education" value={profile.education} onChange={e => setField('education', e.target.value)}/></label>
      <label className="form-label">What you're looking for<textarea className="field" rows={3} data-testid="input-profile-preferences" value={profile.preferences} onChange={e => setField('preferences', e.target.value)} placeholder="Team, work style, or role preferences"/></label>
       <div><div className="form-label">CV filename library</div><div style={{ display: 'grid', gap: 8 }}>{profile.cvFiles.map(cv => <div key={cv} className="surface" style={{ padding: 11, display: 'flex', gap: 10, alignItems: 'center', fontSize: 12 }}><input type="radio" name="defaultcv" checked={profile.defaultCvId === cv} onChange={() => setField('defaultCvId', cv)} data-testid={`radio-default-cv-${cv}`}/><span style={{ flex: 1 }}>{cv}</span><span className="tag">{profile.defaultCvId === cv ? 'Default' : 'Choose default'}</span><button type="button" className="btn btn-quiet" aria-label={`Remove ${cv}`} data-testid={`button-remove-cv-${cv}`} onClick={() => removeCv(cv)}>Remove</button></div>)}</div><label className="btn btn-outline" style={{ width: 'fit-content', cursor: 'pointer', marginTop: 10 }}>Add a CV filename<input type="file" accept=".pdf,.doc,.docx" data-testid="input-add-cv" style={{ display: 'none' }} onChange={e => { const input = e.currentTarget; void addCv(input.files?.[0]).finally(() => { input.value = ''; }); }}/></label><div style={{ color: 'hsl(var(--muted-foreground))', fontSize: 11, marginTop: 8 }}>Metadata only: Steadwork saves the selected filename. The file is not uploaded, stored, or attached to applications.</div></div>
      {message && <div role="status" data-testid="status-profile-save" style={{ fontSize: 12, color: 'hsl(var(--primary))' }}>{message}</div>}
      <div style={{ display: 'flex', justifyContent: 'end' }}><button className="btn btn-primary" data-testid="button-save-profile"><Check size={15}/> Save profile</button></div>
    </form>
  </div>;
}
function EmployerPage() {
  const { data, loading, error, reload } = useLoad(() => service.getEmployerDashboard());
  const { data: jobs, error: jobsError, reload: reloadJobs } = useLoad(() => service.listCompanyJobs());
  return <div className="main-wrap page-enter" style={{ paddingTop: 42 }}>
    <PageTitle kicker={`${data?.companyName || 'Hiring team'} · hiring desk`} title="Make room for good people" subtitle="A clear picture of your open roles and the people behind each application." side={<Link href="/employer/jobs/new" className="btn btn-primary" data-testid="button-create-job"><span>+</span> Create a role</Link>}/>
    {loading ? <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>{[1,2,3,4].map(x => <div key={x} className="surface skeleton" style={{ height: 112 }}/>)}</div> : error ? <ErrorState message={error} retry={reload}/> : <>
      <div className="metrics-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0,1fr))', gap: 12, marginBottom: 28 }}>
        <Metric label="Live roles" value={data?.activeJobs ?? 0} icon={<BriefcaseBusiness size={17}/>}/><Metric label="All postings" value={data?.totalJobs ?? 0} icon={<TrendingUp size={17}/>}/><Metric label="Applications" value={data?.applications ?? 0} icon={<Users size={17}/>}/><Metric label="Shortlisted" value={data?.shortlisted ?? 0} icon={<Sparkles size={17}/>}/>
      </div>
      <div className="employer-layout" style={{ display: 'grid', gridTemplateColumns: '1.2fr .8fr', gap: 18 }}>
        <section className="surface" style={{ padding: 21 }}><div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}><div><div className="eyebrow">Your roles</div><h2 className="font-display" style={{ margin: '5px 0', fontSize: 23 }}>Open and in progress</h2></div><Link href="/employer/jobs" className="nav-link" data-testid="link-all-employer-jobs" style={{ fontSize: 12 }}>Manage all <ArrowRight size={13}/></Link></div>
          {jobsError ? <ErrorState message={jobsError} retry={reloadJobs}/> : (jobs || []).slice(0,4).map(j => <div key={j.id} style={{ display: 'grid', gridTemplateColumns: '1fr auto auto', gap: 12, alignItems: 'center', padding: '12px 0', borderTop: '1px solid hsl(var(--border))' }}><div><Link href={`/employer/jobs/${j.id}/applicants`} data-testid={`link-applicants-${j.id}`} style={{ fontSize: 13, fontWeight: 700 }}>{j.title}</Link><div style={{ fontSize: 11, color: 'hsl(var(--muted-foreground))', marginTop: 4 }}>{j.applicationCount} applicants</div></div><StatusPill value={j.status}/><Link href={`/employer/jobs/${j.id}/applicants`} className="btn btn-quiet" aria-label={`View applicants for ${j.title}`}><ArrowRight size={16}/></Link></div>)}
        </section>
        <section className="surface" style={{ padding: 21 }}><div className="eyebrow">Recent applications</div><h2 className="font-display" style={{ margin: '5px 0 14px', fontSize: 23 }}>People to meet</h2>
          {data?.recent.length ? data.recent.map(a => <div key={a.id} style={{ borderTop: '1px solid hsl(var(--border))', padding: '12px 0', display: 'flex', justifyContent: 'space-between', gap: 8 }}><div><strong style={{ fontSize: 12 }}>{a.candidateName}</strong><div style={{ fontSize: 10, color: 'hsl(var(--muted-foreground))', marginTop: 4 }}>{a.candidateEmail}</div></div><StatusPill value={a.status}/></div>) : <p style={{ color: 'hsl(var(--muted-foreground))', fontSize: 12 }}>New applications will show here.</p>}
        </section>
      </div>
      <div style={{ display: 'flex', gap: 10, marginTop: 20, flexWrap: 'wrap' }}><Link className="btn btn-outline" href="/employer/jobs">Manage job posts</Link><span style={{ color: 'hsl(var(--muted-foreground))', alignSelf: 'center', fontSize: 11 }}>A small, useful view. No vanity metrics.</span></div>
    </>}
  </div>;
}
function Metric({ label, value, icon }: { label: string; value: number; icon: ReactNode }) { return <div className="surface" style={{ padding: 17 }}><div style={{ display: 'flex', justifyContent: 'space-between', color: 'hsl(var(--muted-foreground))', fontSize: 11 }}>{label}<span style={{ color: 'hsl(var(--primary))' }}>{icon}</span></div><div className="font-display" data-testid={`metric-${label.toLowerCase().replace(' ', '-')}`} style={{ fontSize: 31, fontWeight: 800, marginTop: 9 }}>{value}</div></div>; }
function StatusPill({ value }: { value: string }) { const color = ['Published','Shortlisted','Hired'].includes(value) ? 'green' : ['Draft','Under Review'].includes(value) ? 'orange' : ['Closed','Rejected','Withdrawn'].includes(value) ? 'red' : ''; return <span className={`status-pill ${color}`}>{value}</span>; }
function EmployerJobsPage() {
  const { data, loading, error, reload } = useLoad(() => service.listCompanyJobs());
  const [jobs, setJobs] = useState<Job[]>([]);
  const [note, setNote] = useState('');
  useEffect(() => setJobs(data || []), [data]);
  const update = async (job: Job, status: JobStatus) => { try { const changed = await service.setJobStatus(job.id, status); setJobs(xs => xs.map(x => x.id === job.id ? changed : x)); setNote(`${job.title} is now ${status.toLowerCase()}.`); } catch (reason) { setNote(reason instanceof Error ? reason.message : 'Could not update role status.'); } };
  return <div className="main-wrap page-enter" style={{ paddingTop: 42, maxWidth: 1000 }}><PageTitle kicker="Hiring desk" title="Manage your roles" subtitle="Every listing, with its status and applicant count." side={<Link href="/employer/jobs/new" className="btn btn-primary" data-testid="button-create-job"><span>+</span> New role</Link>}/>
    {note && <div role="alert" style={{ marginBottom: 12, color: 'hsl(var(--primary))', fontSize: 12 }}>{note}</div>}
    {loading ? <div className="surface skeleton" style={{ height: 220 }}/> : error ? <ErrorState message={error} retry={reload}/> : jobs.length ? <div className="surface" style={{ overflow: 'hidden' }}>{jobs.map((job,i) => <div key={job.id} data-testid={`row-employer-job-${job.id}`} style={{ display: 'grid', gridTemplateColumns: '1fr auto auto', gap: 17, alignItems: 'center', padding: '17px 20px', borderBottom: i === jobs.length-1 ? 0 : '1px solid hsl(var(--border))' }}><div><Link href={`/employer/jobs/${job.id}/applicants`} style={{ fontFamily: 'var(--app-font-serif)', fontWeight: 800 }}>{job.title}</Link><div style={{ fontSize: 11, color: 'hsl(var(--muted-foreground))', marginTop: 5 }}>{job.location} · {job.applicationCount} applicants · Updated {job.postedAt}</div></div><StatusPill value={job.status}/><div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', justifyContent: 'end' }}><Link href={`/employer/jobs/new?id=${job.id}`} className="btn btn-outline" data-testid={`button-edit-job-${job.id}`} style={{ minHeight: 34, padding: '0 10px', fontSize: 11 }}>Edit</Link>{job.status === 'Draft' && <button className="btn btn-primary" data-testid={`button-publish-job-${job.id}`} style={{ minHeight: 34, padding: '0 10px', fontSize: 11 }} onClick={() => update(job,'Published')}>Publish</button>}{job.status === 'Published' && <button className="btn btn-outline" data-testid={`button-close-job-${job.id}`} style={{ minHeight: 34, padding: '0 10px', fontSize: 11 }} onClick={() => update(job,'Closed')}>Close</button>}{job.status === 'Closed' && <button className="btn btn-primary" data-testid={`button-reopen-job-${job.id}`} style={{ minHeight: 34, padding: '0 10px', fontSize: 11 }} onClick={() => update(job,'Published')}>Reopen</button>}<Link href={`/employer/jobs/${job.id}/applicants`} className="btn btn-quiet" data-testid={`button-review-applicants-${job.id}`} style={{ minHeight: 34, padding: '0 10px', fontSize: 11 }}>Applicants <ArrowRight size={13}/></Link></div></div>)}</div> : <EmptyState title="Your first role starts here" body="Add the details candidates need to decide if this is their next good fit." action={<Link className="btn btn-primary" href="/employer/jobs/new">Create a role</Link>}/>}
  </div>;
}
function JobEditorPage() {
  const params = useParams();
  const [, setLocation] = useLocation();
  const id = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '').get('id');
  const existing = useLoad(() => id ? service.getJob(id) : Promise.resolve(undefined), [id]);
  const [values, setValues] = useState<Partial<Job>>({ title: '', description: '', location: '', remotePolicy: 'Hybrid', jobType: 'Full-time', salaryMin: 130000, salaryMax: 170000, experienceLevel: 'Mid', skills: [], responsibilities: [], qualifications: [], benefits: [], applicationMethod: 'Internal', deadline: '2026-07-31', status: 'Draft' });
  const [message, setMessage] = useState('');
  useEffect(() => { if (existing.data) setValues(existing.data); }, [existing.data]);
  void params;
  const set = (key: keyof Job, v: string) => setValues(p => ({ ...p, [key]: ['salaryMin','salaryMax'].includes(key) ? Number(v) : v }));
  const submit = async (e: FormEvent) => { e.preventDefault(); try { const payload = { ...values, skills: String(values.skills || []).length ? values.skills : [], responsibilities: values.responsibilities || [], qualifications: values.qualifications || [], benefits: values.benefits || [] }; if (id) await service.updateJob(id, payload); else await service.createJob(payload); setMessage('Role saved as a draft.'); setTimeout(() => setLocation('/employer/jobs'), 550); } catch(e) { setMessage(e instanceof Error ? e.message : 'Could not save role'); } };
  const list = (key: 'skills' | 'responsibilities' | 'qualifications' | 'benefits') => Array.isArray(values[key]) ? (values[key] as string[]).join(', ') : '';
  const setList = (key: 'skills' | 'responsibilities' | 'qualifications' | 'benefits', v: string) => setValues(p => ({ ...p, [key]: v.split(',').map(x => x.trim()).filter(Boolean) }));
  return <div className="main-wrap page-enter" style={{ paddingTop: 42, maxWidth: 900 }}><Link href="/employer/jobs" className="nav-link" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginBottom: 20, fontSize: 12 }}><ArrowLeft size={14}/> All roles</Link><PageTitle kicker="Build a clear brief" title={id ? 'Edit this role' : 'Create a new role'} subtitle="Good details help the right people see themselves here."/>
    <form className="surface" onSubmit={submit} style={{ padding: 'clamp(20px,4vw,32px)', display: 'grid', gap: 16 }}>
      <label className="form-label">Role title<input className="field" required data-testid="input-job-title" value={values.title || ''} onChange={e => set('title',e.target.value)} placeholder="Senior Platform Engineer"/></label>
      <label className="form-label">Description<textarea className="field" required rows={5} data-testid="input-job-description" value={values.description || ''} onChange={e => set('description',e.target.value)} placeholder="Tell candidates about the work, the team, and why it matters."/></label>
      <div className="editor-grid"><label className="form-label">Location<input className="field" required data-testid="input-job-location" value={values.location || ''} onChange={e => set('location',e.target.value)} placeholder="New York, NY"/></label><SelectField label="Work style" test="select-job-remote" value={String(values.remotePolicy)} options={['Remote','Hybrid','On-site']} onChange={v => set('remotePolicy',v)}/><SelectField label="Job type" test="select-job-type" value={String(values.jobType)} options={['Full-time','Part-time','Contract','Internship']} onChange={v => set('jobType',v)}/><SelectField label="Experience" test="select-job-experience" value={String(values.experienceLevel)} options={['Entry','Mid','Senior','Lead']} onChange={v => set('experienceLevel',v)}/><label className="form-label">Salary minimum<input className="field" type="number" data-testid="input-salary-min" value={values.salaryMin || ''} onChange={e => set('salaryMin',e.target.value)}/></label><label className="form-label">Salary maximum<input className="field" type="number" data-testid="input-salary-max" value={values.salaryMax || ''} onChange={e => set('salaryMax',e.target.value)}/></label></div>
      <label className="form-label">Skills <span style={{ fontWeight: 400 }}>Comma separated</span><input className="field" data-testid="input-job-skills" value={list('skills')} onChange={e => setList('skills',e.target.value)}/></label>
      <label className="form-label">Responsibilities <span style={{ fontWeight: 400 }}>Comma separated</span><textarea className="field" rows={3} value={list('responsibilities')} onChange={e => setList('responsibilities',e.target.value)} data-testid="input-job-responsibilities"/></label>
      <label className="form-label">Qualifications <span style={{ fontWeight: 400 }}>Comma separated</span><textarea className="field" rows={3} value={list('qualifications')} onChange={e => setList('qualifications',e.target.value)} data-testid="input-job-qualifications"/></label>
      <label className="form-label">Benefits <span style={{ fontWeight: 400 }}>Comma separated</span><input className="field" value={list('benefits')} onChange={e => setList('benefits',e.target.value)} data-testid="input-job-benefits"/></label>
      <div className="editor-grid"><SelectField label="Application route" test="select-application-method" value={String(values.applicationMethod)} options={['Internal','External']} onChange={v => set('applicationMethod',v)}/><label className="form-label">Apply by<input className="field" type="date" value={values.deadline || ''} onChange={e => set('deadline',e.target.value)} data-testid="input-job-deadline"/></label></div>
      {values.applicationMethod === 'External' && <label className="form-label">External application URL<input className="field" type="url" data-testid="input-external-url" value={values.externalApplyUrl || ''} onChange={e => set('externalApplyUrl',e.target.value)} placeholder="https://company.com/careers"/></label>}
      {message && <div role="status" data-testid="status-job-save" style={{ color: 'hsl(var(--primary))', fontSize: 12 }}>{message}</div>}
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap' }}><Link href="/employer/jobs" className="btn btn-quiet">Cancel</Link><div style={{ display: 'flex', gap: 8 }}><button type="submit" className="btn btn-outline" data-testid="button-save-draft">Save draft</button><button type="button" className="btn btn-primary" data-testid="button-save-and-publish" onClick={async () => { const form = document.querySelector('form'); if (!form?.reportValidity()) return; const payload = { ...values, status: 'Published' as JobStatus }; try { if(id) await service.updateJob(id,payload); else await service.createJob(payload); setMessage('Your role is published.'); setTimeout(() => setLocation('/employer/jobs'), 550); } catch(e) { setMessage(e instanceof Error ? e.message : 'Could not publish role'); } }}>Publish role <ArrowRight size={14}/></button></div></div>
    </form>
  </div>;
}
function SelectField({ label, test, value, options, onChange }: { label: string; test: string; value: string; options: string[]; onChange: (v: string) => void }) { return <label className="form-label">{label}<select className="field" data-testid={test} value={value} onChange={e => onChange(e.target.value)}>{options.map(o => <option key={o}>{o}</option>)}</select></label>; }
function ApplicantsPage() {
  const { id = '' } = useParams();
  const { data: job } = useLoad(() => service.getJob(id), [id]);
  const { data, loading, error, reload } = useLoad(() => service.listApplicants(id), [id]);
  const [apps, setApps] = useState<Application[]>([]);
  const [notice, setNotice] = useState('');
  useEffect(() => setApps(data || []), [data]);
  const updateStatus = async (app: Application, status: ApplicationStatus) => { try { const result = await service.updateApplicationStatus(app.id, status); setApps(xs => xs.map(x => x.id === app.id ? result : x)); setNotice(`${app.candidateName} marked ${status}.`); } catch (reason) { setNotice(reason instanceof Error ? reason.message : 'Could not update application status.'); } };
  return <div className="main-wrap page-enter" style={{ paddingTop: 42, maxWidth: 1000 }}><Link href="/employer/jobs" className="nav-link" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, marginBottom: 20 }}><ArrowLeft size={14}/> Manage roles</Link><PageTitle kicker="Hiring desk · candidates" title={job?.title || 'Applicants'} subtitle={`${apps.length} people have raised their hand for this role.`}/>
    {notice && <div role="alert" style={{ marginBottom: 12, color: 'hsl(var(--primary))', fontSize: 12 }}>{notice}</div>}
    {loading ? <div className="surface skeleton" style={{ height: 180 }}/> : error ? <ErrorState message={error} retry={reload}/> : apps.length ? <div className="surface" style={{ overflow: 'hidden' }}>{apps.map((app,i) => <div key={app.id} data-testid={`row-applicant-${app.id}`} style={{ padding: 19, borderBottom: i === apps.length-1 ? 0 : '1px solid hsl(var(--border))', display: 'grid', gridTemplateColumns: '1fr auto', gap: 16, alignItems: 'center' }}><div><div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}><strong style={{ fontFamily: 'var(--app-font-serif)', fontSize: 16 }}>{app.candidateName}</strong><StatusPill value={app.status}/></div><div style={{ fontSize: 11, color: 'hsl(var(--muted-foreground))', marginTop: 6 }}>{app.candidateEmail} · Applied {app.createdAt} · CV: {app.cvName}</div>{app.coverLetter && <p style={{ fontSize: 12, color: 'hsl(var(--muted-foreground))', lineHeight: 1.55, maxWidth: 630, margin: '10px 0 0' }}>{app.coverLetter}</p>}</div><div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'end', gap: 6 }}><select aria-label={`Update status for ${app.candidateName}`} className="field" data-testid={`select-applicant-status-${app.id}`} style={{ width: 150, minHeight: 35, padding: '6px 8px' }} value={app.status} onChange={e => updateStatus(app,e.target.value as ApplicationStatus)}>{['Applied','Under Review','Shortlisted','Rejected','Hired','Withdrawn','External click'].map(x => <option key={x}>{x}</option>)}</select><a className="btn btn-outline" href={`mailto:${app.candidateEmail}`} data-testid={`link-email-applicant-${app.id}`} style={{ minHeight: 35, fontSize: 11 }}>Email</a></div></div>)}</div> : <EmptyState title="No applications yet" body="When someone applies, their details and status controls will appear here."/>}
  </div>;
}
function NotificationsPage() {
  const { data, loading, error, reload } = useLoad(() => service.listNotifications());
  const [notes, setNotes] = useState<Notification[]>([]);
  const [notice, setNotice] = useState('');
  useEffect(() => setNotes(data || []), [data]);
  const read = async (id: string) => { try { await service.markNotificationRead(id); setNotes(xs => xs.map(n => n.id === id ? { ...n, readAt: new Date().toISOString() } : n)); } catch (reason) { setNotice(reason instanceof Error ? reason.message : 'Could not mark notification as read.'); } };
  return <div className="main-wrap page-enter" style={{ paddingTop: 42, maxWidth: 820 }}><PageTitle kicker="Stay in the loop" title="Notifications" subtitle="Useful updates, without the noise."/>
    {notice && <div role="alert" style={{ marginBottom: 12, color: 'hsl(var(--destructive))', fontSize: 12 }}>{notice}</div>}
    {loading ? <div className="surface skeleton" style={{ height: 180 }}/> : error ? <ErrorState message={error} retry={reload}/> : notes.length ? <div className="surface" style={{ overflow: 'hidden' }}>{notes.map((n,i) => <div key={n.id} data-testid={`notification-${n.id}`} style={{ display: 'grid', gridTemplateColumns: 'auto 1fr auto', gap: 14, alignItems: 'start', padding: 18, borderBottom: i === notes.length-1 ? 0 : '1px solid hsl(var(--border))', background: n.readAt ? 'transparent' : 'hsl(158 34% 95%)' }}><span style={{ width: 34, height: 34, borderRadius: 10, background: 'hsl(var(--secondary))', display: 'grid', placeItems: 'center', color: 'hsl(var(--primary))' }}><Bell size={16}/></span><div><strong style={{ fontSize: 13 }}>{n.title}</strong><p style={{ fontSize: 12, lineHeight: 1.6, color: 'hsl(var(--muted-foreground))', margin: '5px 0' }}>{n.body}</p><span className="font-mono" style={{ fontSize: 10, color: 'hsl(var(--muted-foreground))' }}>{n.createdAt}</span></div>{!n.readAt && <button className="btn btn-quiet" data-testid={`button-mark-read-${n.id}`} onClick={() => read(n.id)} style={{ fontSize: 10 }}>Mark read</button>}</div>)}</div> : <EmptyState title="All caught up" body="We'll put important application and job updates here."/>}
  </div>;
}
function AccountForm({ mode }: { mode: 'login' | 'register' }) {
  const [, setLocation] = useLocation();
  const [role, setRole] = useState<'candidate' | 'company'>('candidate');
  const [error, setError] = useState('');
  const register = mode === 'register';
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    const fields = new FormData(event.currentTarget);
    try {
      if (register) {
        await service.registerAccount({
          name: String(fields.get('name')),
          email: String(fields.get('email')),
          password: String(fields.get('password')),
          role,
          ...(role === 'company' ? { companyName: String(fields.get('companyName') || '') } : {}),
        });
        setLocation('/verify-email');
      } else {
        const user = await service.login({ email: String(fields.get('email')), password: String(fields.get('password')) });
        const requested = new URLSearchParams(window.location.search).get('returnTo');
        const safeReturn = requested?.startsWith('/') && !requested.startsWith('//') ? requested : '';
        setLocation(user.emailVerified ? safeReturn || (isEmployerRole(user.role) ? '/employer' : '/') : '/verify-email');
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'We could not continue. Please try again.');
    }
  };
  return <div className="main-wrap page-enter auth-wrap">
    <section className="surface auth-card">
      <div className="eyebrow">{register ? 'A thoughtful next step' : 'Welcome back'}</div>
      <h1 className="font-display" style={{ fontSize: 35, letterSpacing: '-.05em', margin: '10px 0' }}>{register ? 'Find your next good fit.' : 'Good to see you again.'}</h1>
      <p style={{ color: 'hsl(var(--muted-foreground))', fontSize: 13, lineHeight: 1.6, margin: '0 0 22px' }}>{register ? 'Create a candidate or company account to make the most of steadwork.' : 'Sign in to return to your saved roles and hiring work.'}</p>
      <form onSubmit={submit} style={{ display: 'grid', gap: 14 }}>
        {register && <label className="form-label">Your name<input className="field" name="name" required autoComplete="name" data-testid="input-account-name"/></label>}
        {register && role === 'company' && <label className="form-label">Company name<input className="field" name="companyName" required autoComplete="organization" data-testid="input-company-name"/></label>}
        <label className="form-label">Email address<input className="field" type="email" name="email" required autoComplete="email" data-testid="input-account-email"/></label>
        <label className="form-label">Password<input className="field" type="password" name="password" required minLength={register ? 8 : 1} autoComplete={register ? 'new-password' : 'current-password'} data-testid="input-account-password"/></label>
        {register && <label className="form-label">Account type<select className="field" data-testid="select-account-role" value={role} onChange={event => setRole(event.target.value as 'candidate' | 'company')}><option value="candidate">Job seeker</option><option value="company">Company</option></select></label>}
        {error && <div role="alert" data-testid="status-auth-error" style={{ color: 'hsl(var(--destructive))', fontSize: 12 }}>{error}</div>}
        <button className="btn btn-primary" data-testid={register ? 'button-register' : 'button-login'}>{register ? 'Create account' : 'Sign in'} <ArrowRight size={15}/></button>
      </form>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', borderTop: '1px solid hsl(var(--border))', marginTop: 20, paddingTop: 16, fontSize: 12 }}>
        {register ? <Link href="/login" className="nav-link" data-testid="link-auth-login">Already have an account? Sign in</Link> : <><Link href="/register" className="nav-link" data-testid="link-auth-register">Create an account</Link><Link href="/forgot-password" className="nav-link" data-testid="link-forgot-password">Forgot password?</Link></>}
      </div>
      <p className="demo-note">{import.meta.env.VITE_DATA_MODE === 'mock' ? 'Demo mode: account changes stay in this browser and passwords are not stored.' : 'Your password is sent securely to the API and stored only as a one-way hash.'}</p>
    </section>
  </div>;
}
function PasswordResetPage() {
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const resetToken = new URLSearchParams(window.location.search).get('token');
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    try {
      if (resetToken) await service.completePasswordReset(resetToken, String(fields.get('password')));
      else await service.requestPasswordReset(String(fields.get('email')));
      setError('');
      setMessage(resetToken ? 'Your password has been updated. You can sign in with the new password.' : 'If an account exists for that email, reset instructions have been sent.');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Enter a valid email address.');
    }
  };
  return <div className="main-wrap page-enter auth-wrap"><section className="surface auth-card">
    <div className="eyebrow">Account recovery</div><h1 className="font-display" style={{ fontSize: 34, letterSpacing: '-.05em', margin: '10px 0' }}>{resetToken ? 'Choose a new password.' : 'Reset your password.'}</h1>
    <p style={{ color: 'hsl(var(--muted-foreground))', fontSize: 13, lineHeight: 1.6 }}>{resetToken ? 'Choose a password with at least 8 characters.' : 'Enter your account email and we will send a one-time reset link if an account exists.'}</p>
    <form onSubmit={submit} style={{ display: 'grid', gap: 14, marginTop: 18 }}>{resetToken ? <label className="form-label">New password<input className="field" type="password" name="password" minLength={8} required autoComplete="new-password" data-testid="input-new-password"/></label> : <label className="form-label">Email address<input className="field" type="email" name="email" required data-testid="input-reset-email"/></label>}<button className="btn btn-primary" data-testid="button-request-reset">{resetToken ? 'Update password' : 'Send reset link'}</button></form>
    {message && <div role="status" data-testid="status-reset-message" style={{ marginTop: 15, color: 'hsl(var(--primary))', fontSize: 12 }}>{message}</div>}
    {error && <div role="alert" data-testid="status-reset-error" style={{ marginTop: 15, color: 'hsl(var(--destructive))', fontSize: 12 }}>{error}</div>}
    <Link href="/login" className="nav-link" data-testid="link-reset-login" style={{ display: 'inline-block', marginTop: 18, fontSize: 12 }}>Back to sign in</Link>
  </section></div>;
}
function VerifyEmailPage() {
  const { data: user, loading, reload } = useLoad(() => hasSessionToken() ? service.getCurrentUser() : Promise.resolve(null));
  const [updatedUser, setUpdatedUser] = useState<User | null>(null);
  const [error, setError] = useState('');
  const token = new URLSearchParams(window.location.search).get('token') || undefined;
  useEffect(() => { if (user) setUpdatedUser(user); }, [user]);
  useEffect(() => {
    if (!token) return;
    let live = true;
    service.verifyEmail(token).then(updated => { if (live) { setUpdatedUser(updated); setError(''); } })
      .catch(reason => { if (live) setError(reason instanceof Error ? reason.message : 'Email verification could not be completed.'); });
    return () => { live = false; };
  }, [token]);
  const checkStatus = async () => {
    try {
      setUpdatedUser(await service.getCurrentUser());
      setError('');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Email verification could not be completed.');
    }
  };
  const verified = updatedUser?.emailVerified;
  return <div className="main-wrap page-enter auth-wrap"><section className="surface auth-card">
    <div className="eyebrow">{verified ? 'You’re all set' : 'One more step'}</div>
    <h1 className="font-display" style={{ fontSize: 34, letterSpacing: '-.05em', margin: '10px 0' }}>{verified ? 'Email confirmed.' : 'Check your inbox.'}</h1>
    <p style={{ color: 'hsl(var(--muted-foreground))', fontSize: 13, lineHeight: 1.6 }}>{loading ? 'Loading account…' : verified ? 'Your email address has been verified.' : updatedUser?.email ? `Open the one-time verification link sent to ${updatedUser.email}.` : 'Open the one-time verification link sent to your email. You can use it here even if you opened it on another device.'}</p>
    {!verified && hasSessionToken() && !token && <button className="btn btn-outline" data-testid="button-check-verification" onClick={checkStatus} disabled={loading}>Check verification status</button>}
    {verified && <Link className="btn btn-primary" data-testid="link-continue-after-verification" href={updatedUser?.role === 'company' ? '/employer' : '/'} style={{ marginTop: 10 }}>Continue to steadwork <ArrowRight size={15}/></Link>}
    {error && <div role="alert" data-testid="status-verification-error" style={{ marginTop: 12, color: 'hsl(var(--destructive))', fontSize: 12 }}>{error}</div>}
    <p className="demo-note">A one-time link was sent to your email. In local development, the link is printed by the backend email console.</p>
  </section></div>;
}
function LoginPage() { return <AccountForm mode="login"/>; }
function RegisterPage() { return <AccountForm mode="register"/>; }
function RoutedPages() {
  return <Switch>
    <Route path="/" component={HomePage}/>
    <Route path="/jobs/:id" component={JobDetailPage}/>
    <Route path="/saved" component={() => <ProtectedPage role="candidate"><SavedPage/></ProtectedPage>}/>
    <Route path="/applications" component={() => <ProtectedPage role="candidate"><ApplicationsPage/></ProtectedPage>}/>
    <Route path="/profile" component={() => <ProtectedPage role="candidate"><ProfilePage/></ProtectedPage>}/>
    <Route path="/employer" component={() => <ProtectedPage role="company"><EmployerPage/></ProtectedPage>}/>
    <Route path="/employer/jobs" component={() => <ProtectedPage role="company"><EmployerJobsPage/></ProtectedPage>}/>
    <Route path="/employer/jobs/new" component={() => <ProtectedPage role="company"><JobEditorPage/></ProtectedPage>}/>
    <Route path="/employer/jobs/:id/applicants" component={() => <ProtectedPage role="company"><ApplicantsPage/></ProtectedPage>}/>
    <Route path="/notifications" component={() => <ProtectedPage><NotificationsPage/></ProtectedPage>}/>
    <Route path="/login" component={LoginPage}/>
    <Route path="/register" component={RegisterPage}/>
    <Route path="/forgot-password" component={PasswordResetPage}/>
    <Route path="/verify-email" component={VerifyEmailPage}/>
    <Route component={NotFoundPage}/>
  </Switch>;
}
function NotFoundPage() {
  return <div className="main-wrap page-enter" style={{ paddingTop: 85, maxWidth: 700 }}><div className="surface" style={{ padding: 'clamp(28px,5vw,54px)', textAlign: 'center' }}><div className="eyebrow">Not quite the right place</div><h1 className="font-display" style={{ fontSize: 42, letterSpacing: '-.06em', margin: '12px 0' }}>This page is off the map.</h1><p style={{ color: 'hsl(var(--muted-foreground))', lineHeight: 1.7, fontSize: 14, maxWidth: 440, margin: '0 auto 22px' }}>The page may have moved, or the link may have a typo. Let's get you back to something useful.</p><Link href="/" className="btn btn-primary" data-testid="link-not-found-home">Back to open roles <ArrowRight size={14}/></Link></div></div>;
}
function App() {
  return <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, '')}><AppShell><RoutedPages/></AppShell></WouterRouter>;
}
export default App;
