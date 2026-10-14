import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

function Home() {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    fetch('http://localhost:3001/api/products')
      .then(res => res.json())
      .then(data => setProducts(data));
  }, []);

  return (
    <div className="container">
      <h1>Products</h1>
      <div className="product-grid">
        {products.map(product => (
          <Link to={`/product/${product.id}`} key={product.id} className="product-card">
            <div className="product-emoji">{product.emoji}</div>
            <h3>{product.name}</h3>
            <p className="price">${product.price}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default Home;
