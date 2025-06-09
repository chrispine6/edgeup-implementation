import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { AuthProvider } from './AuthContext';
import ProtectedRoute from './ProtectedRoute';
import { TextEncoder, TextDecoder } from 'util';

// Mock Firebase modules to avoid browser API errors in Jest
jest.mock('firebase/auth', () => ({
  getAuth: () => ({}),
  onAuthStateChanged: jest.fn(),
  GoogleAuthProvider: jest.fn(),
  signInWithPopup: jest.fn(),
  signOut: jest.fn(),
}));
jest.mock('firebase/analytics', () => ({
  getAnalytics: () => ({}),
}));

// Mock Firebase AuthContext
jest.mock('./AuthContext', () => {
  const actual = jest.requireActual('./AuthContext');
  return {
    ...actual,
    useAuth: jest.fn(),
    AuthProvider: actual.AuthProvider,
  };
});

const { useAuth } = require('./AuthContext');

function ShowLocation() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname}</div>;
}

describe('Route protection and authentication', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('redirects unauthenticated users from /home to /', async () => {
    useAuth.mockReturnValue({ currentUser: null, loading: false });
    render(
      <MemoryRouter initialEntries={['/home']}>
        <Routes>
          <Route path="/" element={<div>Landing</div>} />
          <Route path="/home" element={<ProtectedRoute><div>Home</div></ProtectedRoute>} />
        </Routes>
      </MemoryRouter>
    );
    // Should not render protected content
    await waitFor(() => {
      expect(screen.queryByText('Home')).not.toBeInTheDocument();
    });
  });

  test('allows authenticated users to access /home', async () => {
    useAuth.mockReturnValue({ currentUser: { displayName: 'Test User', uid: '123' }, loading: false });
    render(
      <MemoryRouter initialEntries={['/home']}>
        <Routes>
          <Route path="/home" element={<ProtectedRoute><div>Home</div></ProtectedRoute>} />
        </Routes>
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText('Home')).toBeInTheDocument();
    });
  });

  test('shows loading state when auth is loading', () => {
    useAuth.mockReturnValue({ currentUser: null, loading: true });
    render(
      <MemoryRouter initialEntries={['/home']}>
        <Routes>
          <Route path="/home" element={<ProtectedRoute><div>Home</div></ProtectedRoute>} />
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});

if (typeof global.TextEncoder === 'undefined') {
  global.TextEncoder = TextEncoder;
}
if (typeof global.TextDecoder === 'undefined') {
  global.TextDecoder = TextDecoder;
}
