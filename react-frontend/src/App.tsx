import { useEffect, useMemo, useState } from 'react'
import {
  Search, MapPin, Bookmark, BriefcaseBusiness,
  Sparkles, Upload, RefreshCw, ExternalLink,
  ChevronLeft, ChevronRight, Building2
} from 'lucide-react'
import './App.css'

type Profile = {
  target_titles: string[]
  skills: string[]
  experience_years: number | null
  location: string | null
  remote_only: boolean
}

type Job = {
  source: string
  external_id: string
  title: string
  company: string
  location: string | null
  description: string | null
  job_url: string
  match_score: number | null
  recommendation_summary: string | null
}

type JobResponse = {
  jobs: Job[]
  total_found: number
  total_pages?: number
  companies?: string[]
  source_errors?: string[]
  candidate_profile?: Profile
}

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const PAGE_SIZE = 15

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${url}`, options)
  if (!response.ok) {
    let detail = `Request failed (${response.status})`
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') detail = body.detail
    } catch { /* HTTP response was not JSON */ }
    throw new Error(detail)
  }
  return response.json()
}

function App() {
  const [tab, setTab] = useState<'browse' | 'matches'>('browse')
  const [browseJobs, setBrowseJobs] = useState<Job[]>([])
  const [browseTotal, setBrowseTotal] = useState(0)
  const [browsePages, setBrowsePages] = useState(1)
  const [browseCompanies, setBrowseCompanies] = useState<string[]>([])
  const [browseLoading, setBrowseLoading] = useState(false)
  const [matchJobs, setMatchJobs] = useState<Job[]>([])
  const [profile, setProfile] = useState<Profile | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [keyword, setKeyword] = useState('')
  const [location, setLocation] = useState('')
  const [company, setCompany] = useState('All')
  const [remoteOnly, setRemoteOnly] = useState(false)
  const [sort, setSort] = useState('default')
  const [page, setPage] = useState(1)
  const [selectedKey, setSelectedKey] = useState('')
  const [saved, setSaved] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [sourceErrors, setSourceErrors] = useState<string[]>([])

  const jobKey = (job: Job) =>
    `${job.source}:${job.company}:${job.external_id}`

  async function loadJobs(refresh = false) {
    setBrowseLoading(true)
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(PAGE_SIZE),
        keyword,
        location,
        company,
        remote_only: String(remoteOnly),
        sort,
        refresh: String(refresh)
      })

      const result = await request<JobResponse>(
        `/api/jobs/browse?${params.toString()}`
      )

      setBrowseJobs(result.jobs)
      setBrowseTotal(result.total_found)
      setBrowsePages(result.total_pages ?? 1)
      setBrowseCompanies(result.companies ?? [])
      setSourceErrors(result.source_errors || [])
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : 'Unable to load jobs'
      )
    } finally {
      setBrowseLoading(false)
    }
  }

  useEffect(() => {
    if (tab !== 'browse') return

    const timer = setTimeout(() => {
      void loadJobs()
    }, 300)

    return () => clearTimeout(timer)
  }, [tab, page, keyword, location, company, remoteOnly, sort])

  async function analyzeResume() {
    if (!file) return

    setBusy(true)
    setMessage('Analyzing resume...')

    try {
      const form = new FormData()
      form.append('resume', file)
      if (location.trim()) form.append('location', location.trim())
      form.append('remote_only', String(remoteOnly))

      const analyzed = await request<{ candidate_profile: Profile }>(
        '/api/jobs/profile',
        { method: 'POST', body: form }
      )

      const newProfile = analyzed.candidate_profile
      setProfile(newProfile)
      setMessage('Matching resume against cached jobs...')

      const result = await request<JobResponse>(
        '/api/jobs/matches',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            profile: newProfile,
            minimum_score: 60,
            include_theirstack: false
          })
        }
      )

      setMatchJobs(result.jobs)
      setSourceErrors(result.source_errors || [])
      setTab('matches')
      setPage(1)
      setMessage(`Found ${result.total_found} matching jobs.`)

    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : 'Resume analysis failed'
      )
    } finally {
      setBusy(false)
    }
  }

  async function findMatches(includeTheirStack: boolean) {
    if (!profile) return
    setBusy(true)
    setMessage('')
    try {
      const result = await request<JobResponse>('/api/jobs/matches', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          profile,
          minimum_score: 60,
          include_theirstack: includeTheirStack
        })
      })
      setMatchJobs(result.jobs)
      setSourceErrors(result.source_errors || [])
      setTab('matches')
      setPage(1)
      setSelectedKey('')
      setMessage(`${result.total_found} matching jobs found.`)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Matching failed')
    } finally {
      setBusy(false)
    }
  }

  const jobs = tab === 'browse' ? browseJobs : matchJobs

  const companies = useMemo(
    () => tab === 'browse'
      ? browseCompanies
      : [...new Set(jobs.map(job => job.company))].sort(),
    [jobs, tab, browseCompanies]
  )

  const filtered = useMemo(() => {
    if (tab === 'browse') return jobs
    const words = keyword.toLowerCase().trim().split(/\s+/).filter(Boolean)
    const result = jobs.filter(job => {
      const title = job.title.toLowerCase()
      const companyName = job.company.toLowerCase()
      const loc = (job.location || '').toLowerCase()
      const searchable = `${title} ${companyName}`
      const isRemote = /remote|anywhere|work from home/i.test(loc)
      return words.every(word => searchable.includes(word))
        && (!location || loc.includes(location.toLowerCase()))
        && (company === 'All' || job.company === company)
        && (!remoteOnly || isRemote)
    })
    if (sort === 'title') {
      result.sort((a, b) => a.title.localeCompare(b.title))
    } else if (sort === 'company') {
      result.sort((a, b) => a.company.localeCompare(b.company))
    } else if (sort === 'score') {
      result.sort((a, b) => (b.match_score ?? 0) - (a.match_score ?? 0))
    }
    return result
  }, [jobs, tab, keyword, location, company, remoteOnly, sort])

  const totalPages = tab === 'browse'
    ? browsePages
    : Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))

  const currentPage = Math.min(page, totalPages)

  const visible = tab === 'browse'
    ? filtered
    : filtered.slice(
        (currentPage - 1) * PAGE_SIZE,
        currentPage * PAGE_SIZE
      )

  const selected = visible.find(job => jobKey(job) === selectedKey)
    ?? visible[0]

  function toggleSaved(job: Job) {
    const key = jobKey(job)
    setSaved(current => current.includes(key)
      ? current.filter(item => item !== key)
      : [...current, key])
  }

  function resetFilters() {
    setKeyword('')
    setLocation('')
    setCompany('All')
    setRemoteOnly(false)
    setPage(1)
  }

  function changeTab(next: 'browse' | 'matches') {
    setTab(next)
    setPage(1)
    setSelectedKey('')
    resetFilters()
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="container topbar-inner">
          <div className="brand"><Sparkles size={24} /> TalentFlow <span>AI</span></div>
          <nav>
            <button onClick={() => changeTab('browse')}>Find Jobs</button>
            <button onClick={() => changeTab('matches')}>My Matches</button>
          </nav>
          <span className="top-label">Real jobs · AI-powered matching</span>
        </div>
      </header>

      <section className="hero">
        <div className="container">
          <div className="eyebrow">YOUR CAREER SEARCH, SIMPLIFIED</div>
          <h1>Find your next opportunity.</h1>
          <p>Discover real company openings and match them to your resume.</p>
          <div className="searchbar">
            <div className="search-field">
              <Search size={20} />
              <input
                placeholder="Job title, skill or company"
                value={keyword}
                onChange={e => { setKeyword(e.target.value); setPage(1) }}
              />
            </div>
            <div className="search-field location-field">
              <MapPin size={20} />
              <input
                placeholder="City, state or Remote"
                value={location}
                onChange={e => { setLocation(e.target.value); setPage(1) }}
              />
            </div>
            <button className="primary-button" onClick={() => setPage(1)}>
              Search Jobs
            </button>
          </div>
        </div>
      </section>

      <main className="container main">
        <section className="resume-panel">
          <div>
            <h2><Sparkles size={20} /> AI Resume Matching</h2>
            <p>Upload your PDF or DOCX resume to analyze skills and discover matching jobs.</p>
          </div>
          <div className="resume-actions">
            <input
              aria-label="Upload resume"
              type="file"
              accept=".pdf,.docx"
              onChange={e => setFile(e.target.files?.[0] ?? null)}
            />
            <button
              className="primary-button"
              disabled={!file || busy}
              onClick={analyzeResume}
            >
              <Upload size={17} /> Analyze Resume
            </button>
          </div>
          {profile && (
            <div className="profile-summary">
              <strong>Target roles:</strong> {profile.target_titles.join(', ') || 'Not identified'}
              <div className="skills">
                {profile.skills.slice(0, 15).map(skill => (
                  <span key={skill}>{skill}</span>
                ))}
              </div>
              <button disabled={busy} onClick={() => findMatches(false)}>
                Refresh AI matches
              </button>
              <button disabled={busy} onClick={() => findMatches(true)}>
                Find more with TheirStack (may use API credits)
              </button>
            </div>
          )}
        </section>

        <div className="tabs">
          <button
            className={tab === 'browse' ? 'active' : ''}
            onClick={() => changeTab('browse')}
          >
            Browse Jobs ({browseTotal})
          </button>
          <button
            className={tab === 'matches' ? 'active' : ''}
            onClick={() => changeTab('matches')}
          >
            My Matches · 60%+ ({matchJobs.length})
          </button>
        </div>

        {message && <div className="notice">{message}</div>}
        {sourceErrors.length > 0 && (
          <div className="notice">
            Some sources were unavailable: {sourceErrors.join(', ')}
          </div>
        )}

        <div className="results-heading">
          <div>
            <h2>{tab === 'browse' ? 'Explore Jobs' : 'Personalized Matches'}</h2>
            <p>{filtered.length.toLocaleString()} results from connected sources</p>
          </div>
          <div className="toolbar">
            <select value={sort} onChange={e => setSort(e.target.value)}>
              <option value="default">Default order</option>
              <option value="title">Title A–Z</option>
              <option value="company">Company A–Z</option>
              {tab === 'matches' && <option value="score">Best match</option>}
            </select>
            <button disabled={busy} onClick={() => void loadJobs(true)}>
              <RefreshCw size={16} /> Refresh jobs
            </button>
          </div>
        </div>

        <div className="layout">
          <aside className="filters">
            <h3>Filters</h3>
            <label>Company</label>
            <select value={company} onChange={e => {
              setCompany(e.target.value)
              setPage(1)
            }}>
              <option value="All">All companies</option>
              {companies.map(name => (
                <option key={name} value={name}>{name}</option>
              ))}
            </select>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={remoteOnly}
                onChange={e => { setRemoteOnly(e.target.checked); setPage(1) }}
              />
              Remote only
            </label>
            <button className="clear-button" onClick={resetFilters}>
              Clear filters
            </button>
          </aside>

          <section className="job-list">
            {(tab === 'browse' ? browseLoading : busy) && (
              <div className="empty">Processing your request...</div>
            )}
            {!(tab === 'browse' ? browseLoading : busy) && visible.length === 0 && (
              <div className="empty">
                {tab === 'matches' && !profile
                  ? 'Upload your resume to see AI matches.'
                  : 'No jobs match your current filters.'}
              </div>
            )}
            {visible.map(job => (
              <article
                key={jobKey(job)}
                className={'job-card ' +
                  (jobKey(selected) === jobKey(job) ? 'selected' : '')}
                onClick={() => setSelectedKey(jobKey(job))}
              >
                <div className="job-card-top">
                  <div className="company-avatar"><Building2 size={22} /></div>
                  <button
                    className="icon-button"
                    aria-label="Save job"
                    onClick={e => { e.stopPropagation(); toggleSaved(job) }}
                  >
                    <Bookmark
                      size={19}
                      fill={saved.includes(jobKey(job)) ? 'currentColor' : 'none'}
                    />
                  </button>
                </div>
                <h3>{job.title}</h3>
                <div className="company">{job.company}</div>
                <div className="job-meta">
                  <span><MapPin size={15} /> {job.location || 'Not specified'}</span>
                </div>
                {job.match_score != null && (
                  <div className="match-score">{job.match_score}% resume match</div>
                )}
                <div className="card-bottom">
                  <span>via {job.source}</span>
                  <span><BriefcaseBusiness size={14} /> Direct listing</span>
                </div>
              </article>
            ))}
            {totalPages > 1 && (
              <div className="pagination">
                <button disabled={currentPage === 1}
                  onClick={() => { setPage(currentPage - 1); setSelectedKey('') }}>
                  <ChevronLeft size={18} />
                </button>
                <span>Page {currentPage} of {totalPages}</span>
                <button disabled={currentPage === totalPages}
                  onClick={() => { setPage(currentPage + 1); setSelectedKey('') }}>
                  <ChevronRight size={18} />
                </button>
              </div>
            )}
          </section>

          <section className="detail">
            {selected ? (
              <>
                <div className="company-avatar large"><Building2 size={26} /></div>
                <h2>{selected.title}</h2>
                <div className="company">{selected.company}</div>
                <div className="detail-meta">
                  <span><MapPin size={16} /> {selected.location || 'Not specified'}</span>
                  <span>Source: {selected.source}</span>
                </div>
                {selected.match_score != null && (
                  <div className="match-score">
                    <Sparkles size={18} /> {selected.match_score}% estimated match
                  </div>
                )}
                <a
                  className="apply-button"
                  href={selected.job_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Apply Direct <ExternalLink size={17} />
                </a>
                {selected.recommendation_summary && (
                  <div className="ai-note">
                    <Sparkles size={18} /> {selected.recommendation_summary}
                  </div>
                )}
                <h3>Job Description</h3>
                <div className="description">
                  {selected.description || 'No description provided by source.'}
                </div>
              </>
            ) : (
              <div className="empty">Select a job to view details.</div>
            )}
          </section>
        </div>
      </main>
    </div>
  )
}

export default App

