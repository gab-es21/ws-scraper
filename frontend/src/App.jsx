import React, { useState, useEffect } from 'react';
import axios from 'axios';
import PriceChart from './components/PriceChart';
import FilterForm from './components/FilterForm';
import ExtractionStatus from './components/ExtractionStatus';
import './App.css';

const TABS = ['Dashboard', 'Extraction'];

function App() {
  const [tab, setTab] = useState('Extraction');
  const [brands, setBrands] = useState([]);
  const [selectedBrand, setSelectedBrand] = useState('');
  const [products, setProducts] = useState([]);
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [priceHistory, setPriceHistory] = useState([]);

  useEffect(() => {
    axios.get('/api/brands/')
      .then(r => setBrands(r.data))
      .catch(e => console.error('Error fetching brands:', e));
  }, []);

  useEffect(() => {
    if (!selectedBrand) return;
    axios.get(`/api/products/?brand=${selectedBrand}`)
      .then(r => setProducts(r.data))
      .catch(e => console.error('Error fetching products:', e));
  }, [selectedBrand]);

  const handleFetchPriceHistory = async () => {
    try {
      const r = await axios.post('/api/price_history/', { products: selectedProducts });
      setPriceHistory(r.data);
    } catch (e) {
      console.error('Error fetching price history:', e);
    }
  };

  return (
    <div className="App">
      <header style={{ background: '#1e293b', color: '#fff', padding: '0 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
          <h1 style={{ margin: '0', padding: '16px 0', fontSize: '20px' }}>Workout Savings</h1>
          <nav style={{ display: 'flex', gap: '4px' }}>
            {TABS.map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                style={{
                  padding: '8px 16px',
                  background: tab === t ? '#fff' : 'transparent',
                  color: tab === t ? '#1e293b' : '#cbd5e1',
                  border: 'none',
                  borderRadius: '6px 6px 0 0',
                  cursor: 'pointer',
                  fontWeight: tab === t ? 600 : 400,
                  fontSize: '14px',
                }}
              >
                {t}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {tab === 'Dashboard' && (
        <div style={{ padding: '24px' }}>
          <FilterForm
            brands={brands}
            selectedBrand={selectedBrand}
            products={products}
            selectedProducts={selectedProducts}
            handleBrandChange={e => setSelectedBrand(e.target.value)}
            handleProductChange={e =>
              setSelectedProducts(Array.from(e.target.selectedOptions, o => o.value))
            }
            handleFetchPriceHistory={handleFetchPriceHistory}
          />
          <PriceChart priceHistory={priceHistory} />
        </div>
      )}

      {tab === 'Extraction' && <ExtractionStatus />}
    </div>
  );
}

export default App;
