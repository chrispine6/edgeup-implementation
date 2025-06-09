// API configuration for the Document AI Assistant
// This ensures all requests go to the Python FastAPI server on port 8000

export const API_CONFIG = {
  BASE_URL: process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000',
  TIMEOUT: 60000, // 60 seconds
  UPLOAD_TIMEOUT: 300000, // 5 minutes for file uploads
};

// API endpoints
export const API_ENDPOINTS = {
  HEALTH: '/health',
  SIGN_IN: '/sign-in',
  PROCESS_SEQUENCE: '/process-sequence',
  USER_FILES: '/user-files',
  DELETE_FILE: '/delete-file',
  CHAT_QUERY: '/chat-query',
  CHAT_QUERY_JSON: '/chat-query-json',
  USER_DIALOGUES: '/user-dialogues',
};

// Helper function to build full URL
export const buildApiUrl = (endpoint) => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};

export default API_CONFIG;
