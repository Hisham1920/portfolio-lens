import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Bell,
  BookOpenText,
  BrainCircuit,
  BriefcaseBusiness,
  ChartNoAxesCombined,
  CheckCircle2,
  ChevronDown,
  CircleDollarSign,
  Clock3,
  Crosshair,
  Download,
  FileImage,
  FileText,
  FileUp,
  Gauge,
  LayoutDashboard,
  LoaderCircle,
  PencilLine,
  PieChart as PieChartIcon,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Target,
  Trash2,
  TrendingUp,
  TriangleAlert,
  Trophy,
  UploadCloud,
  WalletCards,
  X,
} from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const COLORS = ['#39e58c', '#65a6ff', '#ffb454', '#bf8cff', '#ff6d85', '#43d8d0']
const SECTORS = ['Automobile', 'Consumer', 'Energy', 'Financials', 'Healthcare', 'Industrials', 'Technology', 'Telecom', 'Utilities', 'Other']
const MARKET_CAPS = ['Large Cap', 'Mid Cap', 'Small Cap']
const API_BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
const PUBLIC_DEMO_MODE = import.meta.env.VITE_PUBLIC_DEMO === 'true'

const apiUrl = (path) => `${API_BASE_URL}${path}`

const createHolding = () => ({
  symbol: '',
  company: '',
  quantity: '',
  average_price: '',
  current_price: '',
  sector: '',
  market_cap: '',
})

const money = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

const compactMoney = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  notation: 'compact',
  maximumFractionDigits: 1,
})

const formatFileSize = (bytes) => `${(bytes / 1024 / 1024).toFixed(bytes >= 1024 * 1024 ? 1 : 2)} MB`

function MetricCard({ label, value, note, icon: Icon, accent = 'green' }) {
  return (
    <article className={`metric-card accent-${accent}`}>
      <div className="metric-card__top">
        <span>{label}</span>
        <div className="metric-icon"><Icon size={18} /></div>
      </div>
      <strong>{value}</strong>
      <small>{note}</small>
    </article>
  )
}

function AllocationTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const item = payload[0].payload
  return (
    <div className="chart-tooltip">
      <span>{item.name}</span>
      <strong>{item.percentage.toFixed(1)}%</strong>
      <small>{money.format(item.value)}</small>
    </div>
  )
}

function DonutCard({ title, subtitle, data }) {
  return (
    <article className="panel chart-panel">
      <div className="panel-heading">
        <div><h3>{title}</h3><p>{subtitle}</p></div>
        <button className="icon-button"><span>View</span><ChevronDown size={16} /></button>
      </div>
      <div className="donut-layout">
        <div className="donut-wrap">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} dataKey="value" innerRadius={58} outerRadius={82} paddingAngle={3} stroke="none">
                {data.map((item, index) => <Cell key={item.name} fill={COLORS[index % COLORS.length]} />)}
              </Pie>
              <Tooltip content={<AllocationTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="donut-center"><strong>{data.length}</strong><span>groups</span></div>
        </div>
        <div className="legend-list">
          {data.slice(0, 5).map((item, index) => (
            <div className="legend-row" key={item.name}>
              <span className="legend-dot" style={{ background: COLORS[index % COLORS.length] }} />
              <span>{item.name}</span>
              <strong>{item.percentage.toFixed(1)}%</strong>
            </div>
          ))}
        </div>
      </div>
    </article>
  )
}

function InsightStat({ label, value, note, icon: Icon, tone = 'green' }) {
  return (
    <article className={`insight-stat tone-${tone}`}>
      <span><Icon size={17} /></span>
      <div><small>{label}</small><strong>{value}</strong><p>{note}</p></div>
    </article>
  )
}

function StressLab({ summary, concentration }) {
  const [marketShock, setMarketShock] = useState(-10)
  const [sectorShock, setSectorShock] = useState(-15)
  const marketImpact = summary.current_value * marketShock / 100
  const sectorValue = summary.current_value * concentration.largest_sector_weight / 100
  const sectorImpact = sectorValue * sectorShock / 100
  const totalImpact = marketImpact + sectorImpact
  const stressedValue = Math.max(0, summary.current_value + totalImpact)
  const totalImpactPercentage = totalImpact / summary.current_value * 100

  return (
    <article className="panel stress-panel" id="stress-test">
      <div className="panel-heading">
        <div><h3><SlidersHorizontal size={18} />Custom stress test</h3><p>Explore a simple “what if” scenario without any API call</p></div>
        <span className="local-badge">LOCAL</span>
      </div>
      <div className="stress-result">
        <div><span>Estimated portfolio value</span><strong>{money.format(stressedValue)}</strong></div>
        <div className={totalImpact >= 0 ? 'positive' : 'negative'}>
          <span>Estimated change</span>
          <strong>{totalImpact >= 0 ? '+' : ''}{money.format(totalImpact)}</strong>
          <small>{totalImpactPercentage >= 0 ? '+' : ''}{totalImpactPercentage.toFixed(2)}%</small>
        </div>
      </div>
      <label className="stress-control">
        <div><span>Whole market move</span><strong>{marketShock}%</strong></div>
        <input type="range" min="-30" max="20" step="1" value={marketShock} onChange={(event) => setMarketShock(Number(event.target.value))} />
        <div className="range-labels"><span>-30%</span><span>+20%</span></div>
      </label>
      <label className="stress-control">
        <div><span>Extra {concentration.largest_sector} move</span><strong>{sectorShock}%</strong></div>
        <input type="range" min="-40" max="20" step="1" value={sectorShock} onChange={(event) => setSectorShock(Number(event.target.value))} />
        <div className="range-labels"><span>-40%</span><span>+20%</span></div>
      </label>
      <p className="stress-disclaimer">This is a linear sensitivity illustration, not a price forecast. Sector shock is applied in addition to the whole-market move.</p>
    </article>
  )
}

function portfolioReportCacheKey(portfolio) {
  const fingerprint = JSON.stringify({
    name: portfolio.meta.portfolio_name,
    holdings: portfolio.holdings.map((item) => [
      item.symbol,
      item.quantity,
      item.average_price,
      item.current_price,
      item.sector,
      item.market_cap,
    ]),
  })
  let hash = 0
  for (let index = 0; index < fingerprint.length; index += 1) {
    hash = ((hash << 5) - hash + fingerprint.charCodeAt(index)) | 0
  }
  return `portfolio-lens-ai-report-${Math.abs(hash)}`
}

function reportHoldings(portfolio) {
  return portfolio.holdings.map((item) => ({
    symbol: item.symbol,
    company: item.company,
    quantity: item.quantity,
    average_price: item.average_price,
    current_price: item.current_price,
    sector: item.sector,
    market_cap: item.market_cap,
  }))
}

