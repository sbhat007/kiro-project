import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

function Cart() {
  const [cartItems, setCartItems] = useState([]);

  const loadCart = () => {
    fetch('http://localhost:3001/api/cart')
      .then(res => res.json())
      .then(data => setCartItems(data));
  };

  useEffect(() => {
    loadCart();
  }, []);

  const updateQuantity = (cartId, quantity) => {
    if (!quantity || quantity < 1 || isNaN(quantity)) return;
    fetch(`http://localhost:3001/api/cart/${cartId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quantity })
    })
      .then(res => res.json())
      .then(() => loadCart())
      .catch(err => console.error('Update failed:', err));
  };

  const removeItem = (cartId) => {
    fetch(`http://localhost:3001/api/cart/${cartId}`, {
      method: 'DELETE'
    })
      .then(res => res.json())
      .then(() => loadCart())
      .catch(err => console.error('Delete failed:', err));
  };

  const total = cartItems.reduce((sum, item) => sum + item.price * item.quantity, 0);

  return (
    <div className="container">
      <h1>Shopping Cart</h1>
      
      {cartItems.length === 0 ? (
        <div className="empty-cart">
          <p>Your cart is empty</p>
          <Link to="/" className="continue-shopping">Continue Shopping</Link>
        </div>
      ) : (
        <>
          <div className="cart-items">
            {cartItems.map(item => (
              <div key={item.cart_id} className="cart-item">
                <div className="cart-item-emoji">{item.emoji}</div>
                <div className="cart-item-info">
                  <h3>{item.name}</h3>
                  <p className="price">${item.price}</p>
                </div>
                <div className="cart-item-actions">
                  <input 
                    type="number" 
                    min="1" 
                    value={item.quantity}
                    onChange={(e) => {
                      const val = parseInt(e.target.value);
                      if (val > 0) {
                        updateQuantity(item.cart_id, val);
                      }
                    }}
                  />
                  <button onClick={() => removeItem(item.cart_id)} className="remove-btn">
                    Remove
                  </button>
                </div>
                <div className="cart-item-total">
                  ${(item.price * item.quantity).toFixed(2)}
                </div>
              </div>
            ))}
          </div>
          
          <div className="cart-summary">
            <h2>Total: ${total.toFixed(2)}</h2>
            <button className="checkout-btn">Proceed to Checkout</button>
          </div>
        </>
      )}
    </div>
  );
}

export default Cart;
