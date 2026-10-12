import { FormEvent, useEffect, useState } from 'react'

type RunStatus = 'BACKTEST_READY' | 'RUNNING' | 'FAILED' | 'QUEUED' | 'RISK_READY'

type ResearchForm = {
  query: string
  symbols: string
  startDate: string
  endDate: string
  initialCapital: string
}

type RunResult = {
  status: RunStatus
  strategyName: string
  totalReturn: number
  benchmarkReturn: number
  maxDrawdown: number
  sharpe: number
  finalEquity: number
  equityCurve: number[]
}

type HistoryItem = {
  research_id: string
  status: RunStatus
  query: string
  strategy_name?: string
  symbols: string[]
  submitted_at: string
  total_return?: number
}

const demoResult: RunResult = {
  status: 'BACKTEST_READY',
  strategyName: 'Volatility-Filtered Momentum',
  totalReturn: 0.284,
  benchmarkReturn: 0.196,
  maxDrawdown: -0.117,
  sharpe: 1.42,
  finalEquity: 128420,
  equityCurve: [100, 102, 101, 106, 109, 107, 113, 116, 114, 121, 119, 126, 128],
}

const initialForm: ResearchForm = {
  query: 'Find a momentum strategy with a volatility filter',
  symbols: 'AAPL, MSFT, NVDA',
  startDate: '2020-01-01',
  endDate: '2026-01-01',
  initialCapital: '100000',
}

const agents = [
  ['01', 'Market data', 'Historical prices and features'],
  ['02', 'Research / RAG', 'Relevant strategy evidence'],
  ['03', 'Strategy', 'Validated strategy DSL'],
  ['04', 'Backtest', 'Returns, costs, benchmark'],
  ['05', 'Risk', 'Portfolio risk diagnostics'],
]

function formatPercent(value: number) {
  return `${value >= 0 ? '+' : ''}${(value * 100).toFixed(1)}%`
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
}

function formatRunDate(value: string) {
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
}

function EquityChart({ values }: { values: number[] }) {
  const min = Math.min(...values) - 2
  const max = Math.max(...values) + 2
  const points = values.map((value, index) => `${(index / (values.length - 1)) * 100},${100 - ((value - min) / (max - min)) * 100}`).join(' ')

  return (
    <div className="chart-wrap">
      <div className="chart-labels"><span>$130k</span><span>$115k</span><span>$100k</span></div>
      <svg className="equity-chart" viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label="Strategy equity curve">
        <defs>
          <linearGradient id="fill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#b5e85c" stopOpacity="0.32" />
            <stop offset="100%" stopColor="#b5e85c" stopOpacity="0" />
          </linearGradient>
        </defs>
        <line x1="0" y1="75" x2="100" y2="75" className="grid-line" />
        <line x1="0" y1="50" x2="100" y2="50" className="grid-line" />
        <line x1="0" y1="25" x2="100" y2="25" className="grid-line" />
        <polygon points={`0,100 ${points} 100,100`} fill="url(#fill)" />
        <polyline points={points} className="curve-line" />
      </svg>
      <div className="chart-dates"><span>Jan 20</span><span>Jan 22</span><span>Jan 24</span><span>Jan 26</span></div>
    </div>
  )
}

