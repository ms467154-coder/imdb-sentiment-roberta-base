import { FormEvent, useMemo, useState } from 'react'
import { ArrowRight, CheckCircle2, FileSpreadsheet, Loader2, Upload, XCircle } from 'lucide-react'
import { predictSentiment, PredictionResponse } from './services/api'

type BatchResult = { file_name: string; text_column: string; columns: string[]; rows: Array<Record<string, unknown>>; rows_processed: number }
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export default function App() {
  const [tab, setTab] = useState<'single' | 'batch'>('single')
  const [text, setText] = useState('')
  const [singleResult, setSingleResult] = useState<PredictionResponse | null>(null)
  const [singleError, setSingleError] = useState('')
  const [loading, setLoading] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [textColumn, setTextColumn] = useState('')
  const [batch, setBatch] = useState<BatchResult | null>(null)
  const [batchError, setBatchError] = useState('')
  const [batchLoading, setBatchLoading] = useState(false)

  async function submitSingle(event: FormEvent) {
    event.preventDefault(); setSingleError(''); setSingleResult(null)
    if (!text.trim()) { setSingleError('Enter a review first.'); return }
    setLoading(true)
    try { setSingleResult(await predictSentiment(text)) } catch (error) { setSingleError(error instanceof Error ? error.message : 'Model inference failed.') } finally { setLoading(false) }
  }

  async function submitBatch(event: FormEvent) {
    event.preventDefault(); setBatchError(''); setBatch(null)
    if (!file) { setBatchError('Choose a CSV, Excel, or JSON file first.'); return }
    setBatchLoading(true)
    try {
      const body = new FormData(); body.append('file', file); if (textColumn) body.append('text_column', textColumn)
      const response = await fetch(`${API_BASE_URL}/api/batch-predict`, { method: 'POST', body })
      const payload = await response.json()
      if (!response.ok) throw new Error(payload.detail || 'Batch analysis failed.')
      setBatch(payload as BatchResult)
    } catch (error) { setBatchError(error instanceof Error ? error.message : 'Batch analysis failed.') } finally { setBatchLoading(false) }
  }

  const download = (format: 'json' | 'csv') => {
    if (!batch) return
    const rows = batch.rows
    const content = format === 'json' ? JSON.stringify(rows, null, 2) : [batch.columns.join(','), ...rows.map(row => batch.columns.map(column => JSON.stringify(row[column] ?? '')).join(','))].join('\n')
    const blob = new Blob([content], { type: format === 'json' ? 'application/json' : 'text/csv' }); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = `imdb-sentiment-results.${format}`; link.click(); URL.revokeObjectURL(link.href)
  }

  const columns = useMemo(() => batch?.columns.filter(column => !['prediction', 'confidence', 'error', 'row_number'].includes(column)) || [], [batch])
  return <div className="app-shell"><header className="topbar"><div className="brand"><span className="brand-mark">AI</span><span><strong>IMDB / SENTIMENT</strong><small>RoBERTa-base inference lab</small></span></div><nav><button className={tab === 'single' ? 'nav-link active' : 'nav-link'} onClick={() => setTab('single')}>Single review</button><button className={tab === 'batch' ? 'nav-link active' : 'nav-link'} onClick={() => setTab('batch')}>Batch files</button></nav><span className="model-badge">MODEL READY / RoBERTa-base</span></header><main className="page-section"><div className="eyebrow">TRANSFORMER NLP / PRODUCTION INFERENCE</div><h1>Read the <em>signal.</em></h1><p className="intro-text">Analyze one review or upload a dataset and receive an honest sentiment prediction for every sentence.</p>{tab === 'single' ? <section className="workspace"><form className="review-card" onSubmit={submitSingle}><div className="card-topline"><span>SINGLE REVIEW</span><span>{text.length} / 5,000</span></div><textarea value={text} onChange={e => setText(e.target.value)} placeholder="Paste an IMDB-style movie review here..." maxLength={5000} /><div className="button-row"><button className="primary-button" disabled={loading}>{loading ? <><Loader2 className="spin" size={17} /> Analyzing...</> : <>Analyze sentiment <ArrowRight size={17} /></>}</button><button className="secondary-button" type="button" onClick={() => { setText(''); setSingleResult(null); setSingleError('') }}>Clear</button></div>{singleError && <p className="error-message"><XCircle size={17} />{singleError}</p>}</form><div className="result-card">{singleResult ? <><span className="eyebrow">PREDICTION RESULT</span><h2 className={singleResult.sentiment === 'Positive' ? 'positive' : 'negative'}>{singleResult.sentiment}</h2><p>Confidence: <strong>{singleResult.confidence === null ? 'Unavailable' : `${Math.round(singleResult.confidence * 100)}%`}</strong></p><p className="muted">Using the preserved notebook-compatible preprocessing and checkpoint.</p></> : <><div className="result-orb">+</div><h2>Your result appears here.</h2><p className="muted">The saved RoBERTa model will classify the review without changing the original ML pipeline.</p></>}</div></section> : <section className="batch-section"><form className="upload-card" onSubmit={submitBatch}><label className="dropzone"><Upload size={26} /><strong>{file ? file.name : 'Choose a dataset file'}</strong><span>CSV, XLSX, XLS, or JSON</span><input type="file" accept=".csv,.xlsx,.xls,.json" onChange={e => { setFile(e.target.files?.[0] || null); setBatch(null); setBatchError('') }} /></label>{file && <label className="field-label">Text column (optional; auto-detects review, text, sentence, comment, or content)<select value={textColumn} onChange={e => setTextColumn(e.target.value)}><option value="">Auto-detect text column</option>{columns.map(column => <option key={column} value={column}>{column}</option>)}</select></label>}<button className="primary-button" disabled={batchLoading}>{batchLoading ? <><Loader2 className="spin" /> Analyzing every row...</> : <>Analyze every row <ArrowRight size={17} /></>}</button>{batchError && <p className="error-message"><XCircle size={17} />{batchError}</p>}</form>{batch && <div className="table-card"><div className="table-header"><div><span className="eyebrow">BATCH RESULTS</span><h2>{batch.rows_processed} rows analyzed</h2><p>Text column: <strong>{batch.text_column}</strong></p></div><div className="button-row"><button className="secondary-button" onClick={() => download('csv')}>Download CSV</button><button className="secondary-button" onClick={() => download('json')}>Download JSON</button></div></div><div className="table-scroll"><table><thead><tr>{batch.columns.map(column => <th key={column}>{column}</th>)}</tr></thead><tbody>{batch.rows.map((row, index) => <tr key={index}>{batch.columns.map(column => <td key={column}>{column === 'prediction' ? <span className={row[column] === 'Positive' ? 'pill positive-pill' : row[column] === 'Negative' ? 'pill negative-pill' : 'pill'}>{String(row[column] ?? '')}</span> : column === 'confidence' && typeof row[column] === 'number' ? `${Math.round(Number(row[column]) * 100)}%` : String(row[column] ?? '')}</td>)}</tr>)}</tbody></table></div></div>}</section>}</main><footer><span>IMDB SENTIMENT ANALYSIS / RoBERTa-base</span><span><CheckCircle2 size={13} /> Original model preserved</span></footer></div>
}
