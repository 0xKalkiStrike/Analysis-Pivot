import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import {
  Database, FileSpreadsheet, Copy, ShieldCheck, Table, Network,
<<<<<<< HEAD
  Terminal, Sparkles, Search, Play, ExternalLink, RefreshCw,
  Bookmark, Command as CommandIcon, ArrowRight, Zap, BarChart3,
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const PALETTE = ["#7c5cff", "#b06bff", "#5bd4ff", "#4be0a8", "#ffb84b", "#ff6b6b", "#c9b6ff", "#f38bff"];

// ─────────────────────────────────────────────────────────────────────────── KPI
function Kpi({ label, value, accent, icon: Icon }) {
  return (
    <div
      data-testid={`kpi-${label.toLowerCase().replace(/\s+/g, "-")}`}
      className="relative overflow-hidden rounded-2xl border border-white/10 bg-[#171727] p-5 transition hover:border-white/20"
    >
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-medium uppercase tracking-widest text-white/50">{label}</span>
        {Icon && <Icon size={16} className="text-white/40" />}
      </div>
      <div className="mt-3 text-3xl font-bold tabular-nums" style={{ color: accent }}>
        {value}
      </div>
      <div className="pointer-events-none absolute -right-6 -bottom-6 h-24 w-24 rounded-full opacity-20 blur-2xl"
           style={{ background: accent }} />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────── section
function Section({ title, subtitle, icon: Icon, children, right }) {
  return (
    <section className="rounded-3xl border border-white/10 bg-[#12121c]/70 p-6 backdrop-blur">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {Icon && (
            <div className="rounded-lg bg-gradient-to-br from-[#5b4be0] to-[#b06bff] p-2 text-white shadow-lg shadow-purple-900/50">
              <Icon size={18} />
            </div>
          )}
          <div>
            <h2 className="text-lg font-semibold text-white">{title}</h2>
            {subtitle && <p className="text-xs text-white/50">{subtitle}</p>}
          </div>
        </div>
        {right}
      </div>
      {children}
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────── formatters
const fmtNum = (n) =>
  n == null ? "—" : n.toLocaleString(undefined, { maximumFractionDigits: 2 });

// ─────────────────────────────────────────────────────────────────────────── main
=======
  Search, Play, RefreshCw, Command as CommandIcon, ArrowRight,
  Upload, Download, Grid, Layers, CheckCircle2, Pause, Square, Sparkles,
  AlertTriangle, FileText, Settings, HelpCircle, Check, Trash2, Folder, FolderPlus,
  Crown, GitPullRequest, Sliders, ChevronDown, ChevronRight, Filter, Cpu, HardDrive, BarChart3, Activity
} from "lucide-react";

const API_BASE = process.env.REACT_APP_BACKEND_URL || (window.location.origin.includes('3000') ? 'http://localhost:8000' : window.location.origin);
const API = `${API_BASE}/api`;

const fmtNum = (n) => (n == null ? "—" : n.toLocaleString());

>>>>>>> a4386bf (Initial commit)
export default function ExcelIntelDashboard() {
  const [samples, setSamples] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedSheet, setSelectedSheet] = useState(null);
  const [summary, setSummary] = useState(null);
  const [dataset, setDataset] = useState(null);
  const [duplicates, setDuplicates] = useState(null);
  const [relationships, setRelationships] = useState(null);
<<<<<<< HEAD
  const [threshold, setThreshold] = useState(90);
  const [search, setSearch] = useState("");
  const [loadingDup, setLoadingDup] = useState(false);
  const [tab, setTab] = useState("data");
  const [paletteOpen, setPaletteOpen] = useState(false);

=======
  const [threshold, setThreshold] = useState(88);
  const [search, setSearch] = useState("");
  const [loadingDup, setLoadingDup] = useState(false);
  const [tab, setTab] = useState("master_mdm");
  const [paletteOpen, setPaletteOpen] = useState(false);

  // Features state
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [pivotRows, setPivotRows] = useState([]);
  const [pivotCols, setPivotCols] = useState([]);
  const [pivotVal, setPivotVal] = useState("");
  const [pivotAgg, setPivotAgg] = useState("sum");
  const [pivotResult, setPivotResult] = useState(null);
  const [loadingPivot, setLoadingPivot] = useState(false);
  const [validationData, setValidationData] = useState(null);
  const [loadingValidation, setLoadingValidation] = useState(false);

  // Consolidation & Merge state
  const [mergedData, setMergedData] = useState(null);
  const [loadingMerge, setLoadingMerge] = useState(false);

  // Cross-Sheet Matching state
  const [crossMatchedData, setCrossMatchedData] = useState(null);
  const [loadingCrossMatch, setLoadingCrossMatch] = useState(false);

  // Advanced MDM Engine state
  const [discoveryReport, setDiscoveryReport] = useState(null);
  const [loadingDiscovery, setLoadingDiscovery] = useState(false);
  const [jobStatus, setJobStatus] = useState("idle"); // idle | running | paused | completed | cancelled | error
  const [jobPercent, setJobPercent] = useState(0);
  const [jobStage, setJobStage] = useState("");
  const [jobCurrentFile, setJobCurrentFile] = useState("");
  const [jobStats, setJobStats] = useState({});
  const [jobResult, setJobResult] = useState(null);
  const [jobError, setJobError] = useState(null);
  const [columnAliases, setColumnAliases] = useState({});
  const [showAliasesModal, setShowAliasesModal] = useState(false);
  const [newCanonical, setNewCanonical] = useState("Name");
  const [newAlias, setNewAlias] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  // MDM Specific State
  const [matchingRules, setMatchingRules] = useState([]);
  const [selectedRuleId, setSelectedRuleId] = useState("rule_1");
  const [expandedMasterId, setExpandedMasterId] = useState(null);
  const [mdmSearch, setMdmSearch] = useState("");
  const [mdmFilterCity, setMdmFilterCity] = useState("");
  const [mdmFilterState, setMdmFilterState] = useState("");
  const [mdmMinDuplicates, setMdmMinDuplicates] = useState("0");
  const [refSearch, setRefSearch] = useState("");

>>>>>>> a4386bf (Initial commit)
  // Boot
  useEffect(() => {
    axios.get(`${API}/samples`).then((res) => {
      setSamples(res.data.files);
      if (res.data.files.length) {
        const f = res.data.files[0];
        setSelectedFile(f.name);
        setSelectedSheet(f.sheets?.[0] || null);
      }
<<<<<<< HEAD
    });
    axios.get(`${API}/summary`).then((res) => setSummary(res.data));
    axios.get(`${API}/relationships`).then((res) => setRelationships(res.data));
  }, []);

  // When file changes, load dataset preview
  useEffect(() => {
    if (!selectedFile) return;
    setDataset(null); setDuplicates(null);
    axios.get(`${API}/dataset`, { params: { file: selectedFile, sheet: selectedSheet, limit: 60 } })
      .then((res) => setDataset(res.data));
=======
    }).catch(err => console.error("Error fetching samples:", err));

    axios.get(`${API}/summary`).then((res) => setSummary(res.data)).catch(() => {});
    axios.get(`${API}/relationships`).then((res) => setRelationships(res.data)).catch(() => {});
    axios.get(`${API}/mdm/matching-rules`).then((res) => setMatchingRules(res.data.rules || [])).catch(() => {});
    fetchDiscoveryReport();
    fetchAliases();
    startMDMAnalysis("rule_1");
  }, []);

  // Poll Job Status when job is running or paused
  useEffect(() => {
    let timer;
    if (jobStatus === "running" || jobStatus === "paused") {
      timer = setInterval(() => {
        axios.get(`${API}/job/status`).then((res) => {
          const data = res.data;
          setJobStatus(data.status);
          setJobPercent(data.percent || 0);
          setJobStage(data.stage || "");
          setJobCurrentFile(data.current_file || "");
          setJobStats(data.stats || {});
          if (data.result) setJobResult(data.result);
          if (data.error) setJobError(data.error);
        }).catch(() => {});
      }, 700);
    }
    return () => clearInterval(timer);
  }, [jobStatus]);

  // When file changes, load dataset preview & reset default pivot fields
  useEffect(() => {
    if (!selectedFile) return;
    setDataset(null); setDuplicates(null); setPivotResult(null); setValidationData(null);
    axios.get(`${API}/summary`, { params: { file: selectedFile, sheet: selectedSheet } })
      .then((res) => setSummary(res.data)).catch(() => {});
    axios.get(`${API}/dataset`, { params: { file: selectedFile, sheet: selectedSheet, limit: 100 } })
      .then((res) => {
        setDataset(res.data);
        if (res.data?.columns?.length) {
          setPivotRows([res.data.columns[0]]);
          const numericCol = res.data.columns.find((c) => res.data.dtypes[c]?.includes("float") || res.data.dtypes[c]?.includes("int"));
          setPivotVal(numericCol || res.data.columns[1] || "");
        }
      }).catch(err => console.error("Error loading dataset:", err));
>>>>>>> a4386bf (Initial commit)
  }, [selectedFile, selectedSheet]);

  // Keyboard shortcut for palette
  useEffect(() => {
    const h = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "p") {
        e.preventDefault(); setPaletteOpen(true);
      }
      if (e.key === "Escape") setPaletteOpen(false);
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);

<<<<<<< HEAD
  const runDuplicates = async () => {
    if (!selectedFile) return;
    setLoadingDup(true);
    try {
      const res = await axios.get(`${API}/duplicates`, {
        params: { file: selectedFile, sheet: selectedSheet, threshold, clean: true },
      });
      setDuplicates(res.data);
      setTab("duplicates");
    } finally {
      setLoadingDup(false);
    }
  };

  const filteredRows = useMemo(() => {
    if (!dataset) return [];
    if (!search.trim()) return dataset.preview;
    const q = search.trim().toLowerCase();
    return dataset.preview.filter((row) =>
      Object.values(row).some((v) => v != null && String(v).toLowerCase().includes(q))
    );
  }, [dataset, search]);

  const kpis = summary?.kpis;
  const perSheet = summary?.per_sheet?.map((s) => ({
    name: s.name.split(" :: ")[0].replace(".xlsx", "").replace(".csv", ""),
    rows: s.rows,
  })) || [];
  const composition = (summary?.quality_composition || []).filter((c) => c.value > 0);

  return (
    <div className="min-h-screen bg-[#0a0a10] text-white antialiased">
      {/* Grain overlay */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 opacity-[0.04] mix-blend-overlay"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'><filter id='n'><feTurbulence baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>\")",
        }}
      />

      {/* Top bar */}
      <header
        data-testid="app-header"
        className="sticky top-0 z-40 border-b border-white/10 bg-[#0a0a10]/85 backdrop-blur-xl"
      >
        <div className="mx-auto flex max-w-[1600px] items-center gap-5 px-6 py-3">
          <div className="flex items-center gap-2">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-[#5b4be0] to-[#b06bff] shadow-lg shadow-purple-900/50">
              <Sparkles size={18} />
            </div>
            <div className="leading-tight">
              <div className="text-sm font-semibold tracking-tight">ExcelIntel</div>
              <div className="text-[11px] text-white/50">Enterprise Excel Analytics · offline</div>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-2 text-[11px] text-white/50">
            <span className="rounded-full bg-white/5 px-2 py-1">v1.2</span>
            <span className="rounded-full bg-emerald-500/10 px-2 py-1 text-emerald-300">API online</span>
          </div>
          <div className="flex-1" />
          <button
            data-testid="open-palette-btn"
            onClick={() => setPaletteOpen(true)}
            className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-white/70 hover:bg-white/[0.06]"
          >
            <CommandIcon size={14} /> Command Palette
            <kbd className="ml-2 rounded bg-white/10 px-1.5 py-0.5 text-[10px]">Ctrl P</kbd>
          </button>
          <a
            href="https://github.com"
            className="hidden md:flex items-center gap-1 rounded-xl bg-white/5 px-3 py-1.5 text-xs text-white/70 hover:bg-white/10"
          >
            <ExternalLink size={13} /> Docs
          </a>
        </div>
      </header>

      <main className="mx-auto max-w-[1600px] px-6 py-8">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mb-8 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between"
        >
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[11px] text-white/60">
              <Zap size={11} className="text-[#c9b6ff]" /> Fully offline Power BI alternative
            </div>
            <h1 className="text-4xl font-bold tracking-tight md:text-5xl">
              <span className="bg-gradient-to-r from-white via-[#e6dfff] to-[#b06bff] bg-clip-text text-transparent">
                Analyze, clean & merge
              </span>
              <br />
              millions of spreadsheet rows.
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-white/60">
              This preview runs the same engines that power the ExcelIntel desktop app —
              duplicate detection, fuzzy matching, pivots, validation, relationship discovery.
              Everything is local, offline, and lightning fast.
            </p>
          </div>
          <div className="flex gap-3">
            <button
              data-testid="refresh-summary-btn"
              onClick={() =>
                axios.get(`${API}/summary`).then((r) => setSummary(r.data))
              }
              className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.05] px-4 py-2 text-sm hover:bg-white/[0.09]"
            >
              <RefreshCw size={14} /> Refresh
            </button>
            <button
              data-testid="scan-duplicates-btn"
              onClick={runDuplicates}
              disabled={loadingDup}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-br from-[#5b4be0] to-[#b06bff] px-4 py-2 text-sm font-medium shadow-lg shadow-purple-900/50 hover:brightness-110 disabled:opacity-60"
            >
              <Play size={14} /> {loadingDup ? "Scanning…" : "Scan Duplicates"}
            </button>
          </div>
        </motion.div>

        {/* KPIs */}
        <div className="mb-8 grid grid-cols-2 gap-4 md:grid-cols-4 xl:grid-cols-8">
          <Kpi label="Files" value={fmtNum(kpis?.files)} accent="#7c5cff" icon={FileSpreadsheet} />
          <Kpi label="Sheets" value={fmtNum(kpis?.sheets)} accent="#b06bff" icon={Database} />
          <Kpi label="Total Rows" value={fmtNum(kpis?.total_rows)} accent="#5bd4ff" icon={Table} />
          <Kpi label="Unique Rows" value={fmtNum(kpis?.unique_rows)} accent="#4be0a8" icon={Copy} />
          <Kpi label="Duplicates" value={fmtNum(kpis?.duplicate_rows)} accent="#ffb84b" icon={Copy} />
          <Kpi label="Missing Values" value={fmtNum(kpis?.missing_values)} accent="#ff6b6b" icon={ShieldCheck} />
          <Kpi label="Quality Score" value={kpis?.data_quality_score?.toFixed(1) ?? "—"} accent="#4be0a8" icon={ShieldCheck} />
          <Kpi label="Validation Score" value={kpis?.validation_score?.toFixed(1) ?? "—"} accent="#c9b6ff" icon={ShieldCheck} />
        </div>

        {/* Charts row */}
        <div className="mb-8 grid gap-5 lg:grid-cols-2">
          <Section title="Rows by Sheet" subtitle="Click a bar to activate that dataset" icon={BarChart3}>
            <BarsSVG
              data={perSheet}
              onBarClick={(entry) => {
                const match = samples.find((s) => s.name.startsWith(entry.name));
                if (match) {
                  setSelectedFile(match.name);
                  setSelectedSheet(match.sheets?.[0] || null);
                  setTab("data");
                }
              }}
            />
          </Section>

          <Section title="Data Quality Composition" subtitle="Uniques vs duplicates vs missing" icon={ShieldCheck}>
            <PieSVG data={composition} />
          </Section>
        </div>

        {/* Data explorer */}
        <div className="mb-8 grid gap-5 lg:grid-cols-[320px_1fr]">
          <Section title="Data Sources" subtitle="Sample datasets" icon={FileSpreadsheet}>
            <div data-testid="samples-list" className="flex flex-col gap-2">
              {samples.map((f) => (
                <button
                  key={f.name}
                  data-testid={`sample-${f.name}`}
                  onClick={() => {
                    setSelectedFile(f.name);
                    setSelectedSheet(f.sheets?.[0] || null);
                  }}
                  className={`group flex items-center justify-between rounded-xl border px-3 py-2 text-left text-sm transition ${
                    selectedFile === f.name
                      ? "border-[#7c5cff] bg-[#7c5cff]/10 text-white"
                      : "border-white/10 bg-white/[0.02] text-white/80 hover:border-white/20"
                  }`}
                >
                  <div className="flex flex-col">
                    <span className="font-medium">{f.name}</span>
                    <span className="text-[10px] text-white/40">
                      {(f.size / 1024).toFixed(1)} KB · {f.sheets?.length || 1} sheet(s)
                    </span>
                  </div>
                  <ArrowRight size={14} className="text-white/40 group-hover:text-white" />
                </button>
              ))}
            </div>
          </Section>

          <div className="flex flex-col gap-5">
            {/* Tabs */}
            <div className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.02] p-1.5">
              {[
                { id: "data", label: "Data", icon: Table },
                { id: "duplicates", label: "Duplicates", icon: Copy },
                { id: "relationships", label: "Relationships", icon: Network },
              ].map((t) => (
                <button
                  key={t.id}
                  data-testid={`tab-${t.id}`}
                  onClick={() => setTab(t.id)}
                  className={`flex items-center gap-2 rounded-xl px-4 py-1.5 text-sm transition ${
                    tab === t.id
                      ? "bg-white/[0.08] text-white shadow-inner shadow-white/10"
                      : "text-white/60 hover:text-white"
                  }`}
                >
                  <t.icon size={14} /> {t.label}
                </button>
              ))}
            </div>

            {tab === "data" && (
              <Section
                title={dataset?.name || "Data Preview"}
                subtitle={
                  dataset
                    ? `${fmtNum(dataset.rows)} rows × ${dataset.cols} columns · showing top ${dataset.preview.length}`
                    : "Pick a dataset from the left"
                }
                icon={Table}
                right={
                  <div className="relative">
                    <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" />
                    <input
                      data-testid="data-search"
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      placeholder="Search rows…"
                      className="rounded-xl border border-white/10 bg-white/[0.03] py-1.5 pl-8 pr-3 text-xs outline-none placeholder:text-white/40 focus:border-[#7c5cff]"
                    />
                  </div>
                }
              >
                <div data-testid="data-table" className="overflow-auto rounded-xl border border-white/10 bg-[#0f0f18]">
                  {dataset ? (
                    <table className="min-w-full text-xs">
                      <thead className="bg-[#1a1a2e] text-[#c9b6ff]">
                        <tr>
                          {dataset.columns.slice(0, 12).map((c) => (
                            <th key={c} className="border-b border-white/10 px-3 py-2 text-left font-semibold">
                              {c}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {filteredRows.slice(0, 40).map((row, i) => (
                          <tr key={i} className={i % 2 ? "bg-white/[0.02]" : ""}>
                            {dataset.columns.slice(0, 12).map((c) => (
                              <td key={c} className="border-b border-white/5 px-3 py-2 text-white/80">
                                {row[c] == null ? <span className="text-white/30">—</span> : String(row[c]).slice(0, 60)}
                              </td>
=======
  const fetchDiscoveryReport = async () => {
    setLoadingDiscovery(true);
    try {
      const res = await axios.get(`${API}/discovery`);
      setDiscoveryReport(res.data);
    } catch (err) {
      console.error("Discovery error:", err);
    } finally {
      setLoadingDiscovery(false);
    }
  };

  const fetchAliases = async () => {
    try {
      const res = await axios.get(`${API}/aliases`);
      setColumnAliases(res.data.aliases || {});
    } catch (err) {
      console.error("Aliases error:", err);
    }
  };

  const handleAddAlias = async () => {
    if (!newAlias.trim()) return;
    try {
      const res = await axios.post(`${API}/aliases`, { canonical: newCanonical, alias: newAlias.trim() });
      setColumnAliases(res.data.aliases || {});
      setNewAlias("");
    } catch (err) {
      console.error("Add alias error:", err);
    }
  };

  const handleClearWorkspace = async (keepSamples = false) => {
    if (!window.confirm("Are you sure you want to clear all uploaded files from the workspace?")) return;
    try {
      const res = await axios.post(`${API}/clear-workspace`, null, { params: { keep_samples: keepSamples } });
      const samplesRes = await axios.get(`${API}/samples`);
      setSamples(samplesRes.data.files || []);
      if (samplesRes.data.files?.length) {
        setSelectedFile(samplesRes.data.files[0].name);
        setSelectedSheet(samplesRes.data.files[0].sheets?.[0] || null);
      } else {
        setSelectedFile(null);
        setSelectedSheet(null);
        setDataset(null);
      }
      setDuplicates(null);
      setJobResult(null);
      setJobStatus("idle");
      setJobPercent(0);
      setJobStage("");
      setUploadSuccess("Workspace cleared successfully. Ready for new uploads.");
      fetchDiscoveryReport();
      axios.get(`${API}/summary`).then((r) => setSummary(r.data)).catch(() => {});
    } catch (err) {
      console.error("Clear workspace error:", err);
    }
  };

  const SPREADSHEET_EXTENSIONS = [".xlsx", ".csv", ".xls", ".xlsm", ".xlsb", ".tsv", ".zip"];

  const handleBatchUpload = async (rawFileEntries) => {
    if (!rawFileEntries || rawFileEntries.length === 0) return;

    // Filter valid spreadsheet files on client side to avoid uploading non-data junk files
    const fileEntries = rawFileEntries.filter((item) => {
      const file = item.file || item;
      const name = (file.name || "").toLowerCase();
      return SPREADSHEET_EXTENSIONS.some((ext) => name.endsWith(ext));
    });

    if (fileEntries.length === 0) {
      alert("No valid spreadsheet files (.xlsx, .csv, .xls, .xlsm, .zip) found in the selected upload.");
      setUploading(false);
      return;
    }

    setUploading(true);
    setUploadSuccess(null);

    // Chunk uploads into parallel batches of 30 files for fast transfer
    const CHUNK_SIZE = 30;
    let totalUploaded = 0;
    let lastResponse = null;

    try {
      for (let i = 0; i < fileEntries.length; i += CHUNK_SIZE) {
        const chunk = fileEntries.slice(i, i + CHUNK_SIZE);
        const formData = new FormData();

        chunk.forEach((item) => {
          const file = item.file || item;
          const relPath = item.relativePath || file.webkitRelativePath || file.name;
          formData.append("files", file);
          formData.append("paths", relPath);
        });

        const res = await axios.post(`${API}/upload-batch`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });

        if (res.data.status === "success") {
          totalUploaded += res.data.files_uploaded || chunk.length;
          lastResponse = res.data;
        }
      }

      const samplesRes = await axios.get(`${API}/samples`);
      setSamples(samplesRes.data.files || []);
      fetchDiscoveryReport();
      setUploadSuccess(`Ultra-Fast Upload Complete: Uploaded ${totalUploaded} spreadsheet file(s).`);

      if (lastResponse?.saved_files?.length) {
        const validSpreadsheet = lastResponse.saved_files.find((f) =>
          SPREADSHEET_EXTENSIONS.some((ext) => f.toLowerCase().endsWith(ext))
        ) || lastResponse.saved_files[0];

        setSelectedFile(validSpreadsheet);
        if (lastResponse.dataset) setDataset(lastResponse.dataset);
        if (lastResponse.active_sheet) setSelectedSheet(lastResponse.active_sheet);
      }

      setTab("master_mdm");
      axios.get(`${API}/summary`).then((r) => setSummary(r.data)).catch(() => {});
      startMDMAnalysis("rule_1");
    } catch (err) {
      console.error("Batch upload error", err);
      alert("Failed to upload folder / files. Please try selecting valid spreadsheet files.");
    } finally {
      setUploading(false);
    }
  };

  const handleFolderDrop = async (e) => {
    e.preventDefault();
    setIsDragging(false);
    setUploading(true);
    const items = e.dataTransfer.items;
    const fileEntries = [];

    const traverseFileTree = (item, path = "") => {
      return new Promise((resolve) => {
        if (item.isFile) {
          item.file((file) => {
            fileEntries.push({ file, relativePath: path + file.name });
            resolve();
          });
        } else if (item.isDirectory) {
          const dirReader = item.createReader();
          const readAll = () => {
            dirReader.readEntries(async (entries) => {
              if (!entries.length) {
                resolve();
              } else {
                for (let i = 0; i < entries.length; i++) {
                  await traverseFileTree(entries[i], path + item.name + "/");
                }
                readAll();
              }
            });
          };
          readAll();
        } else {
          resolve();
        }
      });
    };

    const promises = [];
    if (items) {
      for (let i = 0; i < items.length; i++) {
        const entry = items[i].webkitGetAsEntry ? items[i].webkitGetAsEntry() : null;
        if (entry) {
          promises.push(traverseFileTree(entry));
        } else if (items[i].kind === "file") {
          const file = items[i].getAsFile();
          if (file) fileEntries.push({ file, relativePath: file.name });
        }
      }
    } else {
      const files = Array.from(e.dataTransfer.files);
      files.forEach((f) => fileEntries.push({ file: f, relativePath: f.name }));
    }

    await Promise.all(promises);
    if (fileEntries.length > 0) {
      await handleBatchUpload(fileEntries);
    } else {
      setUploading(false);
    }
  };

  const startMDMAnalysis = async (ruleId = selectedRuleId) => {
    setJobError(null);
    setJobResult(null);
    setJobStatus("running");
    setJobPercent(0);
    setJobStage("Scanning & Consolidating Master Records...");
    try {
      const res = await axios.post(`${API}/mdm/analyze`, { rule_id: ruleId });
      if (res.data.status === "started" || res.data.status === "already_running") {
        setJobStatus("running");
      }
    } catch (err) {
      setJobStatus("error");
      setJobError("Failed to start MDM consolidation job.");
    }
  };

  const controlJob = async (action) => {
    try {
      const res = await axios.post(`${API}/job/control`, { action });
      setJobStatus(res.data.job_status);
    } catch (err) {
      console.error("Control job error:", err);
    }
  };

  const downloadMasterWorkbook = () => {
    window.open(`${API}/download-master-workbook`, "_blank");
  };

  const downloadDuplicateReport = () => {
    window.open(`${API}/download-duplicate-report`, "_blank");
  };

  const handleResolveConflict = async (conflictId, action) => {
    try {
      const res = await axios.post(`${API}/mdm/resolve-conflict`, { conflict_id: conflictId, action });
      if (res.data.status === "success" && jobResult) {
        const updatedConflicts = (jobResult.conflicts || []).map(c => {
          if (action === "apply_all" || c.conflict_id === conflictId) {
            return { ...c, status: action === "apply_all" ? "resolved_keep_first" : `resolved_${action}` };
          }
          return c;
        });
        setJobResult({ ...jobResult, conflicts: updatedConflicts });
      }
    } catch (err) {
      console.error("Resolve conflict error:", err);
    }
  };

  const fetchMergedData = async () => {
    setLoadingMerge(true);
    try {
      const res = await axios.get(`${API}/merge`);
      setMergedData(res.data);
      setTab("merge");
    } catch (err) {
      console.error("Merge error:", err);
    } finally {
      setLoadingMerge(false);
    }
  };

  const fetchCrossMatchedData = async () => {
    setLoadingCrossMatch(true);
    try {
      const res = await axios.get(`${API}/cross-match`);
      setCrossMatchedData(res.data);
      setTab("crossmatch");
    } catch (err) {
      console.error("Cross match error:", err);
    } finally {
      setLoadingCrossMatch(false);
    }
  };

  const runPivot = async () => {
    if (!selectedFile || pivotRows.length === 0) return;
    setLoadingPivot(true);
    try {
      const params = {
        file: selectedFile,
        sheet: selectedSheet,
        rows: pivotRows.join(","),
        columns: pivotCols.length > 0 ? pivotCols.join(",") : undefined,
        value: pivotVal || undefined,
        aggregate: pivotAgg,
      };
      const res = await axios.get(`${API}/pivot`, { params });
      setPivotResult(res.data);
    } catch (err) {
      console.error("Pivot error:", err);
    } finally {
      setLoadingPivot(false);
    }
  };

  const [mdmPage, setMdmPage] = useState(1);
  const [mdmPageSize, setMdmPageSize] = useState(50);

  useEffect(() => {
    setMdmPage(1);
  }, [mdmSearch, mdmFilterCity, mdmFilterState, mdmMinDuplicates]);

  // Filtered Master Records
  const filteredMasterRecords = useMemo(() => {
    if (!jobResult?.master_records) return [];
    let list = jobResult.master_records;

    if (mdmSearch.trim()) {
      const q = mdmSearch.toLowerCase().trim();
      list = list.filter(m =>
        (m.master_id && m.master_id.toLowerCase().includes(q)) ||
        (m.name && m.name.toLowerCase().includes(q)) ||
        (m.address && m.address.toLowerCase().includes(q)) ||
        (m.city && m.city.toLowerCase().includes(q)) ||
        (m.state && m.state.toLowerCase().includes(q)) ||
        (m.company && m.company.toLowerCase().includes(q)) ||
        (m.contact_number && m.contact_number.includes(q)) ||
        (m.email && m.email.toLowerCase().includes(q))
      );
    }

    if (mdmFilterCity.trim()) {
      const q = mdmFilterCity.toLowerCase().trim();
      list = list.filter(m => m.city && m.city.toLowerCase().includes(q));
    }

    if (mdmFilterState.trim()) {
      const q = mdmFilterState.toLowerCase().trim();
      list = list.filter(m => m.state && m.state.toLowerCase().includes(q));
    }

    const minDup = parseInt(mdmMinDuplicates) || 0;
    if (minDup > 0) {
      list = list.filter(m => (m.duplicate_count || 0) >= minDup);
    }

    return list;
  }, [jobResult, mdmSearch, mdmFilterCity, mdmFilterState, mdmMinDuplicates]);

  // Paginated Master Records for ultra-fast DOM rendering
  const paginatedMasterRecords = useMemo(() => {
    const start = (mdmPage - 1) * mdmPageSize;
    return filteredMasterRecords.slice(start, start + mdmPageSize);
  }, [filteredMasterRecords, mdmPage, mdmPageSize]);

  const totalMdmPages = Math.ceil(filteredMasterRecords.length / mdmPageSize) || 1;

  // Filtered Duplicate References
  const filteredDuplicateReferences = useMemo(() => {
    if (!jobResult?.duplicate_references) return [];
    if (!refSearch.trim()) return jobResult.duplicate_references;
    const q = refSearch.toLowerCase().trim();
    return jobResult.duplicate_references.filter(r =>
      (r.master_id && r.master_id.toLowerCase().includes(q)) ||
      (r.source_file && r.source_file.toLowerCase().includes(q)) ||
      (r.sheet_name && r.sheet_name.toLowerCase().includes(q)) ||
      (r.folder_path && r.folder_path.toLowerCase().includes(q))
    );
  }, [jobResult, refSearch]);

  const kpis = summary?.summary;

  return (
    <div className="min-h-screen bg-slate-100 font-sans text-slate-900">
      
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur-md shadow-xs">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3.5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-amber-400 shadow-md shadow-slate-900/20 font-bold text-xl">
              👑
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base font-extrabold tracking-tight text-slate-900">ExcelIntel MDM Studio</span>
                <span className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-bold text-indigo-700 border border-indigo-200">
                  Enterprise Master Data Platform
                </span>
              </div>
              <p className="text-xs text-slate-500">Automatic Master Consolidation, Audit Trail & Conflict Resolution</p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            {/* Download Master Workbook Button */}
            <button
              onClick={downloadMasterWorkbook}
              className="flex items-center gap-1.5 rounded-lg border border-emerald-300 bg-emerald-600 px-3.5 py-2 text-xs font-bold text-white shadow-sm hover:bg-emerald-700 transition"
            >
              <Download size={14} /> Download Master_Data.xlsx
            </button>

            {/* Clear Workspace Button */}
            <button
              onClick={() => handleClearWorkspace(false)}
              className="flex items-center gap-1.5 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-700 hover:bg-rose-100 transition shadow-xs"
            >
              <Trash2 size={14} /> Clear Workspace
            </button>

            {/* Upload Unzipped Folder Button */}
            <label className="flex cursor-pointer items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-2 text-xs font-bold text-white shadow-sm hover:bg-emerald-700 transition">
              <Folder size={14} />
              <span>{uploading ? "Uploading..." : "Upload Unzipped Folder"}</span>
              <input
                type="file"
                webkitdirectory=""
                directory=""
                multiple
                className="hidden"
                onChange={(e) => {
                  if (e.target.files?.length) {
                    handleBatchUpload(Array.from(e.target.files).map(f => ({ file: f, relativePath: f.webkitRelativePath || f.name })));
                    e.target.value = "";
                  }
                }}
              />
            </label>

            {/* Direct Upload Files/ZIPs Button */}
            <label className="flex cursor-pointer items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-2 text-xs font-bold text-white shadow-sm hover:bg-blue-700 transition">
              <Upload size={14} />
              <span>{uploading ? "Uploading..." : "Upload Files / ZIPs"}</span>
              <input
                type="file"
                accept=".xlsx,.csv,.xls,.xlsm,.xlsb,.tsv,.zip"
                multiple
                className="hidden"
                onChange={(e) => {
                  if (e.target.files?.length) {
                    handleBatchUpload(Array.from(e.target.files).map(f => ({ file: f, relativePath: f.name })));
                    e.target.value = "";
                  }
                }}
              />
            </label>

            <button
              onClick={() => setPaletteOpen(true)}
              className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-100/80 px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-200/70 transition"
            >
              <CommandIcon size={14} className="text-slate-500" />
              <span>Palette</span>
              <kbd className="rounded bg-white px-1 py-0.5 text-[9px] font-semibold text-slate-500 border border-slate-200">Ctrl P</kbd>
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="mx-auto max-w-7xl px-6 py-6 space-y-6">
        
        {/* Workspace Active Banner & Control Panel */}
        <div className="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <Sparkles size={18} className="text-blue-600" />
              <h2 className="text-sm font-bold text-slate-900">Workspace Selection & Analysis Engine</h2>
            </div>
            {uploadSuccess && (
              <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 border border-emerald-200">
                ✓ {uploadSuccess}
              </span>
            )}
          </div>

          <div className="grid gap-4 md:grid-cols-[1fr_auto]">
            <div className="flex flex-wrap items-center gap-3">
              {/* Full Folder Analysis Mode Badge */}
              <div className="flex items-center gap-2 rounded-xl bg-blue-50 px-3.5 py-2 border border-blue-200">
                <Folder size={16} className="text-blue-600 font-bold" />
                <div>
                  <div className="text-xs font-extrabold text-blue-900 flex items-center gap-1.5">
                    <span>Full Folder Analysis Mode</span>
                    <span className="rounded-full bg-blue-600 px-2 py-0.5 text-[10px] text-white font-bold">ALL SHEETS</span>
                  </div>
                  <div className="text-[10px] text-blue-700 font-medium">
                    Analyzing 100% of files ({discoveryReport?.total_files || samples.length}) & worksheets ({discoveryReport?.total_worksheets || summary?.kpis?.sheets || 0}) in workspace folder
                  </div>
                </div>
              </div>

              {/* Data Preview Target File Selector */}
              {samples.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-slate-500">Preview File:</span>
                  <select
                    value={selectedFile || ""}
                    onChange={(e) => {
                      const f = samples.find(s => s.name === e.target.value);
                      if (f) {
                        setSelectedFile(f.name);
                        setSelectedSheet(f.sheets?.[0] || null);
                      }
                    }}
                    className="rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-800 shadow-xs focus:border-blue-500 focus:bg-white focus:outline-none min-w-[200px]"
                  >
                    {samples.map((f) => (
                      <option key={f.name} value={f.name}>
                        {f.folder && f.folder !== "Root" ? `📁 ${f.folder} / ` : ""}{f.basename || f.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {jobStatus === "idle" || jobStatus === "completed" || jobStatus === "cancelled" || jobStatus === "error" ? (
                <button
                  onClick={() => startMDMAnalysis(selectedRuleId)}
                  className="flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-amber-400 shadow-md hover:bg-slate-800 transition"
                >
                  <Crown size={15} /> Consolidate Master Data
                </button>
              ) : jobStatus === "running" ? (
                <button
                  onClick={() => controlJob("pause")}
                  className="flex items-center gap-2 rounded-xl bg-amber-600 px-4 py-2 text-xs font-bold text-white shadow-md hover:bg-amber-500 transition"
                >
                  <Pause size={14} /> Pause Job
                </button>
              ) : (
                <button
                  onClick={() => controlJob("resume")}
                  className="flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white shadow-md hover:bg-emerald-500 transition"
                >
                  <Play size={14} /> Resume Job
                </button>
              )}

              <button
                onClick={downloadMasterWorkbook}
                className="flex items-center gap-1.5 rounded-xl border border-emerald-300 bg-emerald-50 px-3.5 py-2 text-xs font-bold text-emerald-800 hover:bg-emerald-100 transition shadow-xs"
              >
                <Download size={14} /> Download Master_Data.xlsx
              </button>
            </div>
          </div>

          {/* Job Progress Indicator Bar */}
          {(jobStatus === "running" || jobStatus === "paused") && (
            <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-4 space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-slate-800">
                <span className="flex items-center gap-2">
                  <RefreshCw size={14} className="animate-spin text-blue-600" />
                  {jobStage || "Processing..."} ({jobCurrentFile || "Analyzing datasets"})
                </span>
                <span className="text-blue-700">{jobPercent}%</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
                <div
                  className="h-full bg-blue-600 transition-all duration-300 rounded-full"
                  style={{ width: `${jobPercent}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Enterprise Executive KPI Bar */}
        <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-4 lg:grid-cols-8">
          <div className="rounded-2xl border border-slate-200 bg-white p-3.5 shadow-sm">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Files</div>
            <div className="mt-1 text-xl font-extrabold text-slate-900">{discoveryReport?.total_files || samples.length}</div>
            <div className="mt-0.5 text-[10px] text-slate-500">Spreadsheets</div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-3.5 shadow-sm">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Worksheets</div>
            <div className="mt-1 text-xl font-extrabold text-blue-600">{discoveryReport?.total_worksheets || 0}</div>
            <div className="mt-0.5 text-[10px] text-slate-500">Scanned</div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-3.5 shadow-sm">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Rows</div>
            <div className="mt-1 text-xl font-extrabold text-indigo-600">{fmtNum(jobResult?.mdm_summary?.total_records || discoveryReport?.total_records || kpis?.total_rows || 0)}</div>
            <div className="mt-0.5 text-[10px] text-slate-500">Indexed</div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-3.5 shadow-sm">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Master Records</div>
            <div className="mt-1 text-xl font-extrabold text-emerald-600">{fmtNum(jobResult?.mdm_summary?.master_records_count || 0)}</div>
            <div className="mt-0.5 text-[10px] text-emerald-600 font-bold">Unique Entities</div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-3.5 shadow-sm">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Duplicates</div>
            <div className="mt-1 text-xl font-extrabold text-amber-600">{fmtNum(jobResult?.mdm_summary?.duplicate_records_count || 0)}</div>
            <div className="mt-0.5 text-[10px] text-amber-600 font-medium">References</div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-3.5 shadow-sm">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Unique Only</div>
            <div className="mt-1 text-xl font-extrabold text-teal-600">{fmtNum(jobResult?.mdm_summary?.unique_records_count || 0)}</div>
            <div className="mt-0.5 text-[10px] text-slate-500">Single Occurrences</div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-3.5 shadow-sm">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Conflicts</div>
            <div className="mt-1 text-xl font-extrabold text-rose-600">{fmtNum(jobResult?.mdm_summary?.conflicting_records_count || 0)}</div>
            <div className="mt-0.5 text-[10px] text-rose-600 font-bold">Require Review</div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-3.5 shadow-sm">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">System Metrics</div>
            <div className="mt-1 text-xs font-bold text-slate-700">
              {jobResult?.mdm_summary?.processing_time_sec ? `${jobResult.mdm_summary.processing_time_sec}s` : "0s"}
            </div>
            <div className="mt-0.5 text-[9px] text-slate-500">
              RAM: {jobResult?.mdm_summary?.memory_usage_mb ? `${jobResult.mdm_summary.memory_usage_mb} MB` : "—"}
            </div>
          </div>
        </div>

        {/* Workspace Navigation Tabs */}
        <div className="rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
          <div className="flex flex-wrap items-center gap-1 border-b border-slate-100 pb-2">
            {[
              { id: "master_mdm", label: "Master Dataset (MDM View)", icon: Crown },
              { id: "duplicate_refs", label: "Duplicate References Audit Trail", icon: Layers },
              { id: "conflicts", label: "Conflicting Records Workflow", icon: AlertTriangle },
              { id: "matching_rules", label: "Matching Rules & Column Mapping", icon: Sliders },
              { id: "advanced_duplicates", label: "Cross-File Duplicate Finder", icon: Sparkles },
              { id: "data", label: "Data Preview", icon: FileSpreadsheet },
              { id: "pivot", label: "Pivot Table Builder", icon: Grid },
              { id: "validation", label: "Quality Audit", icon: ShieldCheck },
            ].map((t) => {
              const Icon = t.icon;
              const active = tab === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-bold transition ${
                    active
                      ? "bg-slate-900 text-amber-400 shadow-sm font-bold"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  <Icon size={14} />
                  <span>{t.label}</span>
                </button>
              );
            })}
          </div>

          {/* Tab Content Area */}
          <div className="p-4">

            {/* TAB 1: MASTER DATASET (MDM VIEW) */}
            {tab === "master_mdm" && (
              <div className="space-y-5">
                {/* Search & Filter Toolbar */}
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-3">
                    <div className="flex items-center gap-2">
                      <Crown size={18} className="text-amber-500" />
                      <h3 className="text-sm font-bold text-slate-900">Consolidated Master Dataset Explorer</h3>
                      <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-bold text-emerald-800">
                        {filteredMasterRecords.length} Master Record(s) Shown
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => startMDMAnalysis(selectedRuleId)}
                        className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-1.5 text-xs font-bold text-white shadow-sm hover:bg-blue-700 transition"
                      >
                        <RefreshCw size={13} /> Re-Run Master Consolidation
                      </button>
                      <button
                        onClick={downloadMasterWorkbook}
                        className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-1.5 text-xs font-bold text-white shadow-sm hover:bg-emerald-700 transition"
                      >
                        <Download size={13} /> Export Master_Data.xlsx
                      </button>
                    </div>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-5">
                    <div className="relative">
                      <Search size={14} className="absolute left-3 top-3 text-slate-400" />
                      <input
                        type="text"
                        placeholder="Search Name, ID, Address..."
                        value={mdmSearch}
                        onChange={(e) => setMdmSearch(e.target.value)}
                        className="w-full rounded-xl border border-slate-300 bg-white pl-9 pr-3 py-2 text-xs font-medium focus:border-blue-500 focus:outline-none"
                      />
                    </div>

                    <div>
                      <input
                        type="text"
                        placeholder="Filter City..."
                        value={mdmFilterCity}
                        onChange={(e) => setMdmFilterCity(e.target.value)}
                        className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium focus:border-blue-500 focus:outline-none"
                      />
                    </div>

                    <div>
                      <input
                        type="text"
                        placeholder="Filter State..."
                        value={mdmFilterState}
                        onChange={(e) => setMdmFilterState(e.target.value)}
                        className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium focus:border-blue-500 focus:outline-none"
                      />
                    </div>

                    <div>
                      <select
                        value={mdmMinDuplicates}
                        onChange={(e) => setMdmMinDuplicates(e.target.value)}
                        className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium focus:border-blue-500 focus:outline-none"
                      >
                        <option value="0">All Duplicates Count</option>
                        <option value="1">At least 1 Duplicate</option>
                        <option value="2">At least 2 Duplicates</option>
                        <option value="5">At least 5 Duplicates</option>
                      </select>
                    </div>

                    <div>
                      <select
                        value={selectedRuleId}
                        onChange={(e) => {
                          setSelectedRuleId(e.target.value);
                          startMDMAnalysis(e.target.value);
                        }}
                        className="w-full rounded-xl border border-blue-300 bg-blue-50 px-3 py-2 text-xs font-bold text-blue-900 focus:border-blue-500 focus:outline-none"
                      >
                        {matchingRules.map(r => (
                          <option key={r.rule_id} value={r.rule_id}>⚙️ {r.rule_name}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>

                {/* Master Records Table */}
                {filteredMasterRecords.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-12 text-center">
                    <Crown size={36} className="mx-auto text-slate-400 mb-3" />
                    <h4 className="text-base font-bold text-slate-800">No Master Records Available</h4>
                    <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                      Upload your Excel files or click <strong>"Consolidate Master Data"</strong> to automatically scan and build the Master Dataset.
                    </p>
                    <button
                      onClick={() => startMDMAnalysis(selectedRuleId)}
                      className="mt-4 inline-flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-2.5 text-xs font-bold text-amber-400 shadow-md hover:bg-slate-800 transition"
                    >
                      <Play size={14} /> Run Master Consolidation Now
                    </button>
                  </div>
                ) : (
                  <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead className="bg-slate-900 text-slate-200 font-bold uppercase tracking-wider text-[10px]">
                          <tr>
                            <th className="p-3">Master ID</th>
                            <th className="p-3">Name / Entity</th>
                            <th className="p-3">Address</th>
                            <th className="p-3">City</th>
                            <th className="p-3">State</th>
                            <th className="p-3">Contact Number</th>
                            <th className="p-3">Email</th>
                            <th className="p-3 text-center">Sources</th>
                            <th className="p-3 text-center">Duplicates</th>
                            <th className="p-3 text-center">Audit References</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {paginatedMasterRecords.map((m, idx) => {
                            const isExpanded = expandedMasterId === m.master_id;
                            return (
                              <React.Fragment key={m.master_id || idx}>
                                <tr className={`hover:bg-slate-50 transition ${isExpanded ? "bg-blue-50/40 font-medium" : ""}`}>
                                  <td className="p-3 font-mono font-bold text-slate-900">
                                    <span className="rounded bg-slate-900 px-2 py-0.5 text-[10px] text-amber-400 font-bold">
                                      {m.master_id}
                                    </span>
                                  </td>
                                  <td className="p-3 font-bold text-slate-900">{m.name || "—"}</td>
                                  <td className="p-3 text-slate-700 max-w-[200px] truncate">{m.address || "—"}</td>
                                  <td className="p-3 text-slate-700">{m.city || "—"}</td>
                                  <td className="p-3 text-slate-700">{m.state || "—"}</td>
                                  <td className="p-3 font-mono font-medium text-slate-800">{m.contact_number || "—"}</td>
                                  <td className="p-3 text-blue-600 font-medium">{m.email || "—"}</td>
                                  <td className="p-3 text-center font-bold">
                                    <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] text-blue-800">
                                      📁 {m.source_count} file(s)
                                    </span>
                                  </td>
                                  <td className="p-3 text-center font-bold">
                                    <span className={`rounded-full px-2 py-0.5 text-[10px] ${m.duplicate_count > 0 ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-600"}`}>
                                      🔁 {m.duplicate_count}
                                    </span>
                                  </td>
                                  <td className="p-3 text-center">
                                    <button
                                      onClick={() => setExpandedMasterId(isExpanded ? null : m.master_id)}
                                      className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-[10px] font-bold text-slate-700 hover:bg-slate-100 transition shadow-xs"
                                    >
                                      {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                                      <span>Audit Trail ({m.references_count || m.references?.length || 0})</span>
                                    </button>
                                  </td>
                                </tr>

                                {/* Collapsible Audit Trail Drawer */}
                                {isExpanded && (
                                  <tr>
                                    <td colSpan={10} className="bg-slate-50/90 p-4 border-t border-b border-blue-200">
                                      <div className="rounded-xl border border-blue-200 bg-white p-4 space-y-3 shadow-sm">
                                        <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                                          <div className="flex items-center gap-2">
                                            <Layers size={14} className="text-blue-600" />
                                            <span className="text-xs font-bold text-slate-900">
                                              Duplicate References Audit Trail for Master Record {m.master_id} ({m.name})
                                            </span>
                                          </div>
                                          <span className="text-[10px] text-slate-500">Total Occurrences: {m.total_occurrences}</span>
                                        </div>

                                        <div className="overflow-x-auto">
                                          <table className="w-full text-left text-[11px] border-collapse">
                                            <thead className="bg-slate-100 text-slate-700 font-bold uppercase text-[9px]">
                                              <tr>
                                                <th className="p-2">Master ID</th>
                                                <th className="p-2">Source File</th>
                                                <th className="p-2">Worksheet</th>
                                                <th className="p-2">Row Number</th>
                                                <th className="p-2">Folder Path</th>
                                                <th className="p-2">Import Timestamp</th>
                                              </tr>
                                            </thead>
                                            <tbody className="divide-y divide-slate-100">
                                              {(m.references || []).map((ref, rIdx) => (
                                                <tr key={rIdx} className="hover:bg-blue-50/30 transition">
                                                  <td className="p-2 font-mono font-bold text-slate-900">{ref.master_id}</td>
                                                  <td className="p-2 font-bold text-blue-700">📄 {ref.source_file}</td>
                                                  <td className="p-2 text-slate-700">{ref.sheet_name}</td>
                                                  <td className="p-2 font-mono font-semibold text-slate-800">Row #{ref.row_number}</td>
                                                  <td className="p-2 text-slate-500 font-mono text-[10px]">{ref.folder_path}</td>
                                                  <td className="p-2 text-slate-400 text-[10px]">{ref.import_date}</td>
                                                </tr>
                                              ))}
                                            </tbody>
                                          </table>
                                        </div>
                                      </div>
                                    </td>
                                  </tr>
                                )}
                              </React.Fragment>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>

                    {/* Ultra-Fast UI Pagination Bar */}
                    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 bg-slate-50 px-4 py-3 text-xs font-semibold text-slate-700">
                      <div className="flex items-center gap-2">
                        <span>Showing</span>
                        <strong className="text-slate-900 font-extrabold">
                          {filteredMasterRecords.length === 0 ? 0 : (mdmPage - 1) * mdmPageSize + 1}
                        </strong>
                        <span>to</span>
                        <strong className="text-slate-900 font-extrabold">
                          {Math.min(mdmPage * mdmPageSize, filteredMasterRecords.length)}
                        </strong>
                        <span>of</span>
                        <strong className="text-slate-900 font-extrabold">{filteredMasterRecords.length}</strong>
                        <span>Master Records</span>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-1.5 text-xs">
                          <span className="text-slate-500">Rows per page:</span>
                          <select
                            value={mdmPageSize}
                            onChange={(e) => { setMdmPageSize(parseInt(e.target.value)); setMdmPage(1); }}
                            className="rounded-lg border border-slate-300 bg-white px-2 py-1 text-xs font-bold text-slate-800 focus:outline-none"
                          >
                            <option value={25}>25</option>
                            <option value={50}>50</option>
                            <option value={100}>100</option>
                            <option value={250}>250</option>
                          </select>
                        </div>

                        <div className="flex items-center gap-1">
                          <button
                            disabled={mdmPage <= 1}
                            onClick={() => setMdmPage(p => Math.max(1, p - 1))}
                            className="rounded-lg border border-slate-300 bg-white px-3 py-1 text-xs font-bold text-slate-700 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition"
                          >
                            Previous
                          </button>

                          <span className="px-2 text-xs font-bold text-slate-900">
                            Page {mdmPage} of {totalMdmPages}
                          </span>

                          <button
                            disabled={mdmPage >= totalMdmPages}
                            onClick={() => setMdmPage(p => Math.min(totalMdmPages, p + 1))}
                            className="rounded-lg border border-slate-300 bg-white px-3 py-1 text-xs font-bold text-slate-700 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition"
                          >
                            Next
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 2: DUPLICATE REFERENCES AUDIT TRAIL */}
            {tab === "duplicate_refs" && (
              <div className="space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">Duplicate References Audit Log</h3>
                    <p className="text-xs text-slate-500">Every duplicate occurrence mapped to its Master ID and lineage</p>
                  </div>
                  <div className="relative min-w-[260px]">
                    <Search size={14} className="absolute left-3 top-3 text-slate-400" />
                    <input
                      type="text"
                      placeholder="Filter Master ID or Source File..."
                      value={refSearch}
                      onChange={(e) => setRefSearch(e.target.value)}
                      className="w-full rounded-xl border border-slate-300 bg-white pl-9 pr-3 py-2 text-xs font-medium focus:outline-none"
                    />
                  </div>
                </div>

                <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-slate-900 text-slate-200 font-bold uppercase text-[10px]">
                      <tr>
                        <th className="p-3">Master ID</th>
                        <th className="p-3">Source File</th>
                        <th className="p-3">Worksheet</th>
                        <th className="p-3">Row Number</th>
                        <th className="p-3">Folder Path</th>
                        <th className="p-3">Import Date</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {filteredDuplicateReferences.slice(0, 500).map((ref, idx) => (
                        <tr key={idx} className="hover:bg-slate-50 transition">
                          <td className="p-3 font-mono font-bold text-slate-900">
                            <span className="rounded bg-slate-900 px-2 py-0.5 text-[10px] text-amber-400 font-bold">
                              {ref.master_id}
                            </span>
                          </td>
                          <td className="p-3 font-bold text-blue-700">📄 {ref.source_file}</td>
                          <td className="p-3 text-slate-700">{ref.sheet_name}</td>
                          <td className="p-3 font-mono text-slate-800">Row #{ref.row_number}</td>
                          <td className="p-3 font-mono text-[10px] text-slate-500">{ref.folder_path}</td>
                          <td className="p-3 text-slate-400 text-[10px]">{ref.import_date}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 3: CONFLICTING RECORDS WORKFLOW */}
            {tab === "conflicts" && (
              <div className="space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <AlertTriangle size={16} className="text-amber-600" />
                      <h3 className="text-sm font-bold text-amber-900">Interactive Conflicting Records Resolution Workflow</h3>
                    </div>
                    <p className="text-xs text-amber-700 mt-0.5">
                      Entities matching on primary attributes but containing differing detail fields across Excel files.
                    </p>
                  </div>

                  <button
                    onClick={() => handleResolveConflict("all", "apply_all")}
                    className="flex items-center gap-1.5 rounded-xl bg-amber-600 px-4 py-2 text-xs font-bold text-white shadow-sm hover:bg-amber-700 transition"
                  >
                    <Check size={14} /> Apply "Keep First" to All Conflicts
                  </button>
                </div>

                {(!jobResult?.conflicts || jobResult.conflicts.length === 0) ? (
                  <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-12 text-center">
                    <CheckCircle2 size={36} className="mx-auto text-emerald-500 mb-2" />
                    <h4 className="text-base font-bold text-slate-800">No Conflicting Records Detected</h4>
                    <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                      All consolidated Master Records have consistent field values across uploaded spreadsheets.
                    </p>
                  </div>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2">
                    {jobResult.conflicts.map((c, idx) => (
                      <div key={c.conflict_id || idx} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm space-y-3">
                        <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                          <div>
                            <span className="rounded bg-rose-100 px-2 py-0.5 text-[10px] font-bold text-rose-800">
                              {c.conflict_id}
                            </span>
                            <span className="ml-2 font-mono text-xs font-bold text-slate-900">{c.master_id}</span>
                          </div>
                          <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase ${c.status.startsWith("resolved") ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>
                            {c.status}
                          </span>
                        </div>

                        <div>
                          <div className="text-xs font-bold text-slate-900">{c.entity_name}</div>
                          <div className="text-xs text-slate-500">Field in Conflict: <strong className="text-rose-600">{c.field_name}</strong></div>
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
                            <div className="text-[10px] font-bold text-slate-400">OPTION A</div>
                            <div className="font-bold text-slate-900 mt-1">{c.value_a}</div>
                            <div className="text-[10px] text-slate-500 mt-1">📄 {c.source_a} ({c.sheet_a}:L{c.row_a})</div>
                          </div>

                          <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
                            <div className="text-[10px] font-bold text-slate-400">OPTION B</div>
                            <div className="font-bold text-slate-900 mt-1">{c.value_b}</div>
                            <div className="text-[10px] text-slate-500 mt-1">📄 {c.source_b} ({c.sheet_b}:L{c.row_b})</div>
                          </div>
                        </div>

                        <div className="flex flex-wrap items-center gap-2 pt-1">
                          <button
                            onClick={() => handleResolveConflict(c.conflict_id, "keep_first")}
                            className="rounded-lg bg-slate-900 px-3 py-1.5 text-[10px] font-bold text-white hover:bg-slate-800 transition"
                          >
                            Keep Option A
                          </button>
                          <button
                            onClick={() => handleResolveConflict(c.conflict_id, "keep_second")}
                            className="rounded-lg bg-blue-600 px-3 py-1.5 text-[10px] font-bold text-white hover:bg-blue-700 transition"
                          >
                            Keep Option B
                          </button>
                          <button
                            onClick={() => handleResolveConflict(c.conflict_id, "ignore")}
                            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-[10px] font-bold text-slate-700 hover:bg-slate-100 transition"
                          >
                            Ignore
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* TAB 4: MATCHING RULES & COLUMN MAPPING */}
            {tab === "matching_rules" && (
              <div className="space-y-6">
                <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
                  <h3 className="text-sm font-bold text-blue-900">Configurable Comparison & Matching Rules Engine</h3>
                  <p className="text-xs text-blue-700 mt-1">
                    Choose what defines a duplicate entity across files. Changing active rule automatically re-consolidates the Master Dataset.
                  </p>
                </div>

                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {matchingRules.map(r => {
                    const isSelected = selectedRuleId === r.rule_id;
                    return (
                      <div
                        key={r.rule_id}
                        onClick={() => {
                          setSelectedRuleId(r.rule_id);
                          startMDMAnalysis(r.rule_id);
                        }}
                        className={`cursor-pointer rounded-2xl border p-5 transition ${
                          isSelected
                            ? "border-blue-600 bg-white shadow-md ring-2 ring-blue-500/20"
                            : "border-slate-200 bg-white hover:border-blue-300 hover:shadow-sm"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase ${isSelected ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-600"}`}>
                            {isSelected ? "Active Rule" : r.rule_id}
                          </span>
                        </div>
                        <h4 className="text-sm font-extrabold text-slate-900 mt-2">{r.rule_name}</h4>
                        <p className="text-xs text-slate-500 mt-1">{r.description}</p>
                        <div className="mt-3 flex flex-wrap gap-1">
                          {r.fields.map(f => (
                            <span key={f} className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-700">
                              {f}
                            </span>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Column Aliases Editor */}
                <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-4">
                  <h4 className="text-sm font-bold text-slate-900">Editable Column Mapping Alias Dictionary</h4>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div>
                      <label className="text-[11px] font-bold text-slate-500">Canonical Target Column</label>
                      <select
                        value={newCanonical}
                        onChange={(e) => setNewCanonical(e.target.value)}
                        className="w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-xs font-semibold focus:outline-none"
                      >
                        {Object.keys(columnAliases).map(c => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="text-[11px] font-bold text-slate-500">New Column Variant Name</label>
                      <input
                        type="text"
                        placeholder="e.g. Phone_No, Customer_Full_Name..."
                        value={newAlias}
                        onChange={(e) => setNewAlias(e.target.value)}
                        className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs font-medium focus:outline-none"
                      />
                    </div>

                    <div className="flex items-end">
                      <button
                        onClick={handleAddAlias}
                        className="w-full rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-700 transition"
                      >
                        Add Alias Mapping
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 5: ADVANCED CROSS-FILE DUPLICATE FINDER */}
            {tab === "advanced_duplicates" && (
              <div className="space-y-6">
                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                    <h3 className="text-sm font-bold text-slate-900">Cross-File Record Similarity & Fuzzy Matches</h3>
                  </div>
                  {(!jobResult?.exact_duplicates && !jobResult?.similar_records) ? (
                    <div className="p-8 text-center text-xs text-slate-500">
                      Run MDM Consolidation to populate fuzzy & exact duplicate records view.
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {(jobResult?.exact_duplicates || []).slice(0, 20).map((g, idx) => (
                        <div key={idx} className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs space-y-1">
                          <div className="font-bold text-slate-900">Group #{g.group_id} — {g.match_level} ({g.confidence_score}%)</div>
                          <div className="text-slate-500">{g.reason}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 6: DATA PREVIEW */}
            {tab === "data" && (
              <div className="space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">Dataset Sheet Preview: <span className="font-mono text-blue-700">{selectedFile || "No file selected"}</span></h3>
                    <p className="text-[11px] text-slate-500">Inspecting raw tabular data. Note: Master Consolidation Engine analyzes 100% of files & sheets in workspace automatically.</p>
                  </div>
                  <div className="flex items-center gap-3">
                    {samples.find(s => s.name === selectedFile)?.sheets?.length > 1 && (
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-medium text-slate-500">Preview Sheet:</span>
                        <select
                          value={selectedSheet || ""}
                          onChange={(e) => setSelectedSheet(e.target.value)}
                          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-800"
                        >
                          {samples.find(s => s.name === selectedFile)?.sheets.map(sh => (
                            <option key={sh} value={sh}>{sh}</option>
                          ))}
                        </select>
                      </div>
                    )}
                    <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">{dataset?.rows || 0} rows | {dataset?.cols || 0} columns</span>
                  </div>
                </div>
                {dataset?.preview?.length ? (
                  <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-900 text-slate-200 text-[10px] font-bold uppercase">
                        <tr>
                          {dataset.columns.map(c => (
                            <th key={c} className="p-3">{c}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {dataset.preview.map((r, i) => (
                          <tr key={i} className="hover:bg-slate-50">
                            {dataset.columns.map(c => (
                              <td key={c} className="p-3">{r[c] != null ? String(r[c]) : "—"}</td>
>>>>>>> a4386bf (Initial commit)
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
<<<<<<< HEAD
                  ) : (
                    <div className="p-8 text-center text-sm text-white/40">Loading…</div>
                  )}
                </div>
              </Section>
            )}

            {tab === "duplicates" && (
              <Section
                title="Duplicate Detection"
                subtitle="Smart multi-strategy: hash, fuzzy, semantic column detection"
                icon={Copy}
                right={
                  <div className="flex items-center gap-3">
                    <label className="flex items-center gap-2 text-xs text-white/60">
                      Threshold
                      <input
                        data-testid="threshold-slider"
                        type="range" min="50" max="99" value={threshold}
                        onChange={(e) => setThreshold(Number(e.target.value))}
                        className="accent-[#7c5cff]"
                      />
                      <span className="w-8 text-white">{threshold}%</span>
                    </label>
                    <button
                      data-testid="run-dup-btn"
                      onClick={runDuplicates}
                      disabled={loadingDup}
                      className="rounded-lg bg-[#5b4be0] px-3 py-1.5 text-xs font-medium hover:brightness-110 disabled:opacity-60"
                    >
                      {loadingDup ? "…" : "Detect"}
                    </button>
                  </div>
                }
              >
                {duplicates ? (
                  <div>
                    <div className="mb-3 flex flex-wrap gap-3 text-xs text-white/60">
                      <span className="rounded-full bg-white/[0.05] px-3 py-1">
                        <b className="text-white">{duplicates.total_groups}</b> groups
                      </span>
                      <span className="rounded-full bg-white/[0.05] px-3 py-1">
                        <b className="text-white">{duplicates.total_rows_flagged}</b> rows flagged
                      </span>
                      <span className="rounded-full bg-white/[0.05] px-3 py-1">
                        algo <b className="text-white">{duplicates.algorithm}</b>
                      </span>
                    </div>
                    <div data-testid="duplicates-list" className="grid gap-2 max-h-[520px] overflow-auto pr-1">
                      {duplicates.groups.map((g) => (
                        <div key={g.id} className="rounded-xl border border-white/10 bg-white/[0.02] p-3">
                          <div className="mb-2 flex items-center justify-between text-xs">
                            <div className="flex items-center gap-2">
                              <span className="rounded-full bg-[#7c5cff]/20 px-2 py-0.5 text-[#c9b6ff]">
                                Group {g.id + 1}
                              </span>
                              <span className="text-white/60">{g.method}</span>
                              <span className="text-white/40">— {g.reason}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="rounded-full bg-white/5 px-2 py-0.5">
                                size <b className="text-white">{g.size}</b>
                              </span>
                              <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-emerald-300">
                                {g.confidence.toFixed(1)}%
                              </span>
                            </div>
                          </div>
                          <div className="overflow-auto rounded-lg border border-white/5">
                            <table className="min-w-full text-[11px]">
                              <thead className="bg-white/[0.03] text-white/60">
                                <tr>
                                  {Object.keys(g.rows[0] || {}).slice(0, 8).map((c) => (
                                    <th key={c} className="px-2 py-1 text-left font-medium">{c}</th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {g.rows.slice(0, 4).map((r, i) => (
                                  <tr key={i} className={i % 2 ? "bg-white/[0.02]" : ""}>
                                    {Object.keys(g.rows[0] || {}).slice(0, 8).map((c) => (
                                      <td key={c} className="px-2 py-1 text-white/70">
                                        {r[c] == null ? "—" : String(r[c]).slice(0, 40)}
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="p-6 text-center text-sm text-white/40">
                    Adjust the threshold and click Detect.
                  </div>
                )}
              </Section>
            )}

            {tab === "relationships" && (
              <Section
                title="Relationship Discovery"
                subtitle="Auto-inferred foreign keys across all loaded datasets"
                icon={Network}
              >
                <div data-testid="relationships-list" className="overflow-auto rounded-xl border border-white/10 bg-[#0f0f18]">
                  <table className="min-w-full text-xs">
                    <thead className="bg-[#1a1a2e] text-[#c9b6ff]">
                      <tr>
                        <th className="border-b border-white/10 px-3 py-2 text-left font-semibold">Left</th>
                        <th className="border-b border-white/10 px-3 py-2 text-left font-semibold">Right</th>
                        <th className="border-b border-white/10 px-3 py-2 text-left font-semibold">Cardinality</th>
                        <th className="border-b border-white/10 px-3 py-2 text-left font-semibold">Confidence</th>
                        <th className="border-b border-white/10 px-3 py-2 text-left font-semibold">Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(relationships?.relationships || []).map((r, i) => (
                        <tr key={i} className={i % 2 ? "bg-white/[0.02]" : ""}>
                          <td className="border-b border-white/5 px-3 py-2">
                            <code className="text-[#c9b6ff]">{r.left_dataset}.{r.left_column}</code>
                          </td>
                          <td className="border-b border-white/5 px-3 py-2">
                            <code className="text-[#c9b6ff]">{r.right_dataset}.{r.right_column}</code>
                          </td>
                          <td className="border-b border-white/5 px-3 py-2">
                            <span className="rounded-full bg-[#7c5cff]/20 px-2 py-0.5 text-[#c9b6ff]">{r.cardinality}</span>
                          </td>
                          <td className="border-b border-white/5 px-3 py-2 text-emerald-300">
                            {r.confidence.toFixed(1)}%
                          </td>
                          <td className="border-b border-white/5 px-3 py-2 text-white/60">{r.reason}</td>
                        </tr>
                      ))}
                      {(relationships?.relationships || []).length === 0 && (
                        <tr>
                          <td colSpan={5} className="p-6 text-center text-white/40">No relationships detected yet.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </Section>
            )}
          </div>
        </div>

        {/* Feature strip */}
        <Section title="Everything ExcelIntel does" subtitle="Feature preview" icon={Sparkles}>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {[
              { icon: Copy, title: "Smart Duplicate Detection", body: "6 fuzzy algorithms, phonetic, hash, semantic column detection." },
              { icon: Network, title: "Relationship Discovery", body: "Automatically infer FKs across every pair of datasets." },
              { icon: Table, title: "Drag-drop Pivot Builder", body: "Cross-tabs with 9 aggregations & drill-through to the underlying rows." },
              { icon: ShieldCheck, title: "Validation Engine", body: "Emails, phones, GSTINs, ZIPs, dates, outliers, missing headers." },
              { icon: RefreshCw, title: "Live Refresh", body: "Watches source files on disk — dashboard updates the moment a file changes." },
              { icon: Bookmark, title: "Saved Views", body: "Bookmark filters, pivots, SQL and jump back with one click." },
              { icon: CommandIcon, title: "Command Palette", body: "Ctrl+P fuzzy-searches every dataset, view, saved bookmark & action." },
              { icon: Terminal, title: "DuckDB SQL Console", body: "Ad-hoc analytics across every loaded sheet." },
              { icon: FileSpreadsheet, title: "Formatted Exports", body: "Excel with colors + filters + freeze panes, PDF, HTML, JSON." },
            ].map((f) => (
              <div key={f.title} className="rounded-xl border border-white/10 bg-white/[0.02] p-4 transition hover:border-white/20 hover:bg-white/[0.04]">
                <div className="mb-2 inline-flex rounded-lg bg-gradient-to-br from-[#5b4be0]/30 to-[#b06bff]/20 p-2 text-[#c9b6ff]">
                  <f.icon size={16} />
                </div>
                <div className="text-sm font-semibold">{f.title}</div>
                <div className="mt-1 text-xs text-white/50">{f.body}</div>
              </div>
            ))}
          </div>
        </Section>

        {/* Desktop screenshots */}
        <Section title="Desktop app" subtitle="PySide6 preview — click any thumbnail to expand" icon={Sparkles}>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {[
              { name: "screenshot_dashboard_cross_filter.png", caption: "Cross-filter dashboard" },
              { name: "screenshot_pivot.png", caption: "Pivot Builder" },
              { name: "screenshot_drill_through.png", caption: "Drill-through" },
              { name: "screenshot_command_palette.png", caption: "Command Palette" },
              { name: "screenshot_relationships.png", caption: "Relationship graph" },
              { name: "screenshot_duplicates.png", caption: "Duplicate detection" },
            ].map((s) => (
              <a
                key={s.name}
                href={`${API}/screenshots/${s.name}`} target="_blank" rel="noreferrer"
                className="group overflow-hidden rounded-xl border border-white/10 bg-[#0f0f18] transition hover:border-white/20"
                data-testid={`screenshot-${s.name}`}
              >
                <img
                  src={`${API}/screenshots/${s.name}`} alt={s.caption}
                  className="h-40 w-full object-cover transition group-hover:scale-105"
                />
                <div className="p-3 text-xs text-white/70">{s.caption}</div>
              </a>
            ))}
          </div>
        </Section>

        <footer className="my-10 text-center text-[11px] text-white/40">
          ExcelIntel · offline · Polars · DuckDB · RapidFuzz · PySide6 · 100% Python
        </footer>
      </main>

      {/* Command palette */}
      {paletteOpen && (
        <CommandPalette
          onClose={() => setPaletteOpen(false)}
          samples={samples}
          onFileSelect={(f) => {
            setSelectedFile(f.name); setSelectedSheet(f.sheets?.[0] || null); setTab("data");
          }}
          onTabSelect={(id) => setTab(id)}
          onRunDuplicates={() => { runDuplicates(); }}
        />
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────── palette
function CommandPalette({ onClose, samples, onFileSelect, onTabSelect, onRunDuplicates }) {
  const [q, setQ] = useState("");
  const commands = useMemo(() => {
    const items = [
      { label: "Go to Data", category: "Navigate", run: () => onTabSelect("data") },
      { label: "Go to Duplicates", category: "Navigate", run: () => onTabSelect("duplicates") },
      { label: "Go to Relationships", category: "Navigate", run: () => onTabSelect("relationships") },
      { label: "Scan duplicates now", category: "Action", run: () => onRunDuplicates() },
    ];
    for (const f of samples) {
      items.push({
        label: `Activate: ${f.name}`,
        category: "Dataset",
        run: () => onFileSelect(f),
      });
    }
    return items;
  }, [samples, onFileSelect, onTabSelect, onRunDuplicates]);

  const filtered = q
    ? commands
        .map((c) => ({ ...c, s: score(q.toLowerCase(), (c.label + " " + c.category).toLowerCase()) }))
        .filter((c) => c.s > 0)
        .sort((a, b) => b.s - a.s)
    : commands;

  return (
    <div
      data-testid="command-palette"
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 backdrop-blur"
      onClick={onClose}
    >
      <div
        className="mt-[10vh] w-[min(640px,92vw)] rounded-2xl border border-white/10 bg-[#0f0f18] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="border-b border-white/10 p-3">
          <input
            data-testid="palette-input"
            autoFocus value={q} onChange={(e) => setQ(e.target.value)}
            placeholder="Type to search datasets, tabs, actions…"
            className="w-full rounded-xl bg-white/[0.03] px-4 py-2 text-sm outline-none placeholder:text-white/40"
          />
        </div>
        <div className="max-h-[50vh] overflow-auto p-2">
          {filtered.slice(0, 40).map((c, i) => (
            <button
              key={i}
              data-testid={`palette-item-${i}`}
              onClick={() => { c.run(); onClose(); }}
              className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm hover:bg-white/[0.06]"
            >
              <div className="flex items-center gap-3">
                <span className="w-16 text-[11px] uppercase tracking-widest text-white/40">{c.category}</span>
                <span className="text-white/90">{c.label}</span>
              </div>
              <ArrowRight size={14} className="text-white/30" />
            </button>
          ))}
          {filtered.length === 0 && (
            <div className="p-6 text-center text-xs text-white/40">No matches</div>
          )}
        </div>
        <div className="border-t border-white/10 p-2 text-[11px] text-white/40">
          ↑↓ navigate · Enter to run · Esc to close
        </div>
      </div>
    </div>
  );
}

// naive fuzzy score
function score(q, s) {
  if (!q) return 1;
  if (s.includes(q)) return 200 - (s.length - q.length);
  let i = 0, sc = 0;
  for (const ch of q) {
    const idx = s.indexOf(ch, i);
    if (idx === -1) return 0;
    sc += 5 - Math.min(4, idx - i);
    i = idx + 1;
  }
  return sc;
}

// ─────────────────────────────────────────────────────────────────────────── SVG charts
function BarsSVG({ data = [], onBarClick }) {
  const W = 640, H = 260, PAD_L = 42, PAD_B = 44, PAD_T = 20, PAD_R = 20;
  if (!data.length) {
    return (
      <div data-testid="chart-rows-by-sheet" className="grid h-[260px] place-items-center text-xs text-white/40">
        No data
      </div>
    );
  }
  const max = Math.max(...data.map((d) => d.rows), 1);
  const innerW = W - PAD_L - PAD_R;
  const innerH = H - PAD_T - PAD_B;
  const barW = (innerW / data.length) * 0.65;
  const gap = (innerW / data.length) * 0.35;

  const ticks = 4;
  const tickVals = Array.from({ length: ticks + 1 }, (_, i) => Math.round((max * i) / ticks));

  return (
    <div data-testid="chart-rows-by-sheet" className="w-full">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-[260px]" preserveAspectRatio="none">
        {/* grid */}
        {tickVals.map((v, i) => {
          const y = PAD_T + innerH - (v / max) * innerH;
          return (
            <g key={i}>
              <line x1={PAD_L} x2={W - PAD_R} y1={y} y2={y} stroke="#ffffff10" />
              <text x={PAD_L - 8} y={y + 3} textAnchor="end" fill="#8b8ba8" fontSize="10">
                {v.toLocaleString()}
              </text>
            </g>
          );
        })}
        {/* bars */}
        {data.map((d, i) => {
          const h = (d.rows / max) * innerH;
          const x = PAD_L + i * (barW + gap) + gap / 2;
          const y = PAD_T + innerH - h;
          const color = PALETTE[i % PALETTE.length];
          return (
            <g
              key={d.name} className="cursor-pointer"
              onClick={() => onBarClick && onBarClick(d)}
              data-testid={`bar-${d.name}`}
            >
              <rect x={x} y={y} width={barW} height={h} rx="6" fill={color}>
                <title>{d.name}: {d.rows.toLocaleString()} rows</title>
              </rect>
              <text
                x={x + barW / 2} y={PAD_T + innerH + 16}
                textAnchor="middle" fill="#c9c9dd" fontSize="10"
              >
                {d.name.length > 16 ? d.name.slice(0, 15) + "…" : d.name}
              </text>
              <text
                x={x + barW / 2} y={y - 6}
                textAnchor="middle" fill={color} fontSize="10" fontWeight="600"
              >
                {d.rows.toLocaleString()}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function PieSVG({ data = [] }) {
  const total = data.reduce((a, b) => a + b.value, 0);
  if (!total) {
    return (
      <div data-testid="chart-quality" className="grid h-[260px] place-items-center text-xs text-white/40">
        No data
      </div>
    );
  }
  const cx = 130, cy = 130, r = 100, inner = 60;
  let start = -Math.PI / 2;
  const arcs = data.map((d, i) => {
    const angle = (d.value / total) * Math.PI * 2;
    const end = start + angle;
    const x1 = cx + r * Math.cos(start), y1 = cy + r * Math.sin(start);
    const x2 = cx + r * Math.cos(end), y2 = cy + r * Math.sin(end);
    const xi1 = cx + inner * Math.cos(end), yi1 = cy + inner * Math.sin(end);
    const xi2 = cx + inner * Math.cos(start), yi2 = cy + inner * Math.sin(start);
    const large = angle > Math.PI ? 1 : 0;
    const path = `M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2} L ${xi1} ${yi1} A ${inner} ${inner} 0 ${large} 0 ${xi2} ${yi2} Z`;
    const midAngle = start + angle / 2;
    const labelX = cx + (r + 30) * Math.cos(midAngle);
    const labelY = cy + (r + 30) * Math.sin(midAngle);
    const anchor = Math.cos(midAngle) > 0.1 ? "start" : Math.cos(midAngle) < -0.1 ? "end" : "middle";
    const color = PALETTE[i % PALETTE.length];
    const arc = { path, midAngle, labelX, labelY, anchor, color, label: d.label, value: d.value };
    start = end;
    return arc;
  });

  return (
    <div data-testid="chart-quality" className="flex items-center gap-6 h-[260px]">
      <svg viewBox="0 0 480 260" className="h-full flex-1" preserveAspectRatio="xMidYMid meet">
        {arcs.map((a, i) => (
          <g key={i}>
            <path d={a.path} fill={a.color}>
              <title>{a.label}: {a.value.toLocaleString()}</title>
            </path>
            <line
              x1={cx + (r + 4) * Math.cos(a.midAngle)}
              y1={cy + (r + 4) * Math.sin(a.midAngle)}
              x2={a.labelX} y2={a.labelY}
              stroke={a.color} strokeWidth="1" opacity="0.6"
            />
            <text
              x={a.labelX} y={a.labelY} textAnchor={a.anchor}
              fill={a.color} fontSize="11" fontWeight="600"
              dominantBaseline="middle"
            >
              {a.label}: {a.value.toLocaleString()}
            </text>
          </g>
        ))}
        <text x={cx} y={cy - 6} textAnchor="middle" fill="#c9b6ff" fontSize="14" fontWeight="600">
          {total.toLocaleString()}
        </text>
        <text x={cx} y={cy + 12} textAnchor="middle" fill="#8b8ba8" fontSize="10">
          total
        </text>
      </svg>
=======
                  </div>
                ) : (
                  <div className="p-8 text-center text-xs text-slate-400">Select a valid file to view preview data.</div>
                )}
              </div>
            )}

            {/* TAB 7: PIVOT TABLE BUILDER */}
            {tab === "pivot" && (
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-slate-900">Pivot Table Builder</h3>
                <div className="grid gap-3 sm:grid-cols-4 bg-slate-50 p-4 rounded-xl border border-slate-200">
                  <div>
                    <label className="text-[11px] font-bold text-slate-500">Row Fields</label>
                    <select
                      value={pivotRows[0] || ""}
                      onChange={(e) => setPivotRows([e.target.value])}
                      className="w-full rounded-xl border border-slate-300 bg-white p-2 text-xs font-semibold"
                    >
                      {dataset?.columns?.map(c => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-[11px] font-bold text-slate-500">Value Field</label>
                    <select
                      value={pivotVal || ""}
                      onChange={(e) => setPivotVal(e.target.value)}
                      className="w-full rounded-xl border border-slate-300 bg-white p-2 text-xs font-semibold"
                    >
                      {dataset?.columns?.map(c => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-[11px] font-bold text-slate-500">Aggregation</label>
                    <select
                      value={pivotAgg}
                      onChange={(e) => setPivotAgg(e.target.value)}
                      className="w-full rounded-xl border border-slate-300 bg-white p-2 text-xs font-semibold"
                    >
                      <option value="sum">Sum</option>
                      <option value="mean">Average</option>
                      <option value="count">Count</option>
                      <option value="min">Min</option>
                      <option value="max">Max</option>
                    </select>
                  </div>
                  <div className="flex items-end">
                    <button onClick={runPivot} className="w-full rounded-xl bg-blue-600 p-2 text-xs font-bold text-white hover:bg-blue-700">
                      Generate Pivot Table
                    </button>
                  </div>
                </div>

                {pivotResult?.rows?.length > 0 && (
                  <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-900 text-slate-200 text-[10px] font-bold uppercase">
                        <tr>
                          {pivotResult.columns.map(c => <th key={c} className="p-3">{c}</th>)}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {pivotResult.rows.map((r, i) => (
                          <tr key={i} className="hover:bg-slate-50">
                            {pivotResult.columns.map(c => <td key={c} className="p-3">{r[c] != null ? String(r[c]) : "—"}</td>)}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* TAB 8: QUALITY AUDIT */}
            {tab === "validation" && (
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-slate-900">Data Quality Audit</h3>
                <p className="text-xs text-slate-500">Scan dataset for type mismatches, empty values, and outlier formatting.</p>
              </div>
            )}

          </div>
        </div>
      </main>
>>>>>>> a4386bf (Initial commit)
    </div>
  );
}
