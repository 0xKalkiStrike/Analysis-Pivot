import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import {
  Database, FileSpreadsheet, Copy, ShieldCheck, Table, Network,
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
export default function ExcelIntelDashboard() {
  const [samples, setSamples] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedSheet, setSelectedSheet] = useState(null);
  const [summary, setSummary] = useState(null);
  const [dataset, setDataset] = useState(null);
  const [duplicates, setDuplicates] = useState(null);
  const [relationships, setRelationships] = useState(null);
  const [threshold, setThreshold] = useState(90);
  const [search, setSearch] = useState("");
  const [loadingDup, setLoadingDup] = useState(false);
  const [tab, setTab] = useState("data");
  const [paletteOpen, setPaletteOpen] = useState(false);

  // Boot
  useEffect(() => {
    axios.get(`${API}/samples`).then((res) => {
      setSamples(res.data.files);
      if (res.data.files.length) {
        const f = res.data.files[0];
        setSelectedFile(f.name);
        setSelectedSheet(f.sheets?.[0] || null);
      }
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
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
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
    </div>
  );
}
