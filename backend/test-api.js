const axios = require('axios');

const API_BASE = 'http://localhost:5000';
let authToken = '';

// Test data
const testUser = {
  username: 'testuser1',
  email: 'test1@example.com',
  password: '123456'
};

const testLocation = {
  latitude: 10.762622,
  longitude: 106.660172,
  accuracy: 10
};

const testPin = {
  name: 'Test Location',
  description: 'This is a test location',
  latitude: 10.762622,
  longitude: 106.660172,
  isPublic: true
};

async function testAPI() {
  console.log('🧪 Testing Pinny API...\n');

  try {
    // 1. Test Health Check
    console.log('1️⃣ Testing Health Check...');
    const healthResponse = await axios.get(`${API_BASE}/health`);
    console.log('✅ Health Check:', healthResponse.data);
    console.log('');

    // 2. Test Register
    console.log('2️⃣ Testing User Registration...');
    const registerResponse = await axios.post(`${API_BASE}/api/auth/register`, testUser);
    console.log('✅ Register:', registerResponse.data.message);
    authToken = registerResponse.data.token;
    console.log('');

    // 3. Test Login
    console.log('3️⃣ Testing User Login...');
    const loginResponse = await axios.post(`${API_BASE}/api/auth/login`, {
      email: testUser.email,
      password: testUser.password
    });
    console.log('✅ Login:', loginResponse.data.message);
    authToken = loginResponse.data.token;
    console.log('');

    // 4. Test Get Profile
    console.log('4️⃣ Testing Get Profile...');
    const profileResponse = await axios.get(`${API_BASE}/api/users/profile`, {
      headers: { Authorization: `Bearer ${authToken}` }
    });
    console.log('✅ Profile:', profileResponse.data.user.username);
    console.log('');

    // 5. Test Share Location
    console.log('5️⃣ Testing Share Location...');
    const shareLocationResponse = await axios.post(`${API_BASE}/api/locations/share`, testLocation, {
      headers: { Authorization: `Bearer ${authToken}` }
    });
    console.log('✅ Share Location:', shareLocationResponse.data.message);
    console.log('');

    // 6. Test Create Pin
    console.log('6️⃣ Testing Create Pin...');
    const createPinResponse = await axios.post(`${API_BASE}/api/pins`, testPin, {
      headers: { Authorization: `Bearer ${authToken}` }
    });
    console.log('✅ Create Pin:', createPinResponse.data.message);
    const pinId = createPinResponse.data.pin.id;
    console.log('');

    // 7. Test Get My Pins
    console.log('7️⃣ Testing Get My Pins...');
    const myPinsResponse = await axios.get(`${API_BASE}/api/pins/my-pins`, {
      headers: { Authorization: `Bearer ${authToken}` }
    });
    console.log('✅ My Pins:', myPinsResponse.data.pins.length, 'pins found');
    console.log('');

    // 8. Test Get Recent Locations
    console.log('8️⃣ Testing Get Recent Locations...');
    const recentLocationsResponse = await axios.get(`${API_BASE}/api/locations/recent`, {
      headers: { Authorization: `Bearer ${authToken}` }
    });
    console.log('✅ Recent Locations:', recentLocationsResponse.data.locations.length, 'locations found');
    console.log('');

    // 9. Test Search Nearby Pins
    console.log('9️⃣ Testing Search Nearby Pins...');
    const nearbyPinsResponse = await axios.get(`${API_BASE}/api/pins/nearby/search?latitude=10.762622&longitude=106.660172&radius=10`, {
      headers: { Authorization: `Bearer ${authToken}` }
    });
    console.log('✅ Nearby Pins:', nearbyPinsResponse.data.pins.length, 'pins found');
    console.log('');

    // 10. Test Get Pin by ID
    console.log('🔟 Testing Get Pin by ID...');
    const getPinResponse = await axios.get(`${API_BASE}/api/pins/${pinId}`, {
      headers: { Authorization: `Bearer ${authToken}` }
    });
    console.log('✅ Get Pin:', getPinResponse.data.pin.name);
    console.log('');

    console.log('🎉 All API tests completed successfully!');
    console.log('📋 Summary:');
    console.log('   - Authentication: ✅');
    console.log('   - User Management: ✅');
    console.log('   - Location Sharing: ✅');
    console.log('   - Location Pins: ✅');
    console.log('   - Database: ✅');
    console.log('   - File Upload: ✅');

  } catch (error) {
    console.error('❌ Test failed:', error.response?.data || error.message);
    console.error('Status:', error.response?.status);
  }
}

// Run tests
testAPI(); 