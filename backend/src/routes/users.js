const express = require('express');
const jwt = require('jsonwebtoken');
const Joi = require('joi');
const User = require('../models/User');
const multer = require('multer');
const path = require('path');

const router = express.Router();

// Multer configuration for avatar uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/avatars/');
  },
  filename: (req, file, cb) => {
    cb(null, Date.now() + path.extname(file.originalname));
  }
});

const upload = multer({
  storage: storage,
  limits: { fileSize: 2 * 1024 * 1024 }, // 2MB limit
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) {
      cb(null, true);
    } else {
      cb(new Error('Only image files are allowed'));
    }
  }
});

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
const updateProfileSchema = Joi.object({
  username: Joi.string().min(3).max(30).optional(),
});

const searchUsersSchema = Joi.object({
  q: Joi.string().min(1).max(50).required()
});

// Get user profile
router.get('/profile', authenticateToken, async (req, res) => {
  try {
    const user = await User.findById(req.user.userId);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json({ user });
  } catch (error) {
    console.error('Get profile error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Update user profile
router.put('/profile', authenticateToken, upload.single('avatar'), async (req, res) => {
  try {
    const { error, value } = updateProfileSchema.validate(req.body);
    if (error) {
      return res.status(400).json({ error: error.details[0].message });
    }

    const { username } = value;
    const avatar = req.file ? `/uploads/avatars/${req.file.filename}` : undefined;

    const user = await User.updateProfile(req.user.userId, { username, avatar });
    
    res.json({
      message: 'Profile updated successfully',
      user
    });
  } catch (error) {
    console.error('Update profile error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Search users
router.get('/search', authenticateToken, async (req, res) => {
  try {
    const { error, value } = searchUsersSchema.validate(req.query);
    if (error) {
      return res.status(400).json({ error: error.details[0].message });
    }

    const users = await User.searchUsers(value.q, req.user.userId);
    res.json({ users });
  } catch (error) {
    console.error('Search users error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get user connections
router.get('/connections', authenticateToken, async (req, res) => {
  try {
    const connections = await User.getConnections(req.user.userId);
    res.json({ connections });
  } catch (error) {
    console.error('Get connections error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Send connection request
router.post('/connections/:userId', authenticateToken, async (req, res) => {
  try {
    const { userId } = req.params;
    
    if (parseInt(userId) === req.user.userId) {
      return res.status(400).json({ error: 'Cannot connect to yourself' });
    }

    // Check if user exists
    const targetUser = await User.findById(userId);
    if (!targetUser) {
      return res.status(404).json({ error: 'User not found' });
    }

    // Check if connection already exists
    const existingConnection = await checkExistingConnection(req.user.userId, userId);
    if (existingConnection) {
      return res.status(400).json({ error: 'Connection already exists' });
    }

    // Create connection request
    await createConnectionRequest(req.user.userId, userId);

    res.json({ message: 'Connection request sent successfully' });
  } catch (error) {
    console.error('Send connection request error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Accept/Reject connection request
router.put('/connections/:connectionId', authenticateToken, async (req, res) => {
  try {
    const { connectionId } = req.params;
    const { action } = req.body; // 'accept' or 'reject'

    if (!['accept', 'reject'].includes(action)) {
      return res.status(400).json({ error: 'Invalid action' });
    }

    const updated = await updateConnectionStatus(connectionId, req.user.userId, action);
    
    if (!updated) {
      return res.status(404).json({ error: 'Connection request not found' });
    }

    res.json({ 
      message: `Connection request ${action}ed successfully` 
    });
  } catch (error) {
    console.error('Update connection error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get pending connection requests
router.get('/connections/pending', authenticateToken, async (req, res) => {
  try {
    const pendingRequests = await getPendingConnectionRequests(req.user.userId);
    res.json({ pendingRequests });
  } catch (error) {
    console.error('Get pending requests error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Helper functions for connections
async function checkExistingConnection(user1Id, user2Id) {
  const { Pool } = require('pg');
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
  });

  const query = `
    SELECT * FROM connections 
    WHERE (user1_id = $1 AND user2_id = $2) 
    OR (user1_id = $2 AND user2_id = $1)
  `;
  
  const result = await pool.query(query, [user1Id, user2Id]);
  return result.rows[0];
}

async function createConnectionRequest(fromUserId, toUserId) {
  const { Pool } = require('pg');
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
  });

  const query = `
    INSERT INTO connections (user1_id, user2_id, status, created_at)
    VALUES ($1, $2, 'pending', NOW())
  `;
  
  await pool.query(query, [fromUserId, toUserId]);
}

async function updateConnectionStatus(connectionId, userId, action) {
  const { Pool } = require('pg');
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
  });

  const status = action === 'accept' ? 'accepted' : 'rejected';
  const query = `
    UPDATE connections 
    SET status = $1, updated_at = NOW()
    WHERE id = $2 AND user2_id = $3
  `;
  
  const result = await pool.query(query, [status, connectionId, userId]);
  return result.rowCount > 0;
}

async function getPendingConnectionRequests(userId) {
  const { Pool } = require('pg');
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
  });

  const query = `
    SELECT c.id, c.created_at, u.id as user_id, u.username, u.avatar
    FROM connections c
    JOIN users u ON c.user1_id = u.id
    WHERE c.user2_id = $1 AND c.status = 'pending'
    ORDER BY c.created_at DESC
  `;
  
  const result = await pool.query(query, [userId]);
  return result.rows;
}

module.exports = router; 