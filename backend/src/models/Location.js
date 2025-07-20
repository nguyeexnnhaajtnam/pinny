const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

class Location {
  static async createPin({ userId, name, description, latitude, longitude, imageUrl, isPublic = false }) {
    const query = `
      INSERT INTO location_pins (
        user_id, name, description, location, image_url, is_public, created_at
      )
      VALUES ($1, $2, $3, ST_SetSRID(ST_MakePoint($4, $5), 4326), $6, $7, NOW())
      RETURNING id, name, description, ST_X(location) as longitude, ST_Y(location) as latitude, 
                image_url, is_public, created_at
    `;
    
    const values = [userId, name, description, longitude, latitude, imageUrl, isPublic];
    const result = await pool.query(query, values);
    return result.rows[0];
  }

  static async updatePin(pinId, userId, { name, description, imageUrl, isPublic }) {
    const query = `
      UPDATE location_pins 
      SET name = COALESCE($3, name),
          description = COALESCE($4, description),
          image_url = COALESCE($5, image_url),
          is_public = COALESCE($6, is_public),
          updated_at = NOW()
      WHERE id = $1 AND user_id = $2
      RETURNING id, name, description, ST_X(location) as longitude, ST_Y(location) as latitude,
                image_url, is_public, created_at, updated_at
    `;
    
    const result = await pool.query(query, [pinId, userId, name, description, imageUrl, isPublic]);
    return result.rows[0];
  }

  static async deletePin(pinId, userId) {
    const query = 'DELETE FROM location_pins WHERE id = $1 AND user_id = $2';
    const result = await pool.query(query, [pinId, userId]);
    return result.rowCount > 0;
  }

  static async getPinById(pinId) {
    const query = `
      SELECT lp.*, u.username, u.avatar,
             ST_X(lp.location) as longitude, ST_Y(lp.location) as latitude
      FROM location_pins lp
      JOIN users u ON lp.user_id = u.id
      WHERE lp.id = $1
    `;
    
    const result = await pool.query(query, [pinId]);
    return result.rows[0];
  }

  static async getUserPins(userId) {
    const query = `
      SELECT id, name, description, ST_X(location) as longitude, ST_Y(location) as latitude,
             image_url, is_public, created_at, updated_at
      FROM location_pins
      WHERE user_id = $1
      ORDER BY created_at DESC
    `;
    
    const result = await pool.query(query, [userId]);
    return result.rows;
  }

  static async getSharedPins(userId) {
    const query = `
      SELECT lp.id, lp.name, lp.description, 
             ST_X(lp.location) as longitude, ST_Y(lp.location) as latitude,
             lp.image_url, lp.is_public, lp.created_at, lp.updated_at,
             u.username, u.avatar
      FROM location_pins lp
      JOIN users u ON lp.user_id = u.id
      JOIN connections c ON (c.user1_id = $1 OR c.user2_id = $1)
      WHERE (lp.user_id = c.user1_id OR lp.user_id = c.user2_id)
      AND lp.user_id != $1
      AND c.status = 'accepted'
      AND lp.is_public = true
      ORDER BY lp.created_at DESC
    `;
    
    const result = await pool.query(query, [userId]);
    return result.rows;
  }

  static async searchNearbyPins(latitude, longitude, radius = 10, userId) {
    const query = `
      SELECT lp.id, lp.name, lp.description,
             ST_X(lp.location) as longitude, ST_Y(lp.location) as latitude,
             lp.image_url, lp.is_public, lp.created_at,
             u.username, u.avatar,
             ST_Distance(lp.location, ST_SetSRID(ST_MakePoint($2, $1), 4326)) as distance
      FROM location_pins lp
      JOIN users u ON lp.user_id = u.id
      WHERE ST_DWithin(
        lp.location, 
        ST_SetSRID(ST_MakePoint($2, $1), 4326), 
        $3 * 1000
      )
      AND (lp.is_public = true OR lp.user_id = $4)
      ORDER BY distance
      LIMIT 50
    `;
    
    const result = await pool.query(query, [latitude, longitude, radius, userId]);
    return result.rows;
  }

  static async shareLocation(userId, { latitude, longitude, accuracy, timestamp }) {
    const query = `
      INSERT INTO location_shares (user_id, location, accuracy, timestamp)
      VALUES ($1, ST_SetSRID(ST_MakePoint($3, $2), 4326), $4, $5)
      RETURNING id, ST_X(location) as longitude, ST_Y(location) as latitude, accuracy, timestamp
    `;
    
    const result = await pool.query(query, [userId, latitude, longitude, accuracy, timestamp]);
    return result.rows[0];
  }

  static async getRecentLocations(userId, limit = 10) {
    const query = `
      SELECT id, ST_X(location) as longitude, ST_Y(location) as latitude, 
             accuracy, timestamp
      FROM location_shares
      WHERE user_id = $1
      ORDER BY timestamp DESC
      LIMIT $2
    `;
    
    const result = await pool.query(query, [userId, limit]);
    return result.rows;
  }
}

module.exports = Location; 