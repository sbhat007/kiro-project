import express from 'express';
import cors from 'cors';
import db from './database.js';

const app = express();
app.use(cors());
app.use(express.json());

// Get all products
app.get('/api/products', (req, res) => {
  const products = db.prepare('SELECT * FROM products').all();
  res.json(products);
});

// Get single product with reviews
app.get('/api/products/:id', (req, res) => {
  const product = db.prepare('SELECT * FROM products WHERE id = ?').get(req.params.id);
  if (!product) return res.status(404).json({ error: 'Product not found' });
  
  const reviews = db.prepare('SELECT * FROM reviews WHERE product_id = ?').all(req.params.id);
  res.json({ ...product, reviews });
});

// Get cart items
app.get('/api/cart', (req, res) => {
  const items = db.prepare(`
    SELECT c.id as cart_id, c.quantity, p.id, p.name, p.emoji, p.price, p.description
    FROM cart_items c 
    JOIN products p ON c.product_id = p.id
  `).all();
  res.json(items);
});

// Add to cart
app.post('/api/cart', (req, res) => {
  const { product_id, quantity } = req.body;
  const existing = db.prepare('SELECT * FROM cart_items WHERE product_id = ?').get(product_id);
  
  if (existing) {
    db.prepare('UPDATE cart_items SET quantity = quantity + ? WHERE product_id = ?').run(quantity, product_id);
  } else {
    db.prepare('INSERT INTO cart_items (product_id, quantity) VALUES (?, ?)').run(product_id, quantity);
  }
  res.json({ success: true });
});

// Update cart item quantity
app.put('/api/cart/:id', (req, res) => {
  const { quantity } = req.body;
  console.log(`Updating cart item ${req.params.id} to quantity ${quantity}`);
  const result = db.prepare('UPDATE cart_items SET quantity = ? WHERE id = ?').run(quantity, req.params.id);
  console.log(`Updated ${result.changes} rows`);
  res.json({ success: true, changes: result.changes });
});

// Delete cart item
app.delete('/api/cart/:id', (req, res) => {
  console.log(`Deleting cart item ${req.params.id}`);
  const result = db.prepare('DELETE FROM cart_items WHERE id = ?').run(req.params.id);
  console.log(`Deleted ${result.changes} rows`);
  res.json({ success: true, changes: result.changes });
});

const PORT = 3001;
app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`));
