const express = require('express');
const jwt = require('jsonwebtoken');
const Joi = require('joi');
const Location = require('../models/Location');
const multer = require('multer');
const path = require('path');

const router = express.Router();

// Multer configuration for image uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    cb(null, Date.now() + path.extname(file.originalname));
  }
});

const upload = multer({
  storage: storage,
  limits: { fileSize: 5 * 1024 * 1024 }, // 5MB limit
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
const createPinSchema = Joi.object({
  name: Joi.string().min(1).max(100).required(),
  description: Joi.string().max(500).optional(),
  latitude: Joi.number().min(-90).max(90).required(),
  longitude: Joi.number().min(-180).max(180).required(),
  isPublic: Joi.boolean().default(false)
});

const updatePinSchema = Joi.object({
  name: Joi.string().min(1).max(100).optional(),
  description: Joi.string().max(500).optional(),
  isPublic: Joi.boolean().optional()
});

// Create a new location pin
router.post('/', authenticateToken, upload.single('image'), async (req, res) => {
  try {
    const { error, value } = createPinSchema.validate(req.body);
    if (error) {
      return res.status(400).json({ error: error.details[0].message });
    }

    const { name, description, latitude, longitude, isPublic } = value;
    const imageUrl = req.file ? `/uploads/${req.file.filename}` : null;

    const pin = await Location.createPin({
      userId: req.user.userId,
      name,
      description,
      latitude,
      longitude,
      imageUrl,
      isPublic
    });

    res.status(201).json({
      message: 'Location pin created successfully',
      pin
    });
  } catch (error) {
    console.error('Create pin error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get user's pins
router.get('/my-pins', authenticateToken, async (req, res) => {
  try {
    const pins = await Location.getUserPins(req.user.userId);
    res.json({ pins });
  } catch (error) {
    console.error('Get user pins error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get shared pins from connections
router.get('/shared', authenticateToken, async (req, res) => {
  try {
    const pins = await Location.getSharedPins(req.user.userId);
    res.json({ pins });
  } catch (error) {
    console.error('Get shared pins error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get pin by ID
router.get('/:pinId', authenticateToken, async (req, res) => {
  try {
    const pin = await Location.getPinById(req.params.pinId);
    if (!pin) {
      return res.status(404).json({ error: 'Pin not found' });
    }

    // Check if user can access this pin
    if (!pin.is_public && pin.user_id !== req.user.userId) {
      return res.status(403).json({ error: 'Access denied' });
    }

    res.json({ pin });
  } catch (error) {
    console.error('Get pin error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Update pin
router.put('/:pinId', authenticateToken, upload.single('image'), async (req, res) => {
  try {
    const { error, value } = updatePinSchema.validate(req.body);
    if (error) {
      return res.status(400).json({ error: error.details[0].message });
    }

    const { name, description, isPublic } = value;
    const imageUrl = req.file ? `/uploads/${req.file.filename}` : undefined;

    const pin = await Location.updatePin(req.params.pinId, req.user.userId, {
      name,
      description,
      imageUrl,
      isPublic
    });

    if (!pin) {
      return res.status(404).json({ error: 'Pin not found or access denied' });
    }

    res.json({
      message: 'Pin updated successfully',
      pin
    });
  } catch (error) {
    console.error('Update pin error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Delete pin
router.delete('/:pinId', authenticateToken, async (req, res) => {
  try {
    const deleted = await Location.deletePin(req.params.pinId, req.user.userId);
    
    if (!deleted) {
      return res.status(404).json({ error: 'Pin not found or access denied' });
    }

    res.json({ message: 'Pin deleted successfully' });
  } catch (error) {
    console.error('Delete pin error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Search nearby pins
router.get('/nearby/search', authenticateToken, async (req, res) => {
  try {
    const { latitude, longitude, radius = 10 } = req.query;
    
    if (!latitude || !longitude) {
      return res.status(400).json({ error: 'Latitude and longitude are required' });
    }

    const pins = await Location.searchNearbyPins(
      parseFloat(latitude),
      parseFloat(longitude),
      parseFloat(radius),
      req.user.userId
    );

    res.json({ pins });
  } catch (error) {
    console.error('Search nearby pins error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router; 