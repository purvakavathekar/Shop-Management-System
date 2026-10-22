import { useState, useEffect } from 'react';
import axios from 'axios';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip } from 'chart.js';
import { Html5QrcodeScanner } from 'html5-qrcode';
import './App.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip);

// Backend address (must match the address uvicorn prints when it starts)
const API = 'http://127.0.0.1:8000';

// ==========================================
// Helpers
// ==========================================
const rupee = (n) => '₹' + Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 });

const errMsg = (err, fallback = 'Something went wrong. Try again.') => {
  if (!err.response) return `Cannot reach the server at ${API}. Check that the backend is running.`;
  const detail = err.response.data?.detail;
  return typeof detail === 'string' ? detail : fallback;
};

const TONES = ['violet', 'orange', 'green', 'pink', 'blue'];
const toneFor = (text = '') =>
  TONES[[...String(text)].reduce((sum, ch) => sum + ch.charCodeAt(0), 0) % TONES.length];

const stockStatus = (stock) =>
  stock <= 0
    ? { tone: 'red', label: 'Out of stock' }
    : stock < 5
      ? { tone: 'orange', label: 'Low stock' }
      : { tone: 'green', label: 'Available' };

const matches = (row, q) => !q || Object.values(row).join(' ').toLowerCase().includes(q.toLowerCase());

const fmtDate = (v) => {
  const d = new Date(v);
  return isNaN(d) ? String(v ?? '') : d.toLocaleDateString('en-IN');
};

// QR format used by your labels: id|name|?|price|category
const parseQr = (text) => {
  const parts = text.split('|');
  if (parts.length < 4) return null;
  return { id: parts[0], name: parts[1], price: parts[3], category: parts[4] || 'General' };
};

// ==========================================
// Shared UI pieces
// ==========================================
const ICONS = {
  home: 'M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z',
  box: 'M21 8 12 3 3 8v8l9 5 9-5zM3 8l9 5 9-5M12 13v8',
  receipt: 'M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6',
  chart: 'M4 20V10M10 20V4M16 20v-8M2 20h20',
  logout: 'M9 4H5a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h4M16 8l4 4-4 4M20 12H9',
  search: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM21 21l-4.5-4.5',
  plus: 'M12 5v14M5 12h14',
  x: 'M6 6l12 12M18 6 6 18',
  scan: 'M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3M4 12h16',
  edit: 'M4 20h4L19 9l-4-4L4 16zM13.5 6.5l4 4',
  download: 'M12 4v12M7 11l5 5 5-5M5 20h14',
  alert: 'M12 4 2.5 20h19zM12 10v4M12 17.5v.01',
  info: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 11v5M12 8v.01',
  rupee: 'M7 5h10M7 9h10M7 5c5 0 6 2.5 6 4s-1 4-6 4l7 6',
};

function Icon({ name, size = 20 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={ICONS[name]} />
    </svg>
  );
}

const Pill = ({ tone, children }) => <span className={`pill ${tone}`}>{children}</span>;

function PageHead({ title, children }) {
  return (
    <header className="page-head">
      <h1>{title}</h1>
      {children}
    </header>
  );
}

function Tabs({ items, value, onChange }) {
  return (
    <div className="tabs" role="tablist">
      {items.map((t) => (
        <button
          key={t.id}
          role="tab"
          aria-selected={value === t.id}
          className={`tab ${value === t.id ? 'active' : ''}`}
          onClick={() => onChange(t.id)}
          type="button"
        >
          {t.label}
          {t.count !== undefined && <span className="tab-count">{t.count}</span>}
        </button>
      ))}
    </div>
  );
}

function SearchBox({ value, onChange, placeholder }) {
  return (
    <label className="search">
      <Icon name="search" size={18} />
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} aria-label={placeholder} />
    </label>
  );
}

function Field({ label, ...props }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input {...props} />
    </label>
  );
}

function Modal({ title, onClose, children }) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={title}>
        <h3>{title}</h3>
        {children}
      </div>
    </div>
  );
}

function ConfirmModal({ title, text, confirmLabel, onConfirm, onClose }) {
  return (
    <Modal title={title} onClose={onClose}>
      <p className="modal-text">{text}</p>
      <div className="modal-actions">
        <button className="btn ghost" onClick={onClose}>Cancel</button>
        <button className="btn danger" onClick={onConfirm}>{confirmLabel}</button>
      </div>
    </Modal>
  );
}

