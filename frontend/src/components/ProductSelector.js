import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ProductSelector = ({ brandId, onProductSelect }) => {
    const [products, setProducts] = useState([]);

    useEffect(() => {
        if (brandId) {
            axios.get(`/api/products/?brand=${brandId}`).then(response => {
                setProducts(response.data);
            });
        }
    }, [brandId]);

    return (
        <select onChange={(e) => onProductSelect(e.target.value)}>
            <option value="">Select Product</option>
            {products.map(product => (
                <option key={product.id} value={product.id}>{product.name}</option>
            ))}
        </select>
    );
};

export default ProductSelector;