async function responseJson(response, fallbackMessage) {
  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) {
    throw new Error(fallbackMessage)
  }
  return response.json()
}

function PortfolioReport({ portfolio, publicDemoMode = false }) {
  const [mode, setMode] = useState('automated')
  const cacheKey = useMemo(() => portfolioReportCacheKey(portfolio), [portfolio])
  const [aiResult, setAiResult] = useState(() => {
    try {
      const cached = window.localStorage.getItem(cacheKey)
      return cached ? JSON.parse(cached) : null
    } catch {
      return null
    }
  })
  const [consent, setConsent] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [reportError, setReportError] = useState('')

  const generateAIReport = async () => {
    if (!consent) {
      setReportError('Confirm consent before generating the AI interpretation.')
      return
    }

    setGenerating(true)
    setReportError('')
    try {
      const response = await fetch(apiUrl('/api/portfolio/report/ai'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          portfolio_name: portfolio.meta.portfolio_name,
          holdings: reportHoldings(portfolio),
          consent: true,
        }),
      })
      const result = await responseJson(response, 'The report service returned an unexpected response. Confirm the Milestone 5 backend is running.')
      if (!response.ok) throw new Error(result.error || 'AI report generation failed.')
      setAiResult(result)
      setMode('ai')
      try {
        window.localStorage.setItem(cacheKey, JSON.stringify(result))
      } catch {
        // The report remains available for this session if browser storage is unavailable.
      }
    } catch (error) {
      setReportError(error.message)
    } finally {
      setGenerating(false)
    }
  }

  const report = mode === 'ai' ? aiResult?.report : portfolio.automated_report
  const downloadPDF = async () => {
    if (!report) return
    if (publicDemoMode && mode === 'automated') {
      const link = document.createElement('a')
      link.href = '/portfolio-lens-demo-report.pdf'
      link.download = 'PortfolioLens-demo-report.pdf'
      document.body.appendChild(link)
      link.click()
      link.remove()
      return
    }
    setDownloading(true)
    setReportError('')
    try {
      const response = await fetch(apiUrl('/api/portfolio/report/pdf'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          portfolio_name: portfolio.meta.portfolio_name,
          holdings: reportHoldings(portfolio),
          report,
          report_label: mode === 'ai' ? 'AI-Generated Portfolio Interpretation' : 'Automated Portfolio Report',
        }),
      })
      if (!response.ok) {
        const result = await responseJson(response, 'The PDF service returned an unexpected response.')
        throw new Error(result.error || 'PDF generation failed.')
      }
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${portfolio.meta.portfolio_name.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '') || 'portfolio'}-report.pdf`
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (error) {
      setReportError(error.message)
    } finally {
      setDownloading(false)
    }
  }

  return (
    <section className="panel report-panel" id="report">
      <div className="report-heading">
        <div>
          <span className="report-eyebrow"><BookOpenText size={15} />Written portfolio report</span>
          <h2>{portfolio.meta.portfolio_name}</h2>
          <p>Turn the dashboard metrics into an explanation you can read and share.</p>
        </div>
        <button className="download-report" onClick={downloadPDF} disabled={!report || downloading}>
          {downloading ? <LoaderCircle className="spin-icon" size={16} /> : <Download size={16} />}
          {downloading ? 'Preparing PDF…' : 'Download PDF'}
        </button>
      </div>

      <div className="report-mode-tabs">
        <button className={mode === 'automated' ? 'active' : ''} onClick={() => { setMode('automated'); setReportError('') }}>
          <ChartNoAxesCombined size={16} />
          <span><strong>Automated report</strong><small>Instant · No API cost</small></span>
        </button>
        <button
          className={mode === 'ai' ? 'active' : ''}
          onClick={() => { setMode('ai'); setReportError('') }}
          disabled={publicDemoMode}
          title={publicDemoMode ? 'Paid AI is disabled in the public showcase.' : ''}
        >
          <BrainCircuit size={16} />
          <span>
            <strong>AI interpretation</strong>
            <small>
              {publicDemoMode
                ? 'Disabled in public demo'
                : aiResult ? 'Cached · No repeat charge' : 'Optional · One API request'}
            </small>
          </span>
        </button>
      </div>

      {mode === 'ai' && !aiResult ? (
        <div className="ai-report-gate">
          <div className="ai-gate-icon"><BrainCircuit size={30} /></div>
          <div className="ai-gate-copy">
            <span>Optional premium interpretation</span>
            <h3>Generate one AI-written report</h3>
            <p>PortfolioLens sends only your verified holdings and calculated metrics. It does not resend the screenshot or PDF. The result is cached in this browser.</p>
          </div>
          <label className="report-consent">
            <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} />
            <span>I consent to sending the verified portfolio data to OpenAI for one report-generation request.</span>
          </label>
          <button className="generate-report-button" onClick={generateAIReport} disabled={generating}>
            {generating ? <LoaderCircle className="spin-icon" size={17} /> : <Sparkles size={17} />}
            {generating ? 'Writing report…' : 'Generate AI interpretation'}
          </button>
          <small>Uses the cost-sensitive report model configured in backend/.env. This button is the only report action that uses AI credit.</small>
        </div>
      ) : report ? (
        <div className="written-report">
          <div className={`report-source ${mode === 'ai' ? 'ai' : ''}`}>
            {mode === 'ai' ? <BrainCircuit size={17} /> : <CheckCircle2 size={17} />}
            <div>
              <strong>{mode === 'ai' ? 'AI-generated portfolio interpretation' : 'Automated portfolio report'}</strong>
              <span>
                {mode === 'ai'
                  ? `Generated once with ${aiResult.model} and saved in this browser.`
                  : 'Generated locally from verified portfolio calculations with no AI API call.'}
              </span>
            </div>
          </div>

          <article className="executive-summary">
            <span>Executive summary</span>
            <p>{report.executive_summary}</p>
          </article>

          <div className="report-highlights">
            <article className="report-strengths">
              <h3><CheckCircle2 size={17} />Portfolio strengths</h3>
              {report.strengths.map((item) => <p key={item}>{item}</p>)}
            </article>
            <article className="report-watch">
              <h3><TriangleAlert size={17} />Areas to watch</h3>
              {report.watch_items.map((item) => <p key={item}>{item}</p>)}
            </article>
          </div>

          <div className="report-sections">
            {report.sections.map((section) => (
              <article key={section.heading}>
                <h3>{section.heading}</h3>
                <p>{section.body}</p>
              </article>
            ))}
          </div>

          <article className="report-conclusion">
            <span>Overall perspective</span>
            <p>{report.closing_summary}</p>
          </article>
          <p className="report-disclaimer">This educational report uses user-supplied prices and heuristic portfolio metrics. It is not investment advice, a recommendation, or a forecast.</p>
        </div>
      ) : null}

      {reportError && <div className="report-error">{reportError}</div>}
    </section>
  )
}

function ManualPortfolioModal({ onClose, onAnalyse, onExtract, analysing, extracting }) {
  const [step, setStep] = useState('entry')
  const [entryMode, setEntryMode] = useState('upload')
  const [portfolioName, setPortfolioName] = useState("Hisham's Portfolio")
  const [rows, setRows] = useState([createHolding(), createHolding(), createHolding()])
  const [formError, setFormError] = useState('')
  const [files, setFiles] = useState([])
  const [consent, setConsent] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [extractionMeta, setExtractionMeta] = useState(null)
  const fileInputRef = useRef(null)

  const updateRow = (index, field, value) => {
    setRows((current) => current.map((row, rowIndex) => (
      rowIndex === index ? { ...row, [field]: value } : row
    )))
  }

  const removeRow = (index) => {
    setRows((current) => current.length === 1 ? current : current.filter((_, rowIndex) => rowIndex !== index))
  }

  const addFiles = (fileList) => {
    const incoming = Array.from(fileList)
    const allowedExtensions = ['jpg', 'jpeg', 'png', 'pdf']
    const invalid = incoming.find((file) => !allowedExtensions.includes(file.name.split('.').pop()?.toLowerCase()))
    if (invalid) {
      setFormError(`${invalid.name} is not a supported JPG, PNG, or PDF file.`)
      return
    }
    if (incoming.some((file) => file.size > 12 * 1024 * 1024)) {
      setFormError('Each file must be 12 MB or smaller.')
      return
    }

    setFiles((current) => {
      const merged = [...current]
      incoming.forEach((file) => {
        if (!merged.some((item) => item.name === file.name && item.size === file.size)) merged.push(file)
      })
      if (merged.length > 6) {
        setFormError('Upload no more than 6 files at once.')
        return current
      }
      if (merged.reduce((total, file) => total + file.size, 0) > 25 * 1024 * 1024) {
        setFormError('Uploads must be 25 MB or smaller in total.')
        return current
      }
      setFormError('')
      return merged
    })
  }

  const extractFiles = async () => {
    if (!files.length) {
      setFormError('Select at least one portfolio screenshot or PDF.')
      return
    }
    if (!consent) {
      setFormError('Confirm that you consent to AI processing before continuing.')
      return
    }

    setFormError('')
    const result = await onExtract(files)
    if (result.error) {
      setFormError(result.error)
      return
    }

    setRows(result.data.holdings.map((holding) => ({
      symbol: holding.symbol || '',
      company: holding.company || holding.symbol || '',
      quantity: holding.quantity ?? '',
      average_price: holding.average_price ?? '',
      current_price: holding.current_price ?? '',
      sector: holding.sector || '',
      market_cap: holding.market_cap || '',
      _confidence: holding.confidence,
      _warning: holding.warning,
      _source_file: holding.source_file,
    })))
    setPortfolioName(`${result.data.broker === 'Other' ? 'Imported' : result.data.broker} Portfolio`)
    setExtractionMeta(result.data)
    setEntryMode('manual')
  }

  const validate = () => {
    const completedRows = rows.filter((row) => row.symbol || row.company || row.quantity || row.average_price || row.current_price)
    if (!portfolioName.trim()) {
      setFormError('Give your portfolio a name.')
      return false
    }
    if (!completedRows.length) {
      setFormError('Add at least one holding.')
      return false
    }

    const invalidIndex = completedRows.findIndex((row) => (
      !row.symbol.trim()
      || !row.company.trim()
      || !row.sector
      || !row.market_cap
      || Number(row.quantity) <= 0
      || Number(row.average_price) < 0
      || Number(row.current_price) <= 0
    ))

    if (invalidIndex >= 0) {
      setFormError(`Complete all fields with valid values in holding ${invalidIndex + 1}.`)
      return false
    }

    setRows(completedRows)
    setFormError('')
    return true
  }

  const reviewPortfolio = () => {
    if (validate()) setStep('review')
  }

  const submitPortfolio = async () => {
    const holdings = rows.map((row) => ({
      symbol: row.symbol.trim().toUpperCase(),
      company: row.company.trim(),
      quantity: Number(row.quantity),
      average_price: Number(row.average_price),
      current_price: Number(row.current_price),
      sector: row.sector,
      market_cap: row.market_cap,
    }))

    const requestError = await onAnalyse({ portfolio_name: portfolioName.trim(), holdings })
    if (requestError) setFormError(requestError)
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="portfolio-modal" role="dialog" aria-modal="true" aria-label="Add portfolio">
        <div className="modal-header">
          <div>
            <span className="modal-kicker">{step === 'entry' ? 'Step 1 of 2' : 'Step 2 of 2'}</span>
            <h2>{step === 'entry' ? 'Add your portfolio' : 'Verify your portfolio'}</h2>
            <p>{step === 'entry' ? 'Upload broker files for AI extraction, or enter holdings manually.' : 'Check every value before starting the analysis.'}</p>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close"><X size={19} /></button>
        </div>

        <div className="step-track"><i className="complete" /><i className={step === 'review' ? 'complete' : ''} /></div>

        {step === 'entry' ? (
          <div className="modal-body">
            <div className="method-tabs" role="tablist" aria-label="Portfolio entry method">
              <button className={entryMode === 'upload' ? 'active' : ''} onClick={() => { setEntryMode('upload'); setFormError('') }}><UploadCloud size={17} />Upload files</button>
              <button className={entryMode === 'manual' ? 'active' : ''} onClick={() => { setEntryMode('manual'); setFormError('') }}><PencilLine size={16} />Enter manually</button>
            </div>

            {entryMode === 'upload' ? (
              <div className="upload-workflow">
                <input
                  ref={fileInputRef}
                  className="hidden-file-input"
                  type="file"
                  accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
                  multiple
                  onChange={(event) => {
                    addFiles(event.target.files)
                    event.target.value = ''
                  }}
                />
                <div
                  className={`drop-zone ${dragActive ? 'drag-active' : ''}`}
                  onDragEnter={(event) => { event.preventDefault(); setDragActive(true) }}
                  onDragOver={(event) => event.preventDefault()}
                  onDragLeave={(event) => { event.preventDefault(); setDragActive(false) }}
                  onDrop={(event) => {
                    event.preventDefault()
                    setDragActive(false)
                    addFiles(event.dataTransfer.files)
                  }}
                >
                  <div className="drop-icon"><UploadCloud size={26} /></div>
                  <h3>Drop portfolio files here</h3>
                  <p>Use clear screenshots or broker PDFs. Multiple overlapping screenshots are okay.</p>
                  <button type="button" onClick={() => fileInputRef.current?.click()}>Choose files</button>
                  <small>JPG, JPEG, PNG or PDF · Up to 6 files · 12 MB each</small>
                </div>

                {files.length > 0 && (
                  <div className="selected-files">
                    <div className="selected-files__heading"><strong>{files.length} file{files.length === 1 ? '' : 's'} selected</strong><button onClick={() => { setFiles([]); setFormError('') }}>Clear all</button></div>
                    {files.map((file, index) => (
                      <div className="selected-file" key={`${file.name}-${file.size}`}>
                        <span>{file.type === 'application/pdf' ? <FileText size={17} /> : <FileImage size={17} />}</span>
                        <div><strong>{file.name}</strong><small>{formatFileSize(file.size)}</small></div>
                        <button onClick={() => setFiles((current) => current.filter((_, fileIndex) => fileIndex !== index))} aria-label={`Remove ${file.name}`}><X size={15} /></button>
                      </div>
                    ))}
                  </div>
                )}

                <label className="consent-check">
                  <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} />
                  <span>I consent to sending these files to OpenAI for one-time portfolio extraction. I have removed account numbers or other unnecessary personal information.</span>
                </label>
                <div className="upload-privacy"><ShieldCheck size={17} /><span>PortfolioLens processes the upload in memory and does not save the original file. Always verify the extracted numbers.</span></div>
              </div>
            ) : (
              <div className="manual-workflow">
                <label className="portfolio-name-field">
                  <span>Portfolio name</span>
                  <input value={portfolioName} onChange={(event) => setPortfolioName(event.target.value)} maxLength={60} />
                </label>

                {extractionMeta ? (
                  <>
                    <div className="extraction-result">
                      <ShieldCheck size={17} />
                      <div><strong>{extractionMeta.holdings.length} visible holding{extractionMeta.holdings.length === 1 ? '' : 's'} extracted</strong><span>Detected broker: {extractionMeta.broker}. Review every highlighted or missing field.</span></div>
                    </div>
                    {extractionMeta.warnings?.map((warning) => <div className="extraction-warning" key={warning}>{warning}</div>)}
                  </>
                ) : (
                  <div className="entry-help">
                    <PencilLine size={16} />
                    <p>Enter the price shown by your broker. After analysis, Refresh market prices can replace supported NSE prices with the latest available snapshot.</p>
                  </div>
                )}

                <div className="holding-form-list">
                  {rows.map((row, index) => (
                    <div className={`holding-form-card ${row._confidence < 0.85 ? 'needs-review' : ''}`} key={`${row.symbol}-${index}`}>
                      <div className="holding-form-title">
                        <div>
                          <strong>Holding {index + 1}</strong>
                          {row._confidence != null && <span className={`confidence-chip ${row._confidence < 0.85 ? 'low' : ''}`}>{Math.round(row._confidence * 100)}% read confidence</span>}
                        </div>
                        <button onClick={() => removeRow(index)} disabled={rows.length === 1} aria-label={`Remove holding ${index + 1}`}><Trash2 size={15} /></button>
                      </div>
                      <div className="holding-fields">
                        <label><span>Symbol</span><input placeholder="RELIANCE" value={row.symbol} onChange={(event) => updateRow(index, 'symbol', event.target.value)} /></label>
                        <label className="wide-field"><span>Company</span><input placeholder="Reliance Industries" value={row.company} onChange={(event) => updateRow(index, 'company', event.target.value)} /></label>
                        <label><span>Quantity</span><input type="number" min="0" step="any" placeholder="10" value={row.quantity} onChange={(event) => updateRow(index, 'quantity', event.target.value)} /></label>
                        <label><span>Average price</span><input type="number" min="0" step="any" placeholder="1250" value={row.average_price} onChange={(event) => updateRow(index, 'average_price', event.target.value)} /></label>
                        <label><span>Current price</span><input type="number" min="0" step="any" placeholder="1400" value={row.current_price} onChange={(event) => updateRow(index, 'current_price', event.target.value)} /></label>
                        <label><span>Sector</span><select value={row.sector} onChange={(event) => updateRow(index, 'sector', event.target.value)}><option value="">Select</option>{SECTORS.map((sector) => <option key={sector}>{sector}</option>)}</select></label>
                        <label><span>Market cap</span><select value={row.market_cap} onChange={(event) => updateRow(index, 'market_cap', event.target.value)}><option value="">Select</option>{MARKET_CAPS.map((size) => <option key={size}>{size}</option>)}</select></label>
                      </div>
                      {(row._source_file || row._warning) && <div className="row-source"><span>{row._source_file && `Source: ${row._source_file}`}</span>{row._warning && <strong>{row._warning}</strong>}</div>}
                    </div>
                  ))}
                </div>

                <button className="add-holding" onClick={() => setRows((current) => [...current, createHolding()])}><Plus size={16} />Add another holding</button>
              </div>
            )}
          </div>
        ) : (
          <div className="modal-body verification-body">
            <div className="verification-summary"><span>{portfolioName}</span><strong>{rows.length} holding{rows.length === 1 ? '' : 's'}</strong></div>
            <div className="verification-table-wrap">
              <table className="verification-table">
                <thead><tr><th>Holding</th><th>Quantity</th><th>Avg. price</th><th>Current</th><th>Sector</th><th>Size</th></tr></thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.symbol}>
                      <td><strong>{row.symbol.toUpperCase()}</strong><small>{row.company}</small></td>
                      <td>{row.quantity}</td>
                      <td>{money.format(Number(row.average_price))}</td>
                      <td>{money.format(Number(row.current_price))}</td>
                      <td>{row.sector}</td>
                      <td>{row.market_cap}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="verify-notice"><ShieldCheck size={17} /><span>PortfolioLens will calculate from these verified values. It will not invent or alter your numbers.</span></div>
          </div>
        )}

        {formError && <div className="form-error">{formError}</div>}
        <div className="modal-actions">
          <button className="secondary-action" onClick={step === 'entry' ? onClose : () => { setStep('entry'); setFormError('') }}>{step === 'entry' ? 'Cancel' : 'Back to edit'}</button>
          <button
            className="primary-action"
            onClick={step === 'entry' ? (entryMode === 'upload' ? extractFiles : reviewPortfolio) : submitPortfolio}
            disabled={analysing || extracting}
          >
            {extracting
              ? <><LoaderCircle className="spin-icon" size={17} />Reading files…</>
              : analysing
                ? <><LoaderCircle className="spin-icon" size={17} />Analysing…</>
                : step === 'entry'
                  ? entryMode === 'upload' ? 'Extract holdings' : 'Review portfolio'
                  : 'Analyse portfolio'}
          </button>
        </div>
      </section>
    </div>
  )
}

function CorporateActionModal({ onClose, onResolve, resolving, error }) {
  const [confirmed, setConfirmed] = useState(false)

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="corporate-action-modal" role="dialog" aria-modal="true" aria-label="Resolve Tata Motors demerger">
        <div className="modal-header">
          <div>
            <span className="modal-kicker">Corporate action review</span>
            <h2>Resolve the Tata Motors demerger</h2>
            <p>The legacy TATAMOTORS position cannot safely use a single replacement ticker.</p>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close"><X size={19} /></button>
        </div>
        <div className="corporate-action-body">
          <div className="corporate-action-explainer">
            <TriangleAlert size={20} />
            <div>
              <strong>Why confirmation is required</strong>
              <span>Investors who held the shares on 14 October 2025 retained one TMPV share and received one TMCV share for every legacy TATAMOTORS share.</span>
            </div>
          </div>
          <div className="demerger-grid">
            <article><span>TMPV</span><strong>Passenger vehicles</strong><small>68.85% of original acquisition cost</small></article>
            <article><span>TMCV</span><strong>Commercial vehicles</strong><small>31.15% of original acquisition cost</small></article>
          </div>
          <div className="resolution-result">
            <CheckCircle2 size={18} />
            <div><strong>What PortfolioLens will do</strong><span>Split the quantity 1:1, preserve the total original cost, then refresh both NSE market prices independently.</span></div>
          </div>
          <label className="record-date-check">
            <input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />
            <span>I confirm that this TATAMOTORS position was held on the 14 October 2025 record date.</span>
          </label>
          <p className="corporate-action-caution">If the shares were bought later or your broker already converted them, close this window and enter the actual TMPV/TMCV holdings shown by your broker.</p>
          {error && <div className="form-error corporate-action-error">{error}</div>}
        </div>
        <div className="modal-actions">
          <button className="secondary-action" onClick={onClose}>Not now</button>
          <button className="primary-action" onClick={onResolve} disabled={!confirmed || resolving}>
            {resolving ? <><LoaderCircle className="spin-icon" size={17} />Resolving…</> : 'Resolve and refresh'}
          </button>
        </div>
      </section>
    </div>
  )
}

function App() {
  const [portfolio, setPortfolio] = useState(null)
  const [error, setError] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [analysing, setAnalysing] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [priceRefreshing, setPriceRefreshing] = useState(false)
  const [priceError, setPriceError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [corporateActionOpen, setCorporateActionOpen] = useState(false)
  const [corporateActionResolving, setCorporateActionResolving] = useState(false)
  const [corporateActionError, setCorporateActionError] = useState('')
  const [resolutionNotice, setResolutionNotice] = useState('')

  useEffect(() => {
    const source = PUBLIC_DEMO_MODE ? '/demo-portfolio.json' : apiUrl('/api/portfolio/demo')
    fetch(source)
      .then((response) => {
        if (!response.ok) throw new Error(PUBLIC_DEMO_MODE ? 'The showcase data is unavailable.' : 'The analysis service is unavailable.')
        return response.json()
      })
      .then(setPortfolio)
      .catch((requestError) => setError(requestError.message))
  }, [])

  const performanceData = useMemo(() => {
    if (!portfolio) return []
    return portfolio.holdings
      .slice()
      .sort((a, b) => b.return_percentage - a.return_percentage)
      .map((item) => ({ name: item.symbol, return: item.return_percentage }))
  }, [portfolio])

  const contributionData = useMemo(() => {
    if (!portfolio) return []
    return portfolio.holdings
      .slice()
      .sort((a, b) => b.return_contribution - a.return_contribution)
      .map((item) => ({
        name: item.symbol,
        contribution: item.return_contribution,
        pnl: item.pnl,
      }))
  }, [portfolio])

  const visibleHoldings = useMemo(() => {
    if (!portfolio) return []
    const query = searchTerm.trim().toLowerCase()
    if (!query) return portfolio.holdings
    return portfolio.holdings.filter((item) => (
      item.symbol.toLowerCase().includes(query)
      || item.company.toLowerCase().includes(query)
      || item.sector.toLowerCase().includes(query)
    ))
  }, [portfolio, searchTerm])

  const analyseCustomPortfolio = async (payload) => {
    if (PUBLIC_DEMO_MODE) return 'Portfolio uploads are disabled in the public showcase.'
    setAnalysing(true)
    try {
      const response = await fetch(apiUrl('/api/portfolio/analyse'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const result = await responseJson(response, 'The analysis service returned an unexpected response. Confirm the latest backend is running.')
      if (!response.ok) throw new Error(result.error || 'Portfolio analysis failed.')
      setPortfolio(result)
      setSearchTerm('')
      setModalOpen(false)
      window.scrollTo({ top: 0, behavior: 'smooth' })
      return ''
    } catch (requestError) {
      return requestError.message
    } finally {
      setAnalysing(false)
    }
  }

  const extractPortfolioFiles = async (files) => {
    if (PUBLIC_DEMO_MODE) {
      return { data: null, error: 'AI extraction is disabled in the public showcase.' }
    }
    setExtracting(true)
    try {
      const payload = new FormData()
      files.forEach((file) => payload.append('files', file))
      payload.append('consent', 'true')
      const response = await fetch(apiUrl('/api/portfolio/extract'), {
        method: 'POST',
        body: payload,
      })
      const result = await responseJson(response, 'The extraction service returned an unexpected response. Confirm the latest backend is running.')
      if (!response.ok) throw new Error(result.error || 'Portfolio extraction failed.')
      return { data: result, error: '' }
    } catch (requestError) {
      return { data: null, error: requestError.message }
    } finally {
      setExtracting(false)
    }
  }

  const refreshMarketPrices = async () => {
    if (PUBLIC_DEMO_MODE || !portfolio) return
    setPriceRefreshing(true)
    setPriceError('')
    try {
      const response = await fetch(apiUrl('/api/portfolio/refresh-prices'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          portfolio_name: portfolio.meta.portfolio_name,
          holdings: reportHoldings(portfolio),
        }),
      })
      const result = await responseJson(
        response,
        'The price service returned an unexpected response. Confirm the latest backend is running.',
      )
      if (!response.ok) throw new Error(result.error || 'Market-price refresh failed.')
      setPortfolio(result)
    } catch (requestError) {
      setPriceError(requestError.message)
    } finally {
      setPriceRefreshing(false)
    }
  }

  const resolveTataMotorsDemerger = async () => {
    if (PUBLIC_DEMO_MODE || !portfolio) return
    setCorporateActionResolving(true)
    setCorporateActionError('')
    try {
      const response = await fetch(apiUrl('/api/portfolio/resolve-corporate-action'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          portfolio_name: portfolio.meta.portfolio_name,
          holdings: reportHoldings(portfolio),
          held_on_record_date: true,
        }),
      })
      const result = await responseJson(
        response,
        'The resolver returned an unexpected response. Confirm the latest backend is running.',
      )
      if (!response.ok) throw new Error(result.error || 'Corporate-action resolution failed.')
      setPortfolio(result)
      setCorporateActionOpen(false)
      const priceText = result.meta.corporate_action_resolution?.market_prices_refreshed
        ? 'Both market prices were refreshed.'
        : 'Use Refresh market prices when the provider is available.'
      setResolutionNotice(`TATAMOTORS was split into TMPV and TMCV. ${priceText}`)
    } catch (requestError) {
      setCorporateActionError(requestError.message)
    } finally {
      setCorporateActionResolving(false)
    }
  }

  if (error) {
    return (
      <main className="state-screen">
        <Activity size={32} />
        <h1>We couldn’t load the portfolio</h1>
        <p>{error}{PUBLIC_DEMO_MODE ? ' Refresh this page or try again later.' : ' Start the Flask backend on port 5000 and refresh this page.'}</p>
      </main>
    )
  }

  if (!portfolio) {
    return <main className="state-screen"><div className="loader" /><p>Analysing your portfolio…</p></main>
  }

  const {
    summary,
    performance,
    concentration,
    sector_allocation,
    market_cap_allocation,
    sector_performance,
    risk_breakdown,
    risk_methodology,
    stress_scenarios,
    insights,
    meta,
  } = portfolio
  const positiveReturn = summary.total_pnl >= 0
  const structuralRiskLevel = risk_methodology?.level
    || (summary.risk_score < 35 ? 'Low' : summary.risk_score < 65 ? 'Moderate' : 'High')
  const marketData = meta.market_data
  const marketUpdateTime = marketData?.fetched_at
    ? new Date(marketData.fetched_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : ''

  return (
    <div className="app-shell">
      {modalOpen && (
        <ManualPortfolioModal
          onClose={() => setModalOpen(false)}
          onAnalyse={analyseCustomPortfolio}
          onExtract={extractPortfolioFiles}
          analysing={analysing}
          extracting={extracting}
        />
      )}
      {corporateActionOpen && (
        <CorporateActionModal
          onClose={() => { setCorporateActionOpen(false); setCorporateActionError('') }}
          onResolve={resolveTataMotorsDemerger}
          resolving={corporateActionResolving}
          error={corporateActionError}
        />
      )}
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark"><TrendingUp size={20} /></div><span>Portfolio<span>Lens</span></span></div>
        <nav>
          <a className="active" href="#overview"><LayoutDashboard size={19} />Overview</a>
          <a href="#holdings"><BriefcaseBusiness size={19} />Holdings</a>
          <a href="#allocation"><PieChartIcon size={19} />Allocation</a>
          <a href="#insights"><Sparkles size={19} />Smart insights<span className="new-badge">LOCAL</span></a>
          <a href="#risk"><ShieldCheck size={19} />Risk analysis</a>
          <a href="#stress-test"><SlidersHorizontal size={19} />Stress test</a>
          <a href="#report"><BookOpenText size={19} />Written report<span className="new-badge">NEW</span></a>
        </nav>
        <div className="sidebar-bottom">
          <div className="privacy-card"><ShieldCheck size={20} /><div><strong>Privacy first</strong><span>Upload only after consent.</span></div></div>
          <div className="user-card"><div className="avatar">HS</div><div><strong>Demo Investor</strong><span>Free workspace</span></div><ChevronDown size={16} /></div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="mobile-brand"><TrendingUp size={18} />PortfolioLens</div>
          <label className="search-box"><Search size={17} /><input placeholder="Search holdings…" value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} /></label>
          <div className="top-actions">
            <button className="notification"><Bell size={19} /><i /></button>
            {PUBLIC_DEMO_MODE ? (
              <button className="upload-button demo-button" disabled><ShieldCheck size={17} />Public demo</button>
            ) : (
              <button className="upload-button" onClick={() => setModalOpen(true)}><FileUp size={17} />Add portfolio</button>
            )}
          </div>
        </header>

        <div className="page" id="overview">
          {PUBLIC_DEMO_MODE && (
            <div className="public-demo-banner">
              <ShieldCheck size={17} />
              <div>
                <strong>Safe public showcase</strong>
                <span>Explore the complete dashboard with demonstration data. Uploads and paid AI actions are disabled to protect private information and API credit.</span>
              </div>
            </div>
          )}
          <section className="hero-row">
            <div><p className="eyebrow">Portfolio overview</p><h1>Good afternoon, Hisham.</h1><p>Here’s how your investments are positioned today.</p></div>
            <div className="portfolio-select"><span>Viewing portfolio</span><button>{meta.portfolio_name}<ChevronDown size={16} /></button></div>
          </section>

          <div className="market-data-row">
            <div className="notice"><span className="notice-dot" />{meta.data_notice}</div>
            {!PUBLIC_DEMO_MODE && (
              <button className="refresh-prices-button" onClick={refreshMarketPrices} disabled={priceRefreshing}>
                <RefreshCw className={priceRefreshing ? 'spin-icon' : ''} size={15} />
                {priceRefreshing ? 'Refreshing…' : 'Refresh market prices'}
              </button>
            )}
          </div>
          {marketData && (
            <div className="market-data-status">
              <Clock3 size={14} />
              <span>
                {marketData.provider} snapshot updated at {marketUpdateTime}.
                {' '}{marketData.refreshed_count} symbol{marketData.refreshed_count === 1 ? '' : 's'} refreshed
                {marketData.cache_hits ? ` (${marketData.cache_hits} from cache)` : ''}.
              </span>
              {marketData.failed_count > 0 && (
                <strong>
                  Needs review: {marketData.failed_symbols.map((item) => item.symbol).join(', ')}.
                </strong>
              )}
            </div>
          )}
          {marketData?.failed_symbols?.map((failure) => (
            <div className="market-symbol-warning" key={failure.symbol}>
              <TriangleAlert size={15} />
              <div>
                <strong>{failure.symbol} kept its previous price</strong>
                <span>{failure.reason}</span>
                {failure.suggested_symbols?.length > 0 && (
                  <small>Suggested symbols to review: {failure.suggested_symbols.join(' and ')}.</small>
                )}
                {failure.type === 'corporate_action_review' && !PUBLIC_DEMO_MODE && (
                  <button className="resolve-corporate-action" onClick={() => setCorporateActionOpen(true)}>
                    Resolve Tata Motors demerger
                  </button>
                )}
              </div>
            </div>
          ))}
          {resolutionNotice && (
            <div className="corporate-action-success">
              <CheckCircle2 size={15} />
              <span>{resolutionNotice}</span>
              <button onClick={() => setResolutionNotice('')} aria-label="Dismiss"><X size={14} /></button>
            </div>
          )}
          {priceError && (
            <div className="price-refresh-error"><TriangleAlert size={15} /><span>{priceError}</span></div>
          )}

          <section className="metrics-grid">
            <MetricCard label="Current value" value={money.format(summary.current_value)} note={`${summary.holdings_count} holdings across ${summary.sectors_count} sectors`} icon={WalletCards} />
            <MetricCard label="Total invested" value={money.format(summary.invested_value)} note="Your total acquisition cost" icon={CircleDollarSign} accent="blue" />
            <MetricCard label="Total returns" value={`${positiveReturn ? '+' : ''}${money.format(summary.total_pnl)}`} note={`${positiveReturn ? '▲' : '▼'} ${Math.abs(summary.total_return).toFixed(2)}% overall return`} icon={positiveReturn ? ArrowUpRight : ArrowDownRight} accent={positiveReturn ? 'green' : 'red'} />
            <MetricCard label="Structural risk" value={`${summary.risk_score}/100`} note={`${structuralRiskLevel} exposure score · excludes volatility`} icon={Gauge} accent="orange" />
          </section>

          <section className="insight-stats">
            <InsightStat label="Portfolio health" value={`${Math.round(summary.health_score)}/100`} note="Balance of risk, spread and returns" icon={ShieldCheck} />
            <InsightStat label="Effective holdings" value={summary.effective_holdings.toFixed(1)} note={`Actual diversification across ${summary.holdings_count} positions`} icon={Target} tone="blue" />
            <InsightStat label="Winning positions" value={`${summary.winners_count}/${summary.holdings_count}`} note={`${performance.profitable_weight.toFixed(1)}% of portfolio value is profitable`} icon={Trophy} tone="orange" />
            <InsightStat label="Concentration" value={concentration.level} note={`Top 3 holdings form ${concentration.top_three_weight.toFixed(1)}%`} icon={Crosshair} tone={concentration.level === 'High' ? 'red' : 'purple'} />
          </section>

          <section className="dashboard-grid" id="allocation">
            <DonutCard title="Sector allocation" subtitle="Where your money is invested" data={sector_allocation} />
            <DonutCard title="Market-cap mix" subtitle="Company-size exposure" data={market_cap_allocation} />
            <article className="panel performance-panel">
              <div className="panel-heading"><div><h3>Holding performance</h3><p>Returns from acquisition price</p></div><BarChart3 size={19} /></div>
              <div className="performance-chart">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={performanceData} margin={{ top: 12, right: 4, left: -25, bottom: 0 }}>
                    <CartesianGrid stroke="#1c3028" vertical={false} />
                    <XAxis dataKey="name" tick={{ fill: '#70887d', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#70887d', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(value) => `${value}%`} />
                    <Tooltip cursor={{ fill: 'rgba(255,255,255,.025)' }} contentStyle={{ background: '#10241b', border: '1px solid #244035', borderRadius: 12 }} formatter={(value) => [`${value.toFixed(2)}%`, 'Return']} />
                    <Bar dataKey="return" radius={[5, 5, 0, 0]}>
                      {performanceData.map((item) => <Cell key={item.name} fill={item.return >= 0 ? '#39e58c' : '#ff6d85'} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>
          </section>

          <section className="analysis-deep-grid">
            <article className="panel deep-panel">
              <div className="panel-heading"><div><h3><ChartNoAxesCombined size={18} />Performance quality</h3><p>What is driving your overall result</p></div></div>
              <div className="deep-value-grid">
                <div><span>Gross gains</span><strong className="positive">{money.format(performance.gross_gains)}</strong></div>
                <div><span>Gross losses</span><strong className="negative">{money.format(performance.gross_losses)}</strong></div>
                <div><span>Profit factor</span><strong>{performance.profit_factor == null ? performance.gross_gains > 0 ? 'No losses' : 'N/A' : `${performance.profit_factor.toFixed(2)}×`}</strong></div>
                <div><span>Profitable value</span><strong>{performance.profitable_weight.toFixed(1)}%</strong></div>
              </div>
              <div className="best-worst">
                <div className="best"><span>Best performer</span><strong>{performance.best_holding.symbol}</strong><small>{performance.best_holding.return_percentage >= 0 ? '+' : ''}{performance.best_holding.return_percentage.toFixed(2)}% · {money.format(performance.best_holding.pnl)}</small></div>
                <div className="worst"><span>Weakest performer</span><strong>{performance.worst_holding.symbol}</strong><small>{performance.worst_holding.return_percentage.toFixed(2)}% · {money.format(performance.worst_holding.pnl)}</small></div>
              </div>
            </article>

            <article className="panel deep-panel">
              <div className="panel-heading"><div><h3><Crosshair size={18} />Concentration check</h3><p>How strongly a few positions influence results</p></div><span className={`status-badge status-${concentration.level.toLowerCase()}`}>{concentration.level}</span></div>
              <div className="concentration-list">
                <div>
                  <div><span>{concentration.largest_holding}</span><strong>{concentration.largest_holding_weight.toFixed(1)}%</strong></div>
                  <i><b style={{ width: `${Math.min(concentration.largest_holding_weight, 100)}%` }} /></i>
                  <small>Largest holding</small>
                </div>
                <div>
                  <div><span>Top three holdings</span><strong>{concentration.top_three_weight.toFixed(1)}%</strong></div>
                  <i><b style={{ width: `${Math.min(concentration.top_three_weight, 100)}%` }} /></i>
                  <small>Combined influence</small>
                </div>
                <div>
                  <div><span>{concentration.largest_sector}</span><strong>{concentration.largest_sector_weight.toFixed(1)}%</strong></div>
                  <i><b style={{ width: `${Math.min(concentration.largest_sector_weight, 100)}%` }} /></i>
                  <small>Largest sector</small>
                </div>
              </div>
              <div className="effective-note"><Target size={17} /><span>Your {summary.holdings_count} positions behave like <strong>{concentration.effective_holdings.toFixed(1)} equally sized holdings</strong>.</span></div>
            </article>

            <article className="panel deep-panel" id="risk">
              <div className="panel-heading">
                <div><h3><ShieldCheck size={18} />Structural risk breakdown</h3><p>Weighted exposure heuristic · not a return or volatility forecast</p></div>
                <span className={`status-badge status-${structuralRiskLevel.toLowerCase()}`}>{structuralRiskLevel} · {summary.risk_score}/100</span>
              </div>
              {risk_methodology && (
                <div className="risk-methodology-note">
                  <Gauge size={17} />
                  <div>
                    <strong>What this score means</strong>
                    <span>{risk_methodology.summary}</span>
                    <small>{risk_methodology.performance_context}</small>
                  </div>
                </div>
              )}
              <div className="risk-factor-list">
                {risk_breakdown.map((factor) => (
                  <div className="risk-factor" key={factor.name}>
                    <div>
                      <span>{factor.name}{factor.weight != null && <em>{factor.weight}% weight</em>}</span>
                      <strong className={`level-${factor.level.toLowerCase()}`}>{factor.level}</strong>
                    </div>
                    <i><b style={{ width: `${factor.score}%` }} /></i>
                    <div className="risk-factor-detail">
                      <small>{factor.detail}</small>
                      {factor.contribution != null && <small>{factor.score.toFixed(1)} × {factor.weight}% = <b>{factor.contribution.toFixed(1)} points</b></small>}
                    </div>
                  </div>
                ))}
              </div>
              {risk_methodology && <p className="risk-formula"><strong>Formula:</strong> {risk_methodology.formula}. {risk_methodology.disclaimer}</p>}
            </article>
          </section>

          <section className="analysis-wide-grid">
            <article className="panel contribution-panel">
              <div className="panel-heading"><div><h3><BarChart3 size={18} />Return contribution</h3><p>Percentage points added to or removed from total portfolio return</p></div></div>
              <div className="contribution-chart">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={contributionData} layout="vertical" margin={{ top: 8, right: 16, left: 4, bottom: 0 }}>
                    <CartesianGrid stroke="#1c3028" horizontal={false} />
                    <XAxis type="number" tick={{ fill: '#70887d', fontSize: 10 }} axisLine={false} tickLine={false} tickFormatter={(value) => `${value}%`} />
                    <YAxis type="category" dataKey="name" width={76} tick={{ fill: '#9aafa5', fontSize: 10 }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ background: '#10241b', border: '1px solid #244035', borderRadius: 12 }} formatter={(value, _name, item) => [`${value.toFixed(2)} pp · ${money.format(item.payload.pnl)}`, 'Contribution']} />
                    <Bar dataKey="contribution" radius={[0, 5, 5, 0]}>
                      {contributionData.map((item) => <Cell key={item.name} fill={item.contribution >= 0 ? '#39e58c' : '#ff6d85'} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>
            <StressLab summary={summary} concentration={concentration} />
          </section>

          <section className="panel scenario-panel">
            <div className="panel-heading"><div><h3><Gauge size={18} />Preset stress scenarios</h3><p>Fast sensitivity checks using your current portfolio weights</p></div><span className="local-badge">NO API COST</span></div>
            <div className="scenario-grid">
              {stress_scenarios.map((scenario) => (
                <article key={scenario.name}>
                  <span>{scenario.name}</span>
                  <strong>{scenario.portfolio_impact_percentage.toFixed(2)}%</strong>
                  <small>{money.format(scenario.estimated_change)} estimated impact</small>
                  <p>{scenario.description}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="panel sector-performance-panel">
            <div className="panel-heading"><div><h3><PieChartIcon size={18} />Sector performance</h3><p>Allocation and return quality by sector</p></div></div>
            <div className="table-wrap sector-table-wrap">
              <table>
                <thead><tr><th>Sector</th><th>Weight</th><th>Invested</th><th>Current value</th><th>P&amp;L</th><th>Return</th></tr></thead>
                <tbody>
                  {sector_performance.map((sector) => (
                    <tr key={sector.name}>
                      <td><strong>{sector.name}</strong></td>
                      <td>{sector.weight.toFixed(1)}%</td>
                      <td>{compactMoney.format(sector.invested_value)}</td>
                      <td>{compactMoney.format(sector.current_value)}</td>
                      <td className={sector.pnl >= 0 ? 'positive' : 'negative'}>{sector.pnl >= 0 ? '+' : ''}{compactMoney.format(sector.pnl)}</td>
                      <td><span className={sector.return_percentage >= 0 ? 'return positive' : 'return negative'}>{sector.return_percentage >= 0 ? '+' : ''}{sector.return_percentage.toFixed(2)}%</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <PortfolioReport
            key={portfolioReportCacheKey(portfolio)}
            portfolio={portfolio}
            publicDemoMode={PUBLIC_DEMO_MODE}
          />

          <section className="lower-grid">
            <article className="panel holdings-panel" id="holdings">
              <div className="panel-heading"><div><h3>Your holdings</h3><p>Position-level portfolio breakdown</p></div><button className="text-button">View all</button></div>
              <div className="table-wrap">
                <table>
                  <thead><tr><th>Company</th><th>Value</th><th>Weight</th><th>Avg. price</th><th>LTP</th><th>Returns</th><th>Contribution</th><th>Move to avg.</th></tr></thead>
                  <tbody>
                    {visibleHoldings.slice(0, 6).map((item) => (
                      <tr key={item.symbol}>
                        <td><div className="company-cell"><span>{item.symbol.slice(0, 2)}</span><div><strong>{item.symbol}</strong><small>{item.company}</small></div></div></td>
                        <td>{compactMoney.format(item.current_value)}</td>
                        <td><div className="weight-cell"><span>{item.weight.toFixed(1)}%</span><i><b style={{ width: `${Math.min(item.weight * 3.2, 100)}%` }} /></i></div></td>
                        <td>{money.format(item.average_price)}</td>
                        <td>{money.format(item.current_price)}</td>
                        <td><span className={item.return_percentage >= 0 ? 'return positive' : 'return negative'}>{item.return_percentage >= 0 ? '+' : ''}{item.return_percentage.toFixed(2)}%</span></td>
                        <td className={item.return_contribution >= 0 ? 'positive' : 'negative'}>{item.return_contribution >= 0 ? '+' : ''}{item.return_contribution.toFixed(2)} pp</td>
                        <td>{item.move_to_break_even >= 0 ? '+' : ''}{item.move_to_break_even.toFixed(2)}%</td>
                      </tr>
                    ))}
                    {!visibleHoldings.length && <tr><td colSpan="8" className="empty-search">No holdings match “{searchTerm}”.</td></tr>}
                  </tbody>
                </table>
              </div>
            </article>

            <article className="panel insights-panel" id="insights">
              <div className="panel-heading"><div><h3><Sparkles size={18} />Smart portfolio insights</h3><p>Calculated locally from your verified holdings</p></div><span className="local-badge">LOCAL</span></div>
              <div className="score-card"><div className="score-ring" style={{ '--score': `${summary.diversification_score * 3.6}deg` }}><div><strong>{Math.round(summary.diversification_score)}</strong><span>/100</span></div></div><div><span>Diversification score</span><strong>{summary.diversification_score >= 70 ? 'Well balanced' : 'Can be improved'}</strong><small>Based on holdings and sector spread</small></div></div>
              <div className="insight-list">
                {insights.map((insight) => (
                  <div className={`insight ${insight.type}`} key={insight.title}>
                    <span>{insight.type === 'positive' ? <ShieldCheck size={17} /> : insight.type === 'warning' ? <Gauge size={17} /> : <Activity size={17} />}</span>
                    <div><strong>{insight.title}</strong><p>{insight.message}</p></div>
                  </div>
                ))}
              </div>
            </article>
          </section>
          <footer>PortfolioLens provides educational analytics, not investment advice.</footer>
        </div>
      </main>
    </div>
  )
}

export default App
