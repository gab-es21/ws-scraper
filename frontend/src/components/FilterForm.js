import React from 'react';

function FilterForm({
  brands,
  selectedBrand,
  products,
  selectedProducts,
  handleBrandChange,
  handleProductChange,
  handleFetchPriceHistory,
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxWidth: '480px' }}>
      <div>
        <label style={{ display: 'block', marginBottom: '4px', fontWeight: 600 }}>Brand</label>
        <select value={selectedBrand} onChange={handleBrandChange} style={selectStyle}>
          <option value="">-- Select brand --</option>
          {brands.map(b => (
            <option key={b.id} value={b.id}>{b.name}</option>
          ))}
        </select>
      </div>

      {products.length > 0 && (
        <div>
          <label style={{ display: 'block', marginBottom: '4px', fontWeight: 600 }}>
            Products <span style={{ fontWeight: 400, color: '#666' }}>(hold Ctrl to select multiple)</span>
          </label>
          <select multiple value={selectedProducts} onChange={handleProductChange} style={{ ...selectStyle, height: '140px' }}>
            {products.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>
      )}

      <button
        onClick={handleFetchPriceHistory}
        disabled={selectedProducts.length === 0}
        style={{
          padding: '8px 20px',
          background: selectedProducts.length === 0 ? '#ccc' : '#2563eb',
          color: '#fff',
          border: 'none',
          borderRadius: '6px',
          cursor: selectedProducts.length === 0 ? 'not-allowed' : 'pointer',
          fontWeight: 600,
          alignSelf: 'flex-start',
        }}
      >
        Show Price History
      </button>
    </div>
  );
}

const selectStyle = {
  width: '100%',
  padding: '8px',
  borderRadius: '6px',
  border: '1px solid #cbd5e1',
  fontSize: '14px',
};

export default FilterForm;
