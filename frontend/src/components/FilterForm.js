import React, { useState, useEffect } from 'react';
import axios from 'axios';
import PriceChart from './components/PriceChart';
import FilterForm from './components/FilterForm';
import './App.css';

function App() {
  const [brands, setBrands] = useState([]);
  const [selectedBrand, setSelectedBrand] = useState('');
  const [products, setProducts] = useState([]);
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [priceHistory, setPriceHistory] = useState([]);

  useEffect(() => {
    async function fetchBrands() {
      try {
        const response = await axios.get('/api/brands/');
        setBrands(response.data);
      } catch (error) {
        console.error('Error fetching brands:', error);
      }
    }

    fetchBrands();
  }, []);

  useEffect(() => {
    async function fetchProducts() {
      if (selectedBrand) {
        try {
          const response = await axios.get(`/api/products?brand=${selectedBrand}`);
          setProducts(response.data);
        } catch (error) {
          console.error('Error fetching products:', error);
        }
      }
    }

    fetchProducts();
  }, [selectedBrand]);

  const handleBrandChange = (event) => {
    setSelectedBrand(event.target.value);
  };

  const handleProductChange = (event) => {
    const selectedOptions = Array.from(event.target.selectedOptions, option => option.value);
    setSelectedProducts(selectedOptions);
  };

  const handleFetchPriceHistory = async () => {
    try {
      const response = await axios.post('/api/price_history/', {
        products: selectedProducts
      });
      setPriceHistory(response.data);
    } catch (error) {
      console.error('Error fetching price history:', error);
    }
  };

  return (
    <div className="App">
      <h1>Workout Savings</h1>
      <FilterForm
        brands={brands}
        selectedBrand={selectedBrand}
        products={products}
        selectedProducts={selectedProducts}
        handleBrandChange={handleBrandChange}
        handleProductChange={handleProductChange}
        handleFetchPriceHistory={handleFetchPriceHistory}
      />
      <PriceChart priceHistory={priceHistory} />
    </div>
  );
}

export default App;
