import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

function Product() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [quantity, setQuantity] = useState(1);

  useEffect(() => {
    fetch(`http://localhost:3001/api/products/${id}`)
      .then(res => res.json())
      .then(data => setProduct(data));
  }, [id]);

  const addToCart = () => {
    fetch('http://localhost:3001/api/cart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: id, quantity })
    }).then(() => alert('Added to cart!'));
  };

  if (!product) return <div className="container">Loading...</div>;

  return (
    <div className="container">
      <Link to="/" className="back-link">← Back to Products</Link>
      <div className="product-detail">
        <div className="product-emoji-large">{product.emoji}</div>
        <div className="product-info">
          <h1>{product.name}</h1>
          <p className="price-large">${product.price}</p>
          <p className="description">{product.description}</p>
          
          <div className="quantity-selector">
            <label>Quantity:</label>
            <input 
              type="number" 
              min="1" 
              value={quantity} 
              onChange={(e) => setQuantity(parseInt(e.target.value))}
            />
          </div>
          
          <button className="add-to-cart-btn" onClick={addToCart}>
            Add to Cart
          </button>
        </div>
      </div>

      <div className="reviews">
        <h2>Customer Reviews</h2>
        {product.reviews?.map(review => (
          <div key={review.id} className="review">
            <div className="review-header">
              <strong>{review.author}</strong>
              <span className="rating">{'⭐'.repeat(review.rating)}</span>
            </div>
            <p>{review.comment}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Product;