function App() {
  const [form, setForm] = useState(initialForm)
  const [result, setResult] = useState<RunResult>(demoResult)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [notice, setNotice] = useState('Demo result loaded')
  const apiBase = import.meta.env.VITE_API_URL ?? ''

  async function refreshHistory() {
    const response = await fetch(`${apiBase}/api/v1/research?limit=5`)
    if (!response.ok) throw new Error('Unable to load research history')
    setHistory(await response.json())
  }

  useEffect(() => {
    refreshHistory().catch(() => setNotice('Research history unavailable - showing the demo workspace'))
  }, [])

  const updateField = (field: keyof ResearchForm, value: string) => setForm((current) => ({ ...current, [field]: value }))

  async function runResearch(event: FormEvent) {
    event.preventDefault()
    setResult({ ...demoResult, status: 'RUNNING' })
    setNotice('Running research graph...')
    const payload = {
      query: form.query,
      symbols: form.symbols.split(',').map((symbol) => symbol.trim()).filter(Boolean),
      start_date: form.startDate,
      end_date: form.endDate,
      initial_capital: Number(form.initialCapital),
      volatility_window: 20,
      momentum_window: 20,
      top_k: 5,
      slippage_bps: 2,
    }

    try {
      const response = await fetch(`${apiBase}/api/v1/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!response.ok) throw new Error('API request failed')
      const queued = await response.json()
      const researchId = queued.research_id
      if (!researchId) throw new Error('Gateway did not return a research ID')

      for (let attempt = 0; attempt < 120; attempt += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 1500))
        const statusResponse = await fetch(`${apiBase}/api/v1/research/${researchId}`)
        if (!statusResponse.ok) throw new Error('Unable to read research status')
        const latest = await statusResponse.json()
        if (latest.status !== 'QUEUED' && latest.status !== 'RUNNING') {
          setResult({ ...demoResult, ...latest, status: latest.status ?? 'BACKTEST_READY' })
          setNotice(latest.status === 'FAILED' ? 'Research run failed' : 'Research run completed')
          refreshHistory().catch(() => undefined)
          return
        }
      }
      throw new Error('Research run timed out')
    } catch {
      setResult({ ...demoResult, status: 'FAILED' })
      setNotice('API unavailable - showing the latest demo run')
    }
  }

  const isRunning = result.status === 'RUNNING'

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">Q</span><span>quant / lab</span></div>
        <div className="workspace-switcher"><span className="status-dot" /> Research workspace <span className="chevron">v</span></div>
        <nav className="nav-list" aria-label="Primary navigation">
          <a className="nav-item active" href="#overview"><span>+</span> Overview</a>
          <a className="nav-item" href="#runs"><span>↗</span> Research runs <b>12</b></a>
          <a className="nav-item" href="#strategies"><span>◇</span> Strategies</a>
          <a className="nav-item" href="#knowledge"><span>▤</span> Knowledge base</a>
        </nav>
        <div className="sidebar-bottom"><div className="api-status"><span className="status-dot" /> AI engine connected</div><div className="user-chip"><span>HR</span><div><strong>Himan R.</strong><small>Engineer</small></div><span className="more">...</span></div></div>
      </aside>

      <main className="main-content" id="overview">
        <header className="topbar"><div className="breadcrumb">Research workspace <span>/</span> Overview</div><div className="top-actions"><button className="icon-button" aria-label="Notifications">*</button><button className="avatar">HR</button></div></header>
        <section className="page-heading"><div><p className="eyebrow">AI QUANT RESEARCH PLATFORM <span className="live-pill"><i /> LIVE</span></p><h1>Research, then<br /><em>trade with evidence.</em></h1><p className="lede">Compose a research question and let the agent graph turn market data, evidence, and deterministic backtests into one auditable decision.</p></div><div className="heading-note"><span>LAST RUN</span><strong>Today, 09:42</strong><small>12 completed runs this month</small></div></section>

        <section className="workbench-grid">
          <form className="composer-panel panel" onSubmit={runResearch}>
            <div className="panel-header"><div><span className="panel-kicker">01 / NEW RESEARCH</span><h2>Define your question</h2></div><span className="shortcut">⌘ ↵</span></div>
            <label>Research question<textarea value={form.query} onChange={(event) => updateField('query', event.target.value)} rows={3} /></label>
            <label>Universe <input value={form.symbols} onChange={(event) => updateField('symbols', event.target.value)} /></label>
            <div className="form-row"><label>From <input type="date" value={form.startDate} onChange={(event) => updateField('startDate', event.target.value)} required /></label><label>To <input type="date" value={form.endDate} onChange={(event) => updateField('endDate', event.target.value)} required /></label></div>
            <label>Initial capital <div className="input-prefix"><span>$</span><input value={form.initialCapital} onChange={(event) => updateField('initialCapital', event.target.value)} /></div></label>
            <button className="run-button" disabled={isRunning}>{isRunning ? 'Running agent graph...' : 'Run research'} <span>↗</span></button>
            <p className="form-footnote">Uses historical market data, RAG evidence, strategy DSL validation, and a one-bar execution lag.</p>
          </form>

          <section className="results-panel panel" id="runs">
            <div className="panel-header result-header"><div><span className="panel-kicker">02 / LATEST RESULT</span><h2>{result.status === 'RUNNING' ? 'Research in progress' : result.strategyName}</h2></div><span className={`run-state ${result.status.toLowerCase()}`}><i /> {result.status.replace('_', ' ')}</span></div>
            {result.status === 'RUNNING' ? <div className="loading-state"><div className="loading-bar" /><p>Agents are moving through the research graph.</p></div> : <><div className="metric-grid"><div className="metric"><span>Total return</span><strong className="positive">{formatPercent(result.totalReturn)}</strong><small>vs {formatPercent(result.benchmarkReturn)} benchmark</small></div><div className="metric"><span>Final equity</span><strong>{formatCurrency(result.finalEquity)}</strong><small>on {form.initialCapital} initial</small></div><div className="metric"><span>Max drawdown</span><strong className="negative">{formatPercent(result.maxDrawdown)}</strong><small>peak to trough</small></div><div className="metric"><span>Sharpe ratio</span><strong>{result.sharpe.toFixed(2)}</strong><small>4% risk-free rate</small></div></div><div className="chart-header"><span>Portfolio growth</span><span className="legend"><i className="legend-strategy" /> Strategy <i className="legend-benchmark" /> Benchmark</span></div><EquityChart values={result.equityCurve} /></>}
          </section>
        </section>

        <section className="lower-grid"><section className="pipeline-panel panel"><div className="panel-header"><div><span className="panel-kicker">03 / AGENT GRAPH</span><h2>Research pipeline</h2></div><span className="muted">5 agents</span></div><div className="pipeline-list">{agents.map(([number, name, detail], index) => <div className="pipeline-row" key={name}><span className={`agent-number ${index < 4 ? 'complete' : ''}`}>{index < 4 ? '✓' : number}</span><div><strong>{name}</strong><small>{detail}</small></div><span className={index < 4 ? 'agent-done' : 'agent-wait'}>{index < 4 ? 'READY' : 'QUEUED'}</span></div>)}</div></section><section className="runs-panel panel"><div className="panel-header"><div><span className="panel-kicker">04 / ACTIVITY</span><h2>Recent runs</h2></div><a href="#runs" className="view-all">View all ↗</a></div>{history.length === 0 ? <div className="empty-history">No persisted research runs yet.</div> : history.map((item, index) => <div className="recent-run" key={item.research_id}><div className={`run-icon ${index % 3 === 1 ? 'blue' : index % 3 === 2 ? 'orange' : ''}`}>{item.strategy_name?.slice(0, 2).toUpperCase() ?? 'RQ'}</div><div><strong>{item.strategy_name ?? item.query}</strong><small>{item.symbols.join(', ')} <span>·</span> {formatRunDate(item.submitted_at)}</small></div><span className={`run-return ${item.total_return !== undefined && item.total_return < 0 ? 'negative-text' : ''}`}>{item.total_return === undefined ? item.status : formatPercent(item.total_return)}</span></div>)}</section></section>
        <footer><span>{notice}</span><span>Data refreshes on each research run <b>·</b> v0.1 workbench</span></footer>
      </main>
    </div>
  )
}

export default App