import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getAnalytics } from "firebase/analytics";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCJNkeX6UxFNuMTgeAx_ioz4wpbH9czvUY",
  authDomain: "document-ai-chris.firebaseapp.com",
  projectId: "document-ai-chris",
  storageBucket: "document-ai-chris.firebasestorage.app",
  messagingSenderId: "1063619720153",
  appId: "1:1063619720153:web:db2a12bedb63b36f6f9fc8",
  measurementId: "G-CQ7841GWNY"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication
const auth = getAuth(app);

// Initialize Analytics
const analytics = getAnalytics(app);

export { auth, analytics };
