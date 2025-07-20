const { Pool } = require('pg');
const bcrypt = require('bcryptjs');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

class User {
  static async create({ username, email, password, avatar = null }) {
    const hashedPassword = await bcrypt.hash(password, 12);
    
    const query = `
      INSERT INTO users (username, email, password_hash, avatar, created_at)
      VALUES ($1, $2, $3, $4, NOW())
      RETURNING id, username, email, avatar, created_at
    `;
    
    const values = [username, email, hashedPassword, avatar];
    const result = await pool.query(query, values);
    return result.rows[0];
  }

  static async findByEmail(email) {
    const query = 'SELECT * FROM users WHERE email = $1';
    const result = await pool.query(query, [email]);
    return result.rows[0];
  }

  static async findById(id) {
    const query = 'SELECT id, username, email, avatar, created_at FROM users WHERE id = $1';
    const result = await pool.query(query, [id]);
    return result.rows[0];
  }

  static async updateProfile(id, { username, avatar }) {
    const query = `
      UPDATE users 
      SET username = COALESCE($2, username), 
          avatar = COALESCE($3, avatar),
          updated_at = NOW()
      WHERE id = $1
      RETURNING id, username, email, avatar, created_at, updated_at
    `;
    
    const result = await pool.query(query, [id, username, avatar]);
    return result.rows[0];
  }

  static async getConnections(userId) {
    const query = `
      SELECT u.id, u.username, u.avatar, c.created_at as connected_at
      FROM connections c
      JOIN users u ON (c.user1_id = u.id OR c.user2_id = u.id)
      WHERE (c.user1_id = $1 OR c.user2_id = $1) 
      AND u.id != $1
      AND c.status = 'accepted'
    `;
    
    const result = await pool.query(query, [userId]);
    return result.rows;
  }

  static async searchUsers(searchTerm, currentUserId) {
    const query = `
      SELECT id, username, avatar
      FROM users 
      WHERE username ILIKE $1 
      AND id != $2
      LIMIT 20
    `;
    
    const result = await pool.query(query, [`%${searchTerm}%`, currentUserId]);
    return result.rows;
  }
}

module.exports = User; 