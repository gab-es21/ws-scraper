import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BrandSelector = ({ onBrandSelect }) => {
    const [brands, setBrands] = useState([]);

    useEffect(() => {
        axios.get('/api/brands/').then(response => {
            setBrands(response.data);
        });
    }, []);

    return (
        <select onChange={(e) => onBrandSelect(e.target.value)}>
            <option value="">Select Brand</option>
            {brands.map(brand => (
                <option key={brand.id} value={brand.id}>{brand.name}</option>
            ))}
        </select>
    );
};

export default BrandSelector;
