import { useCallback, useEffect, useMemo, useState } from 'react'

const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
const STATUSES = ['Saved', 'Applied', 'Assessment', 'Interview', 'Offer', 'Rejected']

async function api(path, options = {}) {
  const headers = {
    ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
    ...options.headers,
  }
  const token = sessionStorage.getItem('joblens_access_token')
  if (token && !path.startsWith('/api/auth/')) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const body = await response.json()
      message = body.detail || message
    } catch { /* keep fallback */ }

    const error = new Error(message)
    error.status = response.status

    if (response.status === 401 && !path.startsWith('/api/auth/')) {
      sessionStorage.removeItem('joblens_access_token')
      window.dispatchEvent(new Event('joblens:unauthorized'))
    }
    throw error
  }
  if (response.status === 204) return null
  return response.json()
}

function SectionTitle({ eyebrow, title, detail }) {
  return <div className="section-title"><div><span className="eyebrow">{eyebrow}</span><h2>{title}</h2></div>{detail && <p>{detail}</p>}</div>
}

function EmptyState({ children }) {
  return <div className="empty-state"><span className="empty-icon">↗</span><p>{children}</p></div>
}

export default function App() {
  const [profileText, setProfileText] = useState('')
  const [profileSource, setProfileSource] = useState('')
  const [profileSaved, setProfileSaved] = useState(false)
  const [jobTitle, setJobTitle] = useState('')
  const [company, setCompany] = useState('')
  const [location, setLocation] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [requiredSkills, setRequiredSkills] = useState('')
  const [jobUrl, setJobUrl] = useState('')
  const [match, setMatch] = useState(null)
  const [jobs, setJobs] = useState([])
  const [applications, setApplications] = useState([])
  const [analytics, setAnalytics] = useState({ total_jobs: 0, total_applications: 0, status_counts: {} })
  const [appTitle, setAppTitle] = useState('')
  const [appCompany, setAppCompany] = useState('')
  const [appStatus, setAppStatus] = useState('Saved')
  const [appUrl, setAppUrl] = useState('')
  const [appNotes, setAppNotes] = useState('')
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState({ kind: '', text: '' })
  const [apiReady, setApiReady] = useState(false)
  const [token, setToken] = useState(() => sessionStorage.getItem('joblens_access_token') || '')
  const [authMode, setAuthMode] = useState('login')
  const [authName, setAuthName] = useState('')
  const [authEmail, setAuthEmail] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authBusy, setAuthBusy] = useState(false)
  const [authError, setAuthError] = useState('')
  const [authMessage, setAuthMessage] = useState('')

  const refreshData = useCallback(async () => {
    try {
      const [profile, savedJobs, apps, stats] = await Promise.all([
        api('/api/profile'), api('/api/jobs'), api('/api/applications'), api('/api/analytics'),
      ])
      if (profile?.resume_text) {
        setProfileText(profile.resume_text)
        setProfileSource(profile.source_filename || '')
        setProfileSaved(true)
      }
      setJobs(savedJobs)
      setApplications(apps)
      setAnalytics(stats)
      setApiReady(true)
    } catch (error) {
      setApiReady(false)
      if (error.status === 401) {
        setAuthError('Your session expired. Please log in again.')
        sessionStorage.removeItem('joblens_access_token')
        setToken('')
      } else {
        setNotice({
          kind: 'error',
          text: `Could not reach the backend at ${API_BASE}. ${error.message}`,
        })
      }
    }
  }, [])

  useEffect(() => {
    if (token) {
      refreshData()
    } else {
      setApiReady(false)
    }
  }, [token, refreshData])


  useEffect(() => {
    const handleUnauthorized = () => {
      setAuthError('Your session expired. Please log in again.')
      setToken('')
      setApiReady(false)
    }
    window.addEventListener('joblens:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('joblens:unauthorized', handleUnauthorized)
  }, [])

  const topStatus = useMemo(() => Object.entries(analytics.status_counts || {}).sort((a, b) => b[1] - a[1]).find(([, count]) => count > 0)?.[0] || 'No activity yet', [analytics])

  async function saveProfile() {
    setBusy(true)
    try {
      const saved = await api('/api/profile', { method: 'PUT', body: JSON.stringify({ resume_text: profileText }) })
      setProfileSource(saved.source_filename || '')
      setProfileSaved(true)
      setNotice({ kind: 'success', text: 'Profile saved to the database.' })
    } catch (error) { setNotice({ kind: 'error', text: error.message }) }
    finally { setBusy(false) }
  }

  async function uploadResume(event) {
    const file = event.target.files?.[0]
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setNotice({ kind: 'error', text: 'Please choose a PDF resume.' }); event.target.value = ''; return
    }
    const data = new FormData()
    data.append('file', file)
    setBusy(true)
    try {
      const result = await api('/api/profile/upload', { method: 'POST', body: data })
      setProfileText(result.resume_text)
      setProfileSource(result.source_filename || file.name)
      setProfileSaved(true)
      setNotice({ kind: 'success', text: `Extracted text from ${file.name}. Please review it before matching.` })
    } catch (error) { setNotice({ kind: 'error', text: error.message }) }
    finally { setBusy(false); event.target.value = '' }
  }

  async function analyzeJob(event) {
    event.preventDefault()
    setBusy(true); setMatch(null)
    try {
      const result = await api('/api/analyze', {
        method: 'POST',
        body: JSON.stringify({
          resume_text: profileText,
          job_title: jobTitle || 'Target role',
          job_description: jobDescription,
          required_skills: requiredSkills.split(',').map(s => s.trim()).filter(Boolean),
        }),
      })
      setMatch(result)
      setNotice({ kind: 'success', text: 'Analysis complete. Scores are heuristic indicators, not hiring probabilities.' })
    } catch (error) { setNotice({ kind: 'error', text: error.message }) }
    finally { setBusy(false) }
  }

  async function saveJob() {
    if (!jobTitle.trim() || !jobDescription.trim()) {
      setNotice({ kind: 'error', text: 'Add a job title and description before saving.' }); return
    }
    setBusy(true)
    try {
      await api('/api/jobs', { method: 'POST', body: JSON.stringify({
        title: jobTitle, company: company || 'Not specified', location: location || 'Not specified',
        description: jobDescription, required_skills: requiredSkills.split(',').map(s => s.trim()).filter(Boolean), job_url: jobUrl || null,
      }) })
      await refreshData()
      setNotice({ kind: 'success', text: 'Job saved to your job library.' })
    } catch (error) { setNotice({ kind: 'error', text: error.message }) }
    finally { setBusy(false) }
  }

  
