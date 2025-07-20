const express = require('express');
const jwt = require('jsonwebtoken');
const Joi = require('joi');
const Location = require('../models/Location');

const router = express.Router();

// Middleware to verify JWT token
const authenticateToken = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(403).json({ error: 'Invalid token' });
  }
};

// Validation schemas
const shareLocationSchema = Joi.object({
  latitude: Joi.number().min(-90).max(90).required(),
  longitude: Joi.number().min(-180).max(180).required(),
  accuracy: Joi.number().min(0).optional(),
  timestamp: Joi.date().optional()
});

// Share current location
router.post('/share', authenticateToken, async (req, res) => {
  try {
    const { error, value } = shareLocationSchema.validate(req.body);
    if (error) {
      return res.status(400).json({ error: error.details[0].message });
    }

    const { latitude, longitude, accuracy, timestamp } = value;
    const locationData = {
      latitude,
      longitude,
      accuracy: accuracy || null,
      timestamp: timestamp || new Date()
    };

    const location = await Location.shareLocation(req.user.userId, locationData);

    res.json({
      message: 'Location shared successfully',
      location
    });
  } catch (error) {
    console.error('Share location error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get recent locations for user
router.get('/recent', authenticateToken, async (req, res) => {
  try {
    const { limit = 10 } = req.query;
    const locations = await Location.getRecentLocations(req.user.userId, parseInt(limit));
    
    res.json({ locations });
  } catch (error) {
    console.error('Get recent locations error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get shared locations from connections
router.get('/shared', authenticateToken, async (req, res) => {
  try {
    const { limit = 20 } = req.query;
    const sharedLocations = await getSharedLocations(req.user.userId, parseInt(limit));
    
    res.json({ locations: sharedLocations });
  } catch (error) {
    console.error('Get shared locations error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Helper function to get shared locations from connections
async function getSharedLocations(userId, limit) {
  const { Pool } = require('pg');
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
  });

  const query = `
    SELECT ls.id, ST_X(ls.location) as longitude, ST_Y(ls.location) as latitude,
           ls.accuracy, ls.timestamp, u.username, u.avatar
    FROM location_shares ls
    JOIN users u ON ls.user_id = u.id
    JOIN connections c ON (c.user1_id = $1 OR c.user2_id = $1)
    WHERE (ls.user_id = c.user1_id OR ls.user_id = c.user2_id)
    AND ls.user_id != $1
    AND c.status = 'accepted'
    ORDER BY ls.timestamp DESC
    LIMIT $2
  `;
  
  const result = await pool.query(query, [userId, limit]);
  return result.rows;
}

module.exports = router; 