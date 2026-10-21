import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

// Latest run per store, newest first (the API returns runs newest first).
function LastRuns({ runs, formatDate }) {
  const latest = Object.values(
    runs.reduce((byStore, run) => ({ ...byStore, [run.store]: byStore[run.store] ?? run }), {})
  );
  if (latest.length === 0) return null;

  const colors = { success: '#f0fdf4', partial: '#fffbeb', failed: '#fef2f2', running: '#eff6ff' };
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '16px' }}>
      {latest.map(run => (
        <div key={run.id} style={{
          background: colors[run.status] ?? '#f8fafc', border: '1px solid #e2e8f0',
          borderRadius: '6px', padding: '8px 14px', fontSize: '14px',
        }}>
          <strong>{run.store}</strong> · last scrape {formatDate(run.started_at)} · {run.status} ·{' '}
          {run.items_found} variants, {run.prices_changed} price changes
          {run.errors > 0 && `, ${run.errors} errors`}
        </div>
      ))}
    </div>
  );
}

function ExtractionStatus() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [runs, setRuns] = useState([]);

  const fetchStatus = useCallback(async () => {
    try {
      const [status, scrapeRuns] = await Promise.all([
        axios.get('/api/extraction-status/'),
        axios.get('/api/scrape-runs/'),
      ]);
      setRows(status.data);
      setRuns(scrapeRuns.data);
    } catch (e) {
      console.error('Failed to load status:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);

  const formatDate = (iso) => {
    if (!iso) return '—';
    const d = new Date(iso);
    return d.toLocaleString();
  };

  const staleDays = (iso) => {
    if (!iso) return null;
    return Math.floor((Date.now() - new Date(iso)) / 86400000);
  };

  return (
    <div style={{ padding: '24px' }}>
      <h2 style={{ margin: '0 0 16px' }}>Extraction Status</h2>

      <LastRuns runs={runs} formatDate={formatDate} />

      {loading ? (
        <p>Loading...</p>
      ) : rows.length === 0 ? (
        <p>No products in the database yet. Run the scraper: <code>docker compose run --rm scraper</code></p>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ background: '#f1f5f9', textAlign: 'left' }}>
                <th style={th}>Brand</th>
                <th style={th}>Product</th>
                <th style={th}>Weight</th>
                <th style={th}>Price (€)</th>
                <th style={th}>€/100g</th>
                <th style={th}>Protein/100g</th>
                <th style={th}>Carbs/100g</th>
                <th style={th}>Fat/100g</th>
                <th style={th}>Available</th>
                <th style={th}>Last Extracted</th>
                <th style={th}>Link</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const days = staleDays(row.last_extracted);
                const stale = days !== null && days > 7;
                return (
                  <tr key={row.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                    <td style={td}>{row.brand}</td>
                    <td style={td}>{row.flavor ? `${row.name} · ${row.flavor}` : row.name}</td>
                    <td style={td}>{row.weight_g != null ? `${row.weight_g}g` : '—'}</td>
                    <td style={td}>{row.price_eur != null ? row.price_eur.toFixed(2) : '—'}</td>
                    <td style={td}>{row.price_per_100g != null ? row.price_per_100g.toFixed(2) : '—'}</td>
                    <td style={{ ...td, color: row.protein_g != null ? '#166534' : '#9ca3af' }}>
                      {row.protein_g != null ? `${row.protein_g}g` : '—'}
                    </td>
                    <td style={{ ...td, color: row.carbs_g != null ? '#1d4ed8' : '#9ca3af' }}>
                      {row.carbs_g != null ? `${row.carbs_g}g` : '—'}
                    </td>
                    <td style={{ ...td, color: row.fat_g != null ? '#b45309' : '#9ca3af' }}>
                      {row.fat_g != null ? `${row.fat_g}g` : '—'}
                    </td>
                    <td style={td}>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        background: row.is_available ? '#dcfce7' : '#fee2e2',
                        color: row.is_available ? '#166534' : '#991b1b',
                      }}>
                        {row.is_available ? 'In Stock' : 'Out of Stock'}
                      </span>
                    </td>
                    <td style={{ ...td, color: stale ? '#b45309' : '#166534' }}>
                      {formatDate(row.last_extracted)}
                      {stale && <span style={{ marginLeft: '6px', fontSize: '11px' }}>(stale)</span>}
                    </td>
                    <td style={td}>
                      <a href={row.product_url} target="_blank" rel="noreferrer"
                        style={{ color: '#2563eb' }}>
                        View
                      </a>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const th = {
  padding: '10px 12px',
  fontWeight: 600,
  borderBottom: '2px solid #e2e8f0',
  whiteSpace: 'nowrap',
};

const td = {
  padding: '10px 12px',
  verticalAlign: 'middle',
};

export default ExtractionStatus;