function QrScanner({ id, onScan, onClose }) {
  useEffect(() => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = '';
    const scanner = new Html5QrcodeScanner(id, { fps: 10, qrbox: 250 }, false);
    scanner.render(
      (text) => {
        scanner.clear().catch(() => {});
        onScan(text);
      },
      () => {}
    );
    return () => {
      scanner.clear().catch(() => {});
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  return (
    <Modal title="Scan QR code" onClose={onClose}>
      <div id={id} className="reader" />
      <p className="muted">Hold the product's QR label in front of the camera.</p>
      <div className="modal-actions">
        <button className="btn ghost" onClick={onClose}>Cancel</button>
      </div>
    </Modal>
  );
}

function DataTable({ columns, rows, pageSize = 8, empty = 'Nothing to show yet.', resetKey }) {
  const [page, setPage] = useState(1);
  const pages = Math.max(1, Math.ceil(rows.length / pageSize));

  useEffect(() => {
    setPage(1);
  }, [resetKey]);

  const current = Math.min(page, pages);
  const start = (current - 1) * pageSize;
  const slice = rows.slice(start, start + pageSize);

  return (
    <div className="table-wrap">
      <div className="table-scroll">
        <table>
          <thead>
            <tr>{columns.map((c) => <th key={c.label}>{c.label}</th>)}</tr>
          </thead>
          <tbody>
            {slice.length === 0 ? (
              <tr className="empty-row"><td colSpan={columns.length}>{empty}</td></tr>
            ) : (
              slice.map((row, i) => (
                <tr key={row.id ?? i}>
                  {columns.map((c) => <td key={c.label}>{c.render(row)}</td>)}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {rows.length > pageSize && (
        <div className="pager">
          <span>Showing {start + 1}–{Math.min(start + pageSize, rows.length)} of {rows.length}</span>
          <div className="pager-btns">
            <button disabled={current === 1} onClick={() => setPage(current - 1)} aria-label="Previous page">‹</button>
            {Array.from({ length: pages }, (_, i) => i + 1).map((n) => (
              <button key={n} className={n === current ? 'on' : ''} onClick={() => setPage(n)}>{n}</button>
            ))}
            <button disabled={current === pages} onClick={() => setPage(current + 1)} aria-label="Next page">›</button>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon, tone, label, value }) {
  return (
    <div className="stat">
      <span className={`stat-icon ${tone}`}><Icon name={icon} size={22} /></span>
      <div>
        <span className="stat-label">{label}</span>
        <span className="stat-value">{value}</span>
      </div>
    </div>
  );
}

// ==========================================
// App shell
// ==========================================
const NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: 'home' },
  { id: 'inventory', label: 'Inventory', icon: 'box' },
  { id: 'billing', label: 'Billing', icon: 'receipt' },
  { id: 'sales', label: 'Sales', icon: 'chart' },
];

export default function App() {
  const [user, setUser] = useState(localStorage.getItem('user'));
  const [page, setPage] = useState('dashboard');
  const [toast, setToast] = useState(null);

  const notify = (msg, tone = 'ok') => {
    setToast({ msg, tone });
    setTimeout(() => setToast(null), 3200);
  };

  const logout = () => {
    localStorage.removeItem('user');
    setUser(null);
    setPage('dashboard');
  };

  if (!user) return <Login setUser={setUser} />;

  const pages = { dashboard: Dashboard, inventory: Inventory, billing: Billing, sales: Sales };
  const Page = pages[page];

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">S</span>
          <div>
            <strong>Shop Manager</strong>
            <small>Inventory and billing</small>
          </div>
        </div>

        <nav className="nav" aria-label="Main">
          {NAV.map((n) => (
            <button
              key={n.id}
              className={page === n.id ? 'active' : ''}
              aria-current={page === n.id ? 'page' : undefined}
              onClick={() => setPage(n.id)}
            >
              <Icon name={n.icon} />
              {n.label}
            </button>
          ))}
        </nav>

        <div className="user-chip">
          <span className="avatar">{String(user)[0].toUpperCase()}</span>
          <span className="user-name">{user}</span>
          <button className="icon-btn" onClick={logout} aria-label="Log out" title="Log out">
            <Icon name="logout" size={18} />
          </button>
        </div>
      </aside>

      <main className="main">
        <Page user={user} notify={notify} setPage={setPage} />
      </main>

      {toast && <div className={`toast ${toast.tone}`} role="status">{toast.msg}</div>}
    </div>
  );
}

// ==========================================
// 1. LOGIN
// ==========================================
function Login({ setUser }) {
  const [mode, setMode] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const isLogin = mode === 'login';

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setNotice('');
    setBusy(true);
    try {
      const { data } = await axios.post(`${API}/api/${isLogin ? 'login' : 'register'}`, { username, password });
      if (isLogin) {
        localStorage.setItem('user', data.user);
        setUser(data.user);
      } else {
        setMode('login');
        setPassword('');
        setNotice('Account created. Log in to continue.');
      }
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth">
      <form className="auth-card" onSubmit={submit}>
        <div className="brand">
          <span className="brand-mark">S</span>
          <div><strong>Shop Manager</strong></div>
        </div>
        <h1>{isLogin ? 'Welcome back' : 'Create your account'}</h1>
        <p className="muted">
          {isLogin ? 'Log in to manage stock, bills and sales.' : 'Choose a username and password to get started.'}
        </p>

        <Tabs
          items={[{ id: 'login', label: 'Log in' }, { id: 'register', label: 'Sign up' }]}
          value={mode}
          onChange={(m) => { setMode(m); setError(''); setNotice(''); }}
        />

        {error && <div className="note error" role="alert">{error}</div>}
        {notice && <div className="note ok" role="status">{notice}</div>}

        <Field label="Username" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required />
        <Field
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete={isLogin ? 'current-password' : 'new-password'}
          required
        />
        <button className="btn primary block" disabled={busy}>
          {busy ? 'Please wait…' : isLogin ? 'Log in' : 'Create account'}
        </button>
      </form>
    </div>
  );
}

// ==========================================
// 2. DASHBOARD
// ==========================================
function Dashboard({ setPage }) {
  const [products, setProducts] = useState([]);
  const [revenue, setRevenue] = useState(null);

  useEffect(() => {
    axios.get(`${API}/api/products`).then((r) => setProducts(r.data)).catch(() => {});
    axios.get(`${API}/api/sales/total`).then((r) => setRevenue(r.data.total)).catch(() => {});
  }, []);

  const lowStock = products.filter((p) => p.stock < 5).sort((a, b) => a.stock - b.stock);

  const columns = [
    { label: 'ID', render: (p) => p.id },
    { label: 'Product', render: (p) => <strong>{p.name}</strong> },
    { label: 'Category', render: (p) => <Pill tone={toneFor(p.category)}>{p.category}</Pill> },
    { label: 'In stock', render: (p) => p.stock },
    { label: 'Status', render: (p) => { const s = stockStatus(p.stock); return <Pill tone={s.tone}>{s.label}</Pill>; } },
  ];

  return (
    <>
      <PageHead title="Dashboard">
        <button className="btn primary" onClick={() => setPage('billing')}>
          <Icon name="receipt" size={18} /> New bill
        </button>
        <button className="btn ghost" onClick={() => setPage('inventory')}>
          <Icon name="box" size={18} /> Manage inventory
        </button>
      </PageHead>

      <div className="stats">
        <StatCard icon="box" tone="violet" label="Products" value={products.length} />
        <StatCard icon="alert" tone="orange" label="Low or out of stock" value={lowStock.length} />
        <StatCard icon="rupee" tone="green" label="Total revenue" value={revenue === null ? '–' : rupee(revenue)} />
      </div>

      <h2 className="section-title">Needs restocking</h2>
      <DataTable columns={columns} rows={lowStock} empty="Every product is well stocked." />
    </>
  );
}

// ==========================================
// 3. INVENTORY
// ==========================================
function ProductFormModal({ onClose, onCreated }) {
  const [f, setF] = useState({ id: '', name: '', company: '', category: 'General', price: '', stock: '' });
  const [error, setError] = useState('');
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const { data } = await axios.post(`${API}/api/products`, {
        id: parseInt(f.id),
        name: f.name.trim(),
        company: f.company.trim() || 'Generic',
        category: f.category.trim() || 'General',
        price: parseInt(f.price),
        stock: parseInt(f.stock),
      });
      onCreated({ id: parseInt(f.id), name: f.name.trim(), qr: data.qr });
    } catch (err) {
      setError(errMsg(err));
    }
  };

  return (
    <Modal title="Add product" onClose={onClose}>
      <form onSubmit={submit}>
        {error && <div className="note error" role="alert">{error}</div>}
        <div className="field-grid">
          <Field label="Product ID" type="number" min="1" value={f.id} onChange={set('id')} required autoFocus />
          <Field label="Category" value={f.category} onChange={set('category')} placeholder="Dairy, Grocery, Fruits…" required />
          <div className="full"><Field label="Product name" value={f.name} onChange={set('name')} placeholder="Milk, Apple, Flour…" required /></div>
          <div className="full"><Field label="Brand or company" value={f.company} onChange={set('company')} placeholder="Generic" /></div>
          <Field label="Price (₹)" type="number" min="0" value={f.price} onChange={set('price')} required />
          <Field label="Quantity" type="number" min="0" value={f.stock} onChange={set('stock')} required />
        </div>
        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={onClose}>Cancel</button>
          <button className="btn primary">Add and create QR</button>
        </div>
      </form>
    </Modal>
  );
}

function QrResultModal({ result, onClose }) {
  return (
    <Modal title="Product added" onClose={onClose}>
      <p className="modal-text">
        {result.name} is now in inventory. Download its QR label and stick it on the product so it can be scanned.
      </p>
      <img className="qr-preview" src={result.qr} alt={`QR code for ${result.name}`} />
      <div className="modal-actions">
        <a className="btn ghost" href={result.qr} download={`${result.id}.png`}>Download {result.id}.png</a>
        <button className="btn primary" onClick={onClose}>Done</button>
      </div>
    </Modal>
  );
}

function DetailsModal({ item, onClose }) {
  const s = stockStatus(item.stock);
  return (
    <Modal title="Product details" onClose={onClose}>
      <dl className="details">
        <dt>ID</dt><dd>{item.id}</dd>
        <dt>Name</dt><dd>{item.name}</dd>
        <dt>Category</dt><dd><Pill tone={toneFor(item.category)}>{item.category}</Pill></dd>
        <dt>Price</dt><dd>{rupee(item.price)}</dd>
        <dt>Stock</dt><dd>{item.stock}</dd>
        <dt>Status</dt><dd><Pill tone={s.tone}>{s.label}</Pill></dd>
      </dl>
      <div className="modal-actions">
        <button className="btn primary" onClick={onClose}>Close</button>
      </div>
    </Modal>
  );
}

function StockModal({ item, onClose, onDone }) {
  const [qty, setQty] = useState('');
  const [error, setError] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    const n = parseInt(qty);
    if (!n || n < 1) return setError('Enter a quantity of 1 or more.');
    try {
      const { data } = await axios.post(`${API}/api/products/scan`, {
        id: parseInt(item.id),
        name: item.name,
        price: parseInt(item.price),
        category: item.category,
        stock: n,
      });
      onDone(data.message);
    } catch (err) {
      setError(errMsg(err));
    }
  };

  return (
    <Modal title="Add stock" onClose={onClose}>
      <form onSubmit={submit}>
        <div className="product-line">
          <strong>{item.name}</strong>
          <Pill tone={toneFor(item.category)}>{item.category}</Pill>
          <span className="muted">{rupee(item.price)}</span>
        </div>
        {error && <div className="note error" role="alert">{error}</div>}
        <Field label="Quantity" type="number" min="1" value={qty} onChange={(e) => setQty(e.target.value)} autoFocus required />
        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={onClose}>Cancel</button>
          <button className="btn success">Add stock</button>
        </div>
      </form>
    </Modal>
  );
}

function Inventory({ notify }) {
  const [products, setProducts] = useState([]);
  const [filter, setFilter] = useState('all');
  const [q, setQ] = useState('');
  const [modal, setModal] = useState(null);

  const load = async () => {
    try {
      const { data } = await axios.get(`${API}/api/products`);
      setProducts(data);
    } catch (e) {
      notify(errMsg(e), 'error');
    }
  };
  useEffect(() => { load(); }, []);

  const close = () => setModal(null);
  const done = (msg) => { notify(msg); close(); load(); };

  const inFilter = (p) =>
    filter === 'ok' ? p.stock >= 5 : filter === 'low' ? p.stock > 0 && p.stock < 5 : filter === 'out' ? p.stock <= 0 : true;

  const counts = {
    all: products.length,
    ok: products.filter((p) => p.stock >= 5).length,
    low: products.filter((p) => p.stock > 0 && p.stock < 5).length,
    out: products.filter((p) => p.stock <= 0).length,
  };
  const rows = products.filter(inFilter).filter((p) => matches(p, q));

  const removeProduct = async (p) => {
    try {
      await axios.delete(`${API}/api/products/${p.id}`);
      done(`${p.name} removed.`);
    } catch (e) {
      notify(errMsg(e), 'error');
      close();
    }
  };

  const columns = [
    { label: 'ID', render: (p) => p.id },
    { label: 'Product', render: (p) => <strong>{p.name}</strong> },
    { label: 'Category', render: (p) => <Pill tone={toneFor(p.category)}>{p.category}</Pill> },
    { label: 'Price', render: (p) => rupee(p.price) },
    { label: 'In stock', render: (p) => p.stock },
    { label: 'Status', render: (p) => { const s = stockStatus(p.stock); return <Pill tone={s.tone}>{s.label}</Pill>; } },
    {
      label: 'Actions',
      render: (p) => (
        <div className="row-actions">
          <button
            className="round-btn sm purple"
            title="Check status"
            aria-label={`Check status of ${p.name}`}
            onClick={() => setModal({ type: 'details', item: p })}
          >
            <Icon name="info" size={16} />
          </button>
          <button
            className="round-btn sm green"
            title="Add stock"
            aria-label={`Add stock to ${p.name}`}
            onClick={() => setModal({ type: 'stock', item: { id: p.id, name: p.name, price: p.price, category: p.category } })}
          >
            <Icon name="plus" size={16} />
          </button>
          <button
            className="round-btn sm red"
            title="Delete product"
            aria-label={`Delete ${p.name}`}
            onClick={() => setModal({ type: 'delete', item: p })}
          >
            <Icon name="x" size={16} />
          </button>
        </div>
      ),
    },
  ];

  return (
    <>
      <PageHead title="Inventory">
        <button className="round-btn green" title="Add product" aria-label="Add product" onClick={() => setModal({ type: 'add' })}>
          <Icon name="plus" />
        </button>
        <button className="round-btn purple" title="Scan QR to add stock" aria-label="Scan QR to add stock" onClick={() => setModal({ type: 'scan' })}>
          <Icon name="scan" />
        </button>
        <Tabs
          value={filter}
          onChange={setFilter}
          items={[
            { id: 'all', label: 'All', count: counts.all },
            { id: 'ok', label: 'Available', count: counts.ok },
            { id: 'low', label: 'Low stock', count: counts.low },
            { id: 'out', label: 'Out of stock', count: counts.out },
          ]}
        />
        <SearchBox value={q} onChange={setQ} placeholder="Search products" />
      </PageHead>

      <DataTable columns={columns} rows={rows} resetKey={`${filter}|${q}`} empty="No products match. Add one with the green + button." />

      {modal?.type === 'add' && <ProductFormModal onClose={close} onCreated={(r) => { load(); setModal({ type: 'qr', result: r }); }} />}
      {modal?.type === 'qr' && <QrResultModal result={modal.result} onClose={close} />}
      {modal?.type === 'details' && <DetailsModal item={modal.item} onClose={close} />}
      {modal?.type === 'scan' && (
        <QrScanner
          id="inventory-reader"
          onClose={close}
          onScan={(text) => {
            const item = parseQr(text);
            if (!item) { notify('That QR code is not a product label.', 'error'); return close(); }
            setModal({ type: 'stock', item });
          }}
        />
      )}
      {modal?.type === 'stock' && <StockModal item={modal.item} onClose={close} onDone={done} />}
      {modal?.type === 'delete' && (
        <ConfirmModal
          title="Delete product"
          text={`Remove ${modal.item.name} (ID ${modal.item.id}) from inventory? This cannot be undone.`}
          confirmLabel="Delete product"
          onClose={close}
          onConfirm={() => removeProduct(modal.item)}
        />
      )}
    </>
  );
}

// ==========================================
// 4. BILLING
// ==========================================
function AddToBillModal({ preset, products = [], onClose, onAdd }) {
  const [picked, setPicked] = useState(preset ? { id: preset.id, name: preset.name } : null);
  const [category, setCategory] = useState('all');
  const [q, setQ] = useState('');
  const [qty, setQty] = useState('');
  const [error, setError] = useState('');

  const categories = [...new Set(products.map((p) => p.category))].sort();
  const list = products.filter(
    (p) =>
      (category === 'all' || p.category === category) &&
      String(p.name).toLowerCase().includes(q.trim().toLowerCase())
  );
  const pickedStock = picked ? products.find((p) => String(p.id) === String(picked.id))?.stock : undefined;

  const submit = async (e) => {
    e.preventDefault();
    const n = parseInt(qty);
    if (!picked) return setError('Choose a product from the list.');
    if (!n || n < 1) return setError('Enter a quantity of 1 or more.');
    if (pickedStock !== undefined && n > pickedStock) return setError(`Only ${pickedStock} in stock.`);
    const err = await onAdd(parseInt(picked.id), n);
    if (err) setError(err);
  };

  return (
    <Modal title="Add to bill" onClose={onClose}>
      <form onSubmit={submit}>
        {preset ? (
          <div className="product-line">
            <strong>{preset.name}</strong>
          </div>
        ) : (
          <>
            <div className="picker-filters">
              <select className="select" value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Filter by category">
                <option value="all">All categories</option>
                {categories.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
              <input
                className="picker-search"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search by product name"
                aria-label="Search by product name"
                autoFocus
              />
            </div>
            <div className="picker-list" role="listbox" aria-label="Products">
              {list.length === 0 ? (
                <p className="muted picker-empty">No products match.</p>
              ) : (
                list.map((p) => (
                  <button
                    type="button"
                    key={p.id}
                    role="option"
                    aria-selected={picked?.id === p.id}
                    disabled={p.stock <= 0}
                    className={`picker-item ${picked?.id === p.id ? 'on' : ''}`}
                    onClick={() => { setPicked({ id: p.id, name: p.name }); setError(''); }}
                  >
                    <span className="picker-name">
                      <strong>{p.name}</strong>
                      <Pill tone={toneFor(p.category)}>{p.category}</Pill>
                    </span>
                    <span className="picker-meta">
                      <span>{rupee(p.price)}</span>
                      <span>{p.stock <= 0 ? 'Out of stock' : `${p.stock} in stock`}</span>
                    </span>
                  </button>
                ))
              )}
            </div>
          </>
        )}

        {error && <div className="note error" role="alert">{error}</div>}
        <Field
          label={picked ? `Quantity of ${picked.name}` : 'Quantity'}
          type="number"
          min="1"
          max={pickedStock}
          value={qty}
          onChange={(e) => setQty(e.target.value)}
          autoFocus={!!preset}
          required
        />
        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={onClose}>Cancel</button>
          <button className="btn success">Add to bill</button>
        </div>
      </form>
    </Modal>
  );
}

function EditQtyModal({ item, onClose, onSave }) {
  const [qty, setQty] = useState(String(item.qty));

  const submit = (e) => {
    e.preventDefault();
    const n = parseInt(qty);
    if (isNaN(n) || n < 0) return;
    onSave(n);
  };

  return (
    <Modal title="Change quantity" onClose={onClose}>
      <form onSubmit={submit}>
        <div className="product-line">
          <strong>{item.name}</strong>
          <span className="muted">Currently {item.qty}</span>
        </div>
        <Field label="Quantity to keep" type="number" min="0" max={item.qty} value={qty} onChange={(e) => setQty(e.target.value)} autoFocus required />
        <div className="modal-actions">
          <button type="button" className="btn danger" onClick={() => onSave(0)}>Remove item</button>
          <button className="btn primary">Save quantity</button>
        </div>
      </form>
    </Modal>
  );
}

function ReceiptModal({ receipt, onClose }) {
  const money = (n) => Number(n).toFixed(2);
  return (
    <Modal title={`Bill ${receipt.billno}`} onClose={onClose}>
      <div className="receipt">
        <p className="receipt-title">Shop bill receipt</p>
        <p className="receipt-meta">Bill number {receipt.billno}</p>
        <p className="receipt-meta">{receipt.date}</p>
        <hr />
        <div className="receipt-line head">
          <span>Product</span><span>Qty</span><span>Price</span><span>Total</span>
        </div>
        <hr />
        {receipt.items.map((it, i) => (
          <div className="receipt-line" key={i}>
            <span>{it[1]}</span><span>{it[4]}</span><span>{money(it[3])}</span><span>{money(it[5])}</span>
          </div>
        ))}
        <hr />
        <div className="receipt-row total">
          <span>Grand total</span>
          <span>Rs. {money(receipt.grand_total)}</span>
        </div>
        <p className="receipt-thanks">Thank you for shopping!</p>
      </div>
      <div className="modal-actions">
        <button className="btn ghost" onClick={() => window.print()}>Print</button>
        <button className="btn primary" onClick={onClose}>Done</button>
      </div>
    </Modal>
  );
}

function Billing({ user, notify }) {
  const [cart, setCart] = useState({ bill: [], grand_total: 0 });
  const [products, setProducts] = useState([]);
  const [modal, setModal] = useState(null);

  const loadCart = async () => {
    try {
      const { data } = await axios.get(`${API}/api/cart/${user}`);
      setCart(data);
    } catch (e) {
      notify(errMsg(e), 'error');
    }
  };
  const loadProducts = async () => {
    try {
      const { data } = await axios.get(`${API}/api/products`);
      setProducts(data);
    } catch (e) {
      notify(errMsg(e), 'error');
    }
  };
  useEffect(() => { loadCart(); loadProducts(); }, []);

  const close = () => setModal(null);
  const items = cart.bill.map((it) => ({ id: it[0], name: it[1], category: it[2], price: it[3], qty: it[4], amount: it[5] }));

  // Returns an error string on failure so the modal can show it
  const addToBill = async (id, qty) => {
    try {
      const { data } = await axios.post(`${API}/api/cart/${user}`, { id, qty });
      await loadCart();
      loadProducts();
      notify(data.message);
      close();
    } catch (e) {
      return errMsg(e);
    }
  };

  const setQty = async (id, newQty) => {
    try {
      const { data } = await axios.post(`${API}/api/cart/${user}/remove`, { id, new_qty: newQty });
      await loadCart();
      loadProducts();
      notify(data.message);
      close();
    } catch (e) {
      notify(errMsg(e), 'error');
    }
  };

  const finishBill = async () => {
    try {
      const { data } = await axios.post(`${API}/api/checkout/${user}`);
      await loadCart();
      notify(`Bill ${data.receipt.billno} saved.`);
      setModal({ type: 'receipt', receipt: data.receipt });
    } catch (e) {
      notify(errMsg(e), 'error');
    }
  };

  const clearBill = async () => {
    try {
      await axios.post(`${API}/api/cart/${user}/clear`);
      await loadCart();
      loadProducts();
      notify('Bill cleared.');
    } catch (e) {
      notify(errMsg(e), 'error');
    }
    close();
  };

  const columns = [
    { label: 'ID', render: (r) => r.id },
    { label: 'Product', render: (r) => <strong>{r.name}</strong> },
    { label: 'Category', render: (r) => <Pill tone={toneFor(r.category)}>{r.category}</Pill> },
    { label: 'Price', render: (r) => rupee(r.price) },
    { label: 'Qty', render: (r) => r.qty },
    { label: 'Amount', render: (r) => <strong>{rupee(r.amount)}</strong> },
    {
      label: 'Actions',
      render: (r) => (
        <div className="row-actions">
          <button className="round-btn sm purple" title="Change quantity" aria-label={`Change quantity of ${r.name}`} onClick={() => setModal({ type: 'edit', item: r })}>
            <Icon name="edit" size={15} />
          </button>
          <button className="round-btn sm red" title="Remove from bill" aria-label={`Remove ${r.name} from bill`} onClick={() => setQty(r.id, 0)}>
            <Icon name="x" size={16} />
          </button>
        </div>
      ),
    },
  ];

  const units = items.reduce((s, r) => s + r.qty, 0);

  return (
    <>
      <PageHead title="Billing">
        <button className="round-btn green" title="Add product by ID" aria-label="Add product by ID" onClick={() => setModal({ type: 'add' })}>
          <Icon name="plus" />
        </button>
        <button className="round-btn purple" title="Scan product QR" aria-label="Scan product QR" onClick={() => setModal({ type: 'scan' })}>
          <Icon name="scan" />
        </button>
      </PageHead>

      <div className="billing-grid">
        <DataTable columns={columns} rows={items} empty="The bill is empty. Add a product with the green + button or scan its QR code." />

        <aside className="summary">
          <span className="summary-label">Current bill</span>
          <strong className="summary-total">{rupee(cart.grand_total)}</strong>
          <p>{items.length} {items.length === 1 ? 'product' : 'products'}, {units} {units === 1 ? 'unit' : 'units'}</p>
          <button className="btn success block" disabled={!items.length} onClick={finishBill}>Finish bill</button>
          <button className="btn outline-light block" disabled={!items.length} onClick={() => setModal({ type: 'clear' })}>Clear bill</button>
        </aside>
      </div>

      {modal?.type === 'add' && <AddToBillModal products={products} onClose={close} onAdd={addToBill} />}
      {modal?.type === 'scan' && (
        <QrScanner
          id="billing-reader"
          onClose={close}
          onScan={(text) => {
            const p = parseQr(text);
            if (!p) { notify('That QR code is not a product label.', 'error'); return close(); }
            setModal({ type: 'addScanned', preset: p });
          }}
        />
      )}
      {modal?.type === 'addScanned' && <AddToBillModal preset={modal.preset} onClose={close} onAdd={addToBill} />}
      {modal?.type === 'edit' && <EditQtyModal item={modal.item} onClose={close} onSave={(n) => setQty(modal.item.id, n)} />}
      {modal?.type === 'clear' && (
        <ConfirmModal
          title="Clear bill"
          text="Remove every product from the current bill? Their stock goes back to inventory."
          confirmLabel="Clear bill"
          onClose={close}
          onConfirm={clearBill}
        />
      )}
      {modal?.type === 'receipt' && <ReceiptModal receipt={modal.receipt} onClose={close} />}
    </>
  );
}

// ==========================================
// 5. SALES
// ==========================================
function Sales({ notify }) {
  const [tab, setTab] = useState('overview');
  const [q, setQ] = useState('');
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [cats, setCats] = useState([]);
  const [prods, setProds] = useState([]);

  useEffect(() => {
    (async () => {
      try {
        setRows((await axios.get(`${API}/api/sales`)).data);
        setTotal((await axios.get(`${API}/api/sales/total`)).data.total);
        setCats((await axios.get(`${API}/api/sales/category`)).data);
        setProds((await axios.get(`${API}/api/sales/product`)).data);
      } catch (e) {
        notify(errMsg(e), 'error');
      }
    })();
  }, []);

  const exportCSV = () => {
    if (rows.length === 0) return notify('There is no sales data to export.', 'error');
    const cell = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
    const keys = Object.keys(rows[0]);
    const header = keys.join(',') + '\n';
    const body = rows.map((r) => keys.map((k) => cell(r[k])).join(',')).join('\n');
    const blob = new Blob([header + body], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'sales_report.csv';
    a.click();
  };

  const topCat = [...cats].sort((a, b) => b.revenue - a.revenue)[0];
  const billCount = new Set(rows.map((r) => r.billno)).size;

  const chartData = {
    labels: cats.map((c) => c.category),
    datasets: [{ label: 'Revenue', data: cats.map((c) => c.revenue), backgroundColor: '#6a56d6', borderRadius: 8, maxBarThickness: 48 }],
  };
  const chartOptions = {
    responsive: true,
    plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => rupee(c.parsed.y) } } },
    scales: {
      y: { grid: { color: '#ece9fb' }, ticks: { callback: (v) => rupee(v) } },
      x: { grid: { display: false } },
    },
  };

  const tables = {
    bills: {
      rows: rows.filter((r) => matches(r, q)),
      empty: 'No sales recorded yet.',
      columns: [
        { label: 'Bill', render: (r) => r.billno },
        { label: 'Product ID', render: (r) => r.pid },
        { label: 'Product', render: (r) => <strong>{r.name}</strong> },
        { label: 'Category', render: (r) => <Pill tone={toneFor(r.category)}>{r.category}</Pill> },
        { label: 'Price', render: (r) => '₹' + (r.qty ? r.amount / r.qty : 0).toFixed(2) },
        { label: 'Qty', render: (r) => r.qty },
        { label: 'Amount', render: (r) => rupee(r.amount) },
        { label: 'Date', render: (r) => fmtDate(r.sale_date) },
      ],
    },
    categories: {
      rows: cats.filter((r) => matches(r, q)),
      empty: 'No category sales yet.',
      columns: [
        { label: 'Category', render: (r) => <Pill tone={toneFor(r.category)}>{r.category}</Pill> },
        { label: 'Revenue', render: (r) => <strong>{rupee(r.revenue)}</strong> },
        { label: 'Transactions', render: (r) => r.transactions },
      ],
    },
    products: {
      rows: prods.filter((r) => matches(r, q)),
      empty: 'No product sales yet.',
      columns: [
        { label: 'Product', render: (r) => <strong>{r.name}</strong> },
        { label: 'Category', render: (r) => <Pill tone={toneFor(r.category)}>{r.category}</Pill> },
        { label: 'Revenue', render: (r) => rupee(r.amount) },
      ],
    },
  };

  return (
    <>
      <PageHead title="Sales">
        <button className="round-btn purple" title="Export CSV" aria-label="Export sales as CSV" onClick={exportCSV}>
          <Icon name="download" />
        </button>
        <Tabs
          value={tab}
          onChange={(t) => { setTab(t); setQ(''); }}
          items={[
            { id: 'overview', label: 'Overview' },
            { id: 'bills', label: 'All sales' },
            { id: 'categories', label: 'By category' },
            { id: 'products', label: 'By product' },
          ]}
        />
        {tab !== 'overview' && <SearchBox value={q} onChange={setQ} placeholder="Search sales" />}
      </PageHead>

      {tab === 'overview' ? (
        <>
          <div className="stats">
            <StatCard icon="rupee" tone="green" label="Total revenue" value={rupee(total)} />
            <StatCard icon="receipt" tone="violet" label="Bills issued" value={billCount} />
            <StatCard icon="chart" tone="pink" label="Top category" value={topCat ? topCat.category : '–'} />
          </div>
          <h2 className="section-title">Revenue by category</h2>
          <div className="chart-card">
            {cats.length ? <Bar data={chartData} options={chartOptions} /> : <p className="muted">No sales yet. Finish a bill to see revenue here.</p>}
          </div>
        </>
      ) : (
        <>
          {tab === 'categories' && topCat && (
            <p className="top-line">
              Top performing category: <Pill tone={toneFor(topCat.category)}>{topCat.category}</Pill>
            </p>
          )}
          <DataTable columns={tables[tab].columns} rows={tables[tab].rows} empty={tables[tab].empty} resetKey={`${tab}|${q}`} />
        </>
      )}
    </>
  );
}