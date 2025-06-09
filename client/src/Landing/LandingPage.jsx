import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { auth } from '../firebase';
import { GoogleAuthProvider, signInWithPopup } from 'firebase/auth';
import { useAuth } from '../auth/AuthContext';

const LandingPage = () => {
  const navigate = useNavigate();
  const { currentUser } = useAuth();

  // Redirect if user is already signed in
  useEffect(() => {
    if (currentUser) {
      navigate('/home');
    }
  }, [currentUser, navigate]);

  const handleGoogleSignIn = async () => {
    const provider = new GoogleAuthProvider();
    try {
      const result = await signInWithPopup(auth, provider);
      // Get user info from Firebase
      const user = result.user;
      // Call FastAPI /sign-in endpoint
      await fetch('http://localhost:8000/sign-in?name=' + encodeURIComponent(user.displayName || 'Anonymous') + '&firebase_id=' + encodeURIComponent(user.uid) + '&email=' + encodeURIComponent(user.email || ''), {
        method: 'GET',
      });
      navigate('/home');
    } catch (error) {
      console.error("Error during sign in:", error);
      alert("Failed to sign in with Google. Please try again.");
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>Document AI</h1>
        <p style={styles.description}>
          Intelligent document processing and analysis
        </p>
        <button 
          onClick={handleGoogleSignIn} 
          style={styles.googleButton}
        >
          Sign in with Google
        </button>
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    backgroundColor: '#f5f5f5'
  },
  card: {
    backgroundColor: 'white',
    padding: '40px',
    borderRadius: '8px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    textAlign: 'center',
    maxWidth: '400px',
    width: '100%'
  },
  title: {
    color: '#333',
    marginBottom: '10px'
  },
  description: {
    color: '#666',
    marginBottom: '30px'
  },
  googleButton: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '10px 16px',
    backgroundColor: 'white',
    border: '1px solid #ccc',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: '500',
    width: '100%'
  },
  googleIcon: {
    width: '18px',
    height: '18px',
    marginRight: '10px'
  }
};

export default LandingPage;
