import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

function ExtractionStatus() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [lastRun, setLastRun] = useState(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await axios.get('/api/extraction-status/');
      setRows(res.data);
    } catch (e) {
      console.error('Failed to load status:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);

  const handleRunExtraction = async () => {
    setRunning(true);
    setLastRun(null);
    try {
      const res = await axios.post('/api/run-extraction/');
      setLastRun(res.data);
      await fetchStatus();
    } catch (e) {
      setLastRun({ error: e.message });
    } finally {
      setRunning(false);
    }
  };

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
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
        <h2 style={{ margin: 0 }}>Extraction Status</h2>
        <button
          onClick={handleRunExtraction}
          disabled={running}
          style={{
            padding: '8px 20px',
            background: running ? '#999' : '#2563eb',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            cursor: running ? 'not-allowed' : 'pointer',
            fontWeight: 600,
          }}
        >
          {running ? 'Running...' : 'Run Extraction'}
        </button>
        {running && (
          <span style={{ color: '#666', fontSize: '14px' }}>
            Fetching prices — this takes ~2 min
          </span>
        )}
      </div>

      {lastRun && !lastRun.error && (
        <div style={{
          background: '#f0fdf4', border: '1px solid #86efac',
          borderRadius: '6px', padding: '10px 16px', marginBottom: '16px',
          fontSize: '14px',
        }}>
          Last run: <strong>{lastRun.saved}</strong> saved,{' '}
          <strong>{lastRun.extracted - lastRun.saved}</strong> skipped,{' '}
          <strong>{lastRun.failed?.length ?? 0}</strong> errors
          {' '}across <strong>{lastRun.files_processed}</strong> link file(s).
        </div>
      )}

      {lastRun?.error && (
        <div style={{
          background: '#fef2f2', border: '1px solid #fca5a5',
          borderRadius: '6px', padding: '10px 16px', marginBottom: '16px',
          fontSize: '14px',
        }}>
          Error: {lastRun.error}
        </div>
      )}

      {loading ? (
        <p>Loading...</p>
      ) : rows.length === 0 ? (
        <p>No products in the database yet. Run an extraction first.</p>
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
                    <td style={td}>{row.name}</td>
                    <td style={td}>{row.weight_g}g</td>
                    <td style={td}>{row.price_eur.toFixed(2)}</td>
                    <td style={td}>{row.price_per_100g.toFixed(2)}</td>
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