async function removeJob(id) {
  try {
    await api(`/api/jobs/${id}`, { method: 'DELETE' });
    await refreshData();
    setNotice({
      kind: 'success',
      text: 'Saved job removed.',
    });
  } catch (error) {
    setNotice({ kind: 'error', text: error.message });
  }
}

  async function addApplication(event) {
    event.preventDefault()
    setBusy(true)
    try {
      await api('/api/applications', { method: 'POST', body: JSON.stringify({
        title: appTitle, company: appCompany, status: appStatus, job_url: appUrl || null, notes: appNotes,
      }) })
      setAppTitle(''); setAppCompany(''); setAppStatus('Applied'); setAppUrl(''); setAppNotes('')
      await refreshData()
      setNotice({ kind: 'success', text: 'Application added to your tracker.' })
    } catch (error) { setNotice({ kind: 'error', text: error.message }) }
    finally { setBusy(false) }
  }

  async function changeApplication(id, status) {
    try { await api(`/api/applications/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) }); await refreshData() }
    catch (error) { setNotice({ kind: 'error', text: error.message }) }
  }

  async function removeApplication(id) {
    try { await api(`/api/applications/${id}`, { method: 'DELETE' }); await refreshData(); setNotice({ kind: 'success', text: 'Application removed.' }) }
    catch (error) { setNotice({ kind: 'error', text: error.message }) }
  }

  async function submitAuth(event) {
    event.preventDefault()
    setAuthBusy(true)
    setAuthError('')

    try {
      const isSignup = authMode === 'signup'
      const payload = isSignup
        ? { name: authName.trim(), email: authEmail.trim(), password: authPassword }
        : { email: authEmail.trim(), password: authPassword }

      const result = await api(
        isSignup ? '/api/auth/signup' : '/api/auth/login',
        { method: 'POST', body: JSON.stringify(payload) },
      )

      if (isSignup) {
        setAuthMessage(result.message || 'Account created successfully. You can now log in.')        
        setAuthPassword('')
        setAuthName('')
        setAuthMode('login')
      } else {
        sessionStorage.setItem('joblens_access_token', result.access_token)
        setToken(result.access_token)
        setAuthPassword('')
      }
      setAuthError('')
    } catch (error) {
      setAuthError(error.message || 'Authentication failed. Please try again.')
    } finally {
      setAuthBusy(false)
    }
  }

  function logout() {
    sessionStorage.removeItem('joblens_access_token')
    setToken('')
    setAuthPassword('')
    setAuthError('')
    setProfileText('')
    setProfileSource('')
    setProfileSaved(false)
    setJobs([])
    setApplications([])
    setMatch(null)
    setAnalytics({ total_jobs: 0, total_applications: 0, status_counts: {} })
    setNotice({ kind: '', text: '' })
  }

  if (!token) {
    return (
      <main className="auth-screen">
        <section className="auth-card">
          <div className="brand auth-brand">
            <span className="brand-mark">J</span>
            <span>joblens<span className="brand-ai">.ai</span></span>
          </div>
          <span className="eyebrow">CAREER INTELLIGENCE WORKSPACE</span>
          <h1>{authMode === 'signup' ? 'Create your account' : 'Welcome back'}</h1>
          <p className="auth-description">
            {authMode === 'signup'
              ? 'Create an account to manage your profile, job matches, and applications.'
              : 'Log in to continue your job search with your saved profile and opportunities.'}
          </p>

          <form className="auth-form" onSubmit={submitAuth}>
            {authMode === 'signup' && (
              <div className="field">
                <label htmlFor="auth-name">Full name</label>
                <input
                  id="auth-name"
                  value={authName}
                  onChange={(event) => setAuthName(event.target.value)}
                  minLength={2}
                  maxLength={100}
                  autoComplete="name"
                  required
                />
              </div>
            )}
            <div className="field">
              <label htmlFor="auth-email">Email address</label>
              <input
                id="auth-email"
                type="email"
                value={authEmail}
                onChange={(event) => setAuthEmail(event.target.value)}
                autoComplete="email"
                required
              />
            </div>
            <div className="field">
              <label htmlFor="auth-password">Password</label>
              <input
                id="auth-password"
                type="password"
                value={authPassword}
                onChange={(event) => setAuthPassword(event.target.value)}
                minLength={authMode === 'signup' ? 8 : 1}
                maxLength={128}
                autoComplete={authMode === 'signup' ? 'new-password' : 'current-password'}
                required
              />
              {authMode === 'signup' && (
                <small className="auth-hint">Use at least 8 characters.</small>
              )}
            </div>

            {authError && <p className="auth-error" role="alert">{authError}</p>}
            {authMessage && <p className="auth-message" role="status">{authMessage}</p>}


            <button className="button button-primary auth-submit" type="submit" disabled={authBusy}>
              {authBusy ? 'Please wait…' : authMode === 'signup' ? 'Create account' : 'Log in'}
            </button>
          </form>

          <p className="auth-switch">
            {authMode === 'signup' ? 'Already have an account?' : 'New to JobLens AI?'}
            {' '}
            <button
              type="button"
              onClick={() => {
                setAuthMode(authMode === 'signup' ? 'login' : 'signup')
                setAuthError('')
                setAuthMessage('')
              }}
            >
              {authMode === 'signup' ? 'Log in' : 'Create account'}
            </button>
          </p>
          <p className="auth-footnote">Your session token stays in this browser tab's session storage.</p>
        </section>
      </main>
    )
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">J</span><span>joblens<span className="brand-ai">.ai</span></span></div>
        <div className="workspace-label">WORKSPACE</div>
        <a className="nav-item active" href="#overview"><span>◫</span> Overview</a>
        <a className="nav-item" href="#matcher"><span>⌕</span> Role matcher</a>
        <a className="nav-item" href="#job-library"><span>▤</span> Job library</a>
        <a className="nav-item" href="#applications"><span>✓</span> Applications</a>
        <div className="sidebar-bottom">
          <div className="connection"><span className={`connection-dot ${apiReady ? 'online' : ''}`} /><div><b>{apiReady ? 'API connected' : 'API offline'}</b><small>{apiReady ? 'Local development' : 'Start backend server'}</small></div></div>
          <div className="sidebar-tip"><span className="tip-star">✳</span><b>Build with intention</b><p>Use the match report to identify learning goals—not to define your potential.</p></div>
        </div>
      </aside>

      <main className="main-content" id="overview">
        <header className="topbar"><div className="breadcrumb">Workspace <span>/</span> Overview</div><div className="topbar-right"><span className="date-label">CAREER INTELLIGENCE</span><span className="avatar">ST</span><button className="logout-button" onClick={logout}>Log out</button></div></header>
        <section className="hero"><div><div className="hero-kicker"><span className="pulse" /> YOUR CAREER, WITH CLARITY</div><h1>Make your next move<br /><em>more intentional.</em></h1><p>Understand role fit, find your skill gaps, and keep your job search organized in one workspace.</p></div><div className="hero-art" aria-hidden="true"><div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="art-center">J<span>✳</span></div><div className="floating-tag tag-one">SKILL SIGNALS</div><div className="floating-tag tag-two">ROLE INSIGHTS</div><div className="art-dot dot-one" /><div className="art-dot dot-two" /></div></section>

        {notice.text && <div className={`notice ${notice.kind}`} role="status"><span>{notice.kind === 'error' ? '!' : '✓'}</span><p>{notice.text}</p><button onClick={() => setNotice({ kind: '', text: '' })} aria-label="Dismiss notice">×</button></div>}

        <section className="metric-grid" aria-label="Career search metrics">
          <div className="metric-card"><div className="metric-top"><span>Saved roles</span><span className="metric-icon">▤</span></div><strong>{analytics.total_jobs}</strong><small>In your job library</small><div className="metric-line"><span style={{ width: `${Math.min(100, analytics.total_jobs * 10)}%` }} /></div></div>
          <div className="metric-card"><div className="metric-top"><span>Applications</span><span className="metric-icon">↗</span></div><strong>{analytics.total_applications}</strong><small>Tracked opportunities</small><div className="metric-line"><span style={{ width: `${Math.min(100, analytics.total_applications * 10)}%` }} /></div></div>
          <div className="metric-card"><div className="metric-top"><span>Interviews</span><span className="metric-icon">◎</span></div><strong>{analytics.status_counts?.Interview || 0}</strong><small>Currently at interview stage</small><div className="metric-line"><span style={{ width: `${Math.min(100, (analytics.status_counts?.Interview || 0) * 20)}%` }} /></div></div>
          <div className="metric-card accent-metric"><div className="metric-top"><span>Current pipeline</span><span className="metric-icon">✳</span></div><strong className="pipeline-text">{topStatus}</strong><small>Most common active stage</small><div className="mini-bars">{STATUSES.map((status) => <span key={status} title={`${status}: ${analytics.status_counts?.[status] || 0}`} style={{ height: `${7 + Math.min(28, (analytics.status_counts?.[status] || 0) * 7)}px` }} />)}</div></div>
        </section>

        <section className="panel profile-panel" id="profile">
          <SectionTitle eyebrow="01 / CANDIDATE PROFILE" title="Your skills, in context" detail="Start with resume text. You control what gets stored; this local MVP doesn't send your resume to an external AI provider." />
          <div className="profile-toolbar"><label className="upload-button">⇧ Upload resume PDF<input type="file" accept="application/pdf,.pdf" onChange={uploadResume} disabled={busy} /></label><span className="file-hint">PDF · up to 5 MB {profileSource ? `· ${profileSource}` : ''}</span><span className={`save-state ${profileSaved ? 'saved' : ''}`}>{profileSaved ? '● Profile saved' : '○ Not saved yet'}</span></div>
          <label className="field-label" htmlFor="profile-text">Resume / skills text</label>
          <textarea id="profile-text" className="large-textarea profile-textarea" value={profileText} onChange={(e) => { setProfileText(e.target.value); setProfileSaved(false) }} placeholder="Paste resume text, projects, tools, internships, and skills here…" rows={5} />
          <div className="form-footer"><span className="char-count">{profileText.length.toLocaleString()} / 100,000 characters</span><button className="button button-dark" onClick={saveProfile} disabled={busy || !profileText.trim()}>{busy ? 'Working…' : 'Save profile'} <span>→</span></button></div>
        </section>

        <section className="panel matcher-panel" id="matcher">
          <SectionTitle eyebrow="02 / ROLE MATCHER" title="Decode a job description" detail="Compare skills explicitly and review the text-overlap signal. You can edit the skill list to correct the automatic vocabulary." />
          <form onSubmit={analyzeJob}>
            <div className="field-grid"><div className="field"><label htmlFor="job-title">Role title *</label><input id="job-title" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} placeholder="e.g. Data Analyst" required /></div><div className="field"><label htmlFor="company">Company</label><input id="company" value={company} onChange={(e) => setCompany(e.target.value)} placeholder="e.g. Example Technologies" /></div></div>
            <div className="field-grid"><div className="field"><label htmlFor="location">Location</label><input id="location" value={location} onChange={(e) => setLocation(e.target.value)} placeholder="e.g. Hyderabad / Remote" /></div><div className="field"><label htmlFor="job-url">Job URL (optional)</label><input id="job-url" type="url" value={jobUrl} onChange={(e) => setJobUrl(e.target.value)} placeholder="https://…" /></div></div>
            <div className="field"><label htmlFor="required-skills">Required skills <span className="label-sub">comma-separated</span></label><input id="required-skills" value={requiredSkills} onChange={(e) => setRequiredSkills(e.target.value)} placeholder="Python, SQL, Power BI, communication" /></div>
            <div className="field"><label htmlFor="job-description">Job description *</label><textarea id="job-description" className="large-textarea" value={jobDescription} onChange={(e) => setJobDescription(e.target.value)} rows={6} placeholder="Paste the responsibilities, qualifications, and role requirements…" required /></div>
            <div className="matcher-actions"><p><span className="info-icon">i</span> No generative AI API is required in this version; the baseline matcher runs locally.</p><div className="action-buttons"><button className="button button-light" type="button" onClick={saveJob} disabled={busy || !jobTitle.trim() || !jobDescription.trim()}>＋ Save job</button><button className="button button-primary" type="submit" disabled={busy}>{busy ? 'Analyzing…' : 'Analyze role'} <span>→</span></button></div></div>
          </form>
          {match && <div className="match-results" aria-live="polite"><div className="result-heading"><div><span className="eyebrow">MATCH REPORT</span><h3>{match.job_title}</h3></div><div className="score-ring" style={{ '--score': `${match.match_score}%` }}><div><strong>{match.match_score}<small>%</small></strong><span>heuristic</span></div></div></div><div className="score-breakdown"><div><div><span>Required skill coverage</span><b>{match.skill_coverage_score}%</b></div><div className="progress-track"><span style={{ width: `${match.skill_coverage_score}%` }} /></div></div><div><div><span>TF-IDF text similarity</span><b>{match.text_similarity_score}%</b></div><div className="progress-track lavender"><span style={{ width: `${match.text_similarity_score}%` }} /></div></div></div><div className="skill-columns"><div className="skill-group"><h4>✓ Skills detected in your profile <span>{match.profile_skills.length}</span></h4><div className="chips">{match.profile_skills.length ? match.profile_skills.map(s => <span className="chip neutral" key={s}>{s}</span>) : <small>No known skills detected in profile text.</small>}</div></div><div className="skill-group"><h4>Role requirements <span>{match.job_skills.length}</span></h4><div className="chips">{match.job_skills.map(s => <span className={`chip ${match.matched_skills.includes(s) ? 'good' : 'missing'}`} key={s}>{match.matched_skills.includes(s) ? '✓ ' : '+ '}{s}</span>)}{!match.job_skills.length && <small>No vocabulary matches. Add skills in the field above.</small>}</div></div></div><div className="recommendations"><h4>Learning recommendations</h4>{match.recommendations.map((r, i) => <p key={i}><span>{String(i + 1).padStart(2, '0')}</span>{r}</p>)}</div><p className="scoring-note">ⓘ {match.scoring_note}</p></div>}
        </section>

        <section className="panel" id="job-library"><SectionTitle eyebrow="03 / JOB LIBRARY" title="Roles worth a closer look" detail="Saved job descriptions are stored in your local database." />
          {jobs.length ? <div className="table-wrap"><table><thead><tr><th>ROLE</th><th>COMPANY / LOCATION</th><th>SKILLS</th><th>ADDED</th><th></th></tr></thead><tbody>{jobs.map(job => <tr key={job.id}><td><b>{job.title}</b>{job.job_url && <a className="row-link" href={job.job_url} target="_blank" rel="noreferrer">Open listing ↗</a>}</td><td>{job.company}<small className="cell-sub">{job.location}</small></td><td><div className="chips compact">{(job.required_skills || []).slice(0, 3).map(s => <span className="chip neutral" key={s}>{s}</span>)}{job.required_skills?.length > 3 && <span className="chip neutral">+{job.required_skills.length - 3}</span>}</div></td><td>{new Date(job.created_at).toLocaleDateString()}</td><td><button className="icon-button" onClick={() => removeJob(job.id)} title="Delete saved job" aria-label={`Delete ${job.title}`}>×</button></td></tr>)}</tbody></table></div> : <EmptyState>Save a role from the matcher to start your job library.</EmptyState>}
        </section>

        <section className="panel" id="applications"><SectionTitle eyebrow="04 / APPLICATION TRACKER" title="Keep every next step visible" detail="Track application status as it changes. Update the stage from the table." />
          <form className="application-form" onSubmit={addApplication}><div className="field"><label htmlFor="app-title">Role *</label><input id="app-title" value={appTitle} onChange={e => setAppTitle(e.target.value)} placeholder="Role title" required /></div><div className="field"><label htmlFor="app-company">Company *</label><input id="app-company" value={appCompany} onChange={e => setAppCompany(e.target.value)} placeholder="Company name" required /></div><div className="field"><label htmlFor="app-status">Stage</label><select id="app-status" value={appStatus} onChange={e => setAppStatus(e.target.value)}>{STATUSES.map(s => <option key={s}>{s}</option>)}</select></div><div className="field"><label htmlFor="app-url">Job URL</label><input id="app-url" type="url" value={appUrl} onChange={e => setAppUrl(e.target.value)} placeholder="https://…" /></div><div className="field notes-field"><label htmlFor="app-notes">Notes</label><input id="app-notes" value={appNotes} onChange={e => setAppNotes(e.target.value)} placeholder="Recruiter, deadline, next step…" /></div><button className="button button-dark add-app-button" type="submit" disabled={busy}>＋ Add application</button></form>
          {applications.length ? <div className="table-wrap"><table><thead><tr><th>ROLE / COMPANY</th><th>STAGE</th><th>NOTES</th><th>ADDED</th><th></th></tr></thead><tbody>{applications.map(item => <tr key={item.id}><td><b>{item.title}</b><small className="cell-sub">{item.company}</small>{item.job_url && <a className="row-link" href={item.job_url} target="_blank" rel="noreferrer">Open listing ↗</a>}</td><td><select className={`status-select status-${item.status.toLowerCase()}`} value={item.status} onChange={e => changeApplication(item.id, e.target.value)} aria-label={`Status for ${item.title}`}>{STATUSES.map(s => <option key={s}>{s}</option>)}</select></td><td className="notes-cell">{item.notes || '—'}</td><td>{new Date(item.created_at).toLocaleDateString()}</td><td><button className="icon-button" onClick={() => removeApplication(item.id)} title="Delete application" aria-label={`Delete ${item.title}`}>×</button></td></tr>)}</tbody></table></div> : <EmptyState>Add the roles you have applied to and update each stage over time.</EmptyState>}
        </section>

        <footer className="footer"><span className="footer-brand">joblens.ai</span><span>Built to learn. Designed to explain.</span><span>v1.0 · Local-first MVP</span></footer>
      </main>
    </div>
  )
}
