import Database from 'better-sqlite3';

const db = new Database('ecommerce.db');

// Initialize database
db.exec(`
  CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    emoji TEXT NOT NULL,
    price REAL NOT NULL,
    description TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    author TEXT NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id)
  );

  CREATE TABLE IF NOT EXISTS cart_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id)
  );
`);

// Seed products if empty
const count = db.prepare('SELECT COUNT(*) as count FROM products').get();
if (count.count === 0) {
  const products = [
    { name: 'Laptop Pro', emoji: '💻', price: 1299.99, description: 'High-performance laptop with 16GB RAM and 512GB SSD' },
    { name: 'Smartphone X', emoji: '📱', price: 899.99, description: 'Latest smartphone with 5G connectivity and amazing camera' },
    { name: 'Wireless Headphones', emoji: '🎧', price: 249.99, description: 'Noise-cancelling headphones with 30-hour battery life' },
    { name: 'Smart Watch', emoji: '⌚', price: 399.99, description: 'Fitness tracker with heart rate monitor and GPS' },
    { name: 'Tablet', emoji: '📱', price: 599.99, description: '10-inch display perfect for work and entertainment' },
    { name: 'Camera', emoji: '📷', price: 1499.99, description: 'Professional DSLR camera with 24MP sensor' },
    { name: 'Gaming Console', emoji: '🎮', price: 499.99, description: 'Next-gen gaming console with 4K support' },
    { name: 'Bluetooth Speaker', emoji: '🔊', price: 129.99, description: 'Portable speaker with rich bass and 12-hour battery' },
    { name: 'Keyboard', emoji: '⌨️', price: 149.99, description: 'Mechanical keyboard with RGB lighting' },
    { name: 'Mouse', emoji: '🖱️', price: 79.99, description: 'Ergonomic wireless mouse with precision tracking' },
    { name: 'Monitor', emoji: '🖥️', price: 449.99, description: '27-inch 4K monitor with HDR support' },
    { name: 'External SSD', emoji: '💾', price: 199.99, description: '1TB portable SSD with fast transfer speeds' },
    { name: 'Webcam', emoji: '📹', price: 99.99, description: '1080p webcam with auto-focus and noise reduction' },
    { name: 'Microphone', emoji: '🎤', price: 179.99, description: 'Studio-quality USB microphone for streaming' },
    { name: 'Router', emoji: '📡', price: 159.99, description: 'WiFi 6 router with gigabit speeds' },
    { name: 'Power Bank', emoji: '🔋', price: 49.99, description: '20000mAh portable charger with fast charging' },
    { name: 'USB Hub', emoji: '🔌', price: 39.99, description: '7-port USB hub with individual switches' },
    { name: 'Desk Lamp', emoji: '💡', price: 59.99, description: 'LED desk lamp with adjustable brightness' },
    { name: 'Backpack', emoji: '🎒', price: 89.99, description: 'Laptop backpack with USB charging port' },
    { name: 'Phone Case', emoji: '📦', price: 29.99, description: 'Protective case with shock absorption' }
  ];

  const insert = db.prepare('INSERT INTO products (name, emoji, price, description) VALUES (?, ?, ?, ?)');
  products.forEach(p => insert.run(p.name, p.emoji, p.price, p.description));

  // Add sample reviews
  const reviewInsert = db.prepare('INSERT INTO reviews (product_id, author, rating, comment) VALUES (?, ?, ?, ?)');
  for (let i = 1; i <= 20; i++) {
    reviewInsert.run(i, 'John Doe', 5, 'Excellent product! Highly recommend.');
    reviewInsert.run(i, 'Jane Smith', 4, 'Good quality, fast shipping.');
  }
}

export default db;
