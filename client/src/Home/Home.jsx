import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { auth } from '../firebase';
import { signOut } from 'firebase/auth';
import { useAuth } from '../auth/AuthContext';
import FileWindow from './FileWindow';
import { homeStyles } from '../styles/AppStyles';
import { API_CONFIG, API_ENDPOINTS, buildApiUrl } from '../config/api';

const Home = () => {
  const [messages, setMessages] = useState([
    { 
      text: "Hello! I'm your AI document assistant. 📚\n\nUpload PDF documents using the file window on the left, then ask me questions about their content!", 
      sender: 'bot' 
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [lastDialogueId, setLastDialogueId] = useState(null); // Track the last dialogue for follow-ups
  const navigate = useNavigate();
  const { currentUser } = useAuth();

  const handleResetChat = () => {
    setMessages([
      { 
        text: "Hello! I'm your AI document assistant. 📚\n\nUpload PDF documents using the file window on the left, then ask me questions about their content!", 
        sender: 'bot' 
      }
    ]);
    setSelectedFiles([]);
    setInput('');
    setLastDialogueId(null); // Reset conversation thread
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    // Create user message
    const userMessage = { 
      text: input, 
      sender: 'user',
      selectedFiles: selectedFiles.length > 0 ? selectedFiles.map(file => ({
        name: file.filename || file.originalName,
        id: file.document_id || file.id
      })) : undefined
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    
    try {
      // Prepare document IDs for the query
      const documentIds = selectedFiles.length > 0 
        ? selectedFiles.map(file => file.document_id || file.id).filter(Boolean)
        : [];
      
      console.log('Sending chat query:', {
        query: input.trim(),
        user_id: currentUser?.uid || 'anonymous',
        document_ids: documentIds,
        previous_dialogue_id: lastDialogueId // Include for follow-up questions
      });
      
      // Send query to Python server
      const response = await axios.post(buildApiUrl(API_ENDPOINTS.CHAT_QUERY_JSON), {
        query: input.trim(),
        user_id: currentUser?.uid || 'anonymous',
        document_ids: documentIds.length > 0 ? documentIds : null,
        previous_dialogue_id: lastDialogueId // Include for follow-up questions
      }, {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: API_CONFIG.TIMEOUT
      });
      
      console.log('Chat response received:', response.data);
      
      if (response.data.success) {
        // Format the AI response
        let botText = response.data.response;
        
        // Add reference information if available
        if (response.data.references && response.data.references.length > 0) {
          botText += '\n\n📚 **Sources:**\n';
          response.data.references.forEach((ref, index) => {
            const similarity = (ref.similarity_score * 100).toFixed(1);
            botText += `${index + 1}. ${ref.filename} (Page ${ref.page_num}) - ${similarity}% relevant\n`;
          });
        }
        
        const botMessage = { 
          text: botText,
          sender: 'bot',
          references: response.data.references,
          dialogueId: response.data.dialogue_id
        };
        
        setMessages(prev => [...prev, botMessage]);
        
        // Update the last dialogue ID for follow-up questions
        if (response.data.dialogue_id) {
          setLastDialogueId(response.data.dialogue_id);
          console.log('Updated last dialogue ID for follow-ups:', response.data.dialogue_id);
        }
      } else {
        throw new Error(response.data.error || 'Failed to get response');
      }
      
    } catch (error) {
      console.error('Error processing chat query:', error);
      
      let errorMessage = "Sorry, I encountered an error processing your request.";
      
      if (error.code === 'ECONNABORTED') {
        errorMessage = "Request timed out. Please try again.";
      } else if (error.response?.status === 500) {
        errorMessage = "Server error. Please make sure the Python server is running on port 8000.";
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (!error.response) {
        errorMessage = `Cannot connect to server. Please ensure the Python API is running on ${API_CONFIG.BASE_URL}`;
      }
      
      const errorResponse = { 
        text: errorMessage,
        sender: 'bot',
        isError: true
      };
      
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setInput('');
      setIsLoading(false);
    }
  };
  const handleSignOut = async () => {
    try {
      await signOut(auth);
      navigate('/');
    } catch (error) {
      console.error("Error signing out:", error);
    }
  };

  // Handler for when a file is selected in FileWindow
  const handleFileSelect = (file) => {
    const isAlreadySelected = selectedFiles.some(f => 
      (f.id && f.id === file.id) || 
      (f.document_id && f.document_id === file.document_id) ||
      (f.filename && f.filename === file.filename)
    );
    
    if (!isAlreadySelected) {
      setSelectedFiles(prev => [...prev, file]);
      
      // Update input placeholder
      if (!input.trim()) {
        const fileName = file.filename || file.originalName || 'the selected file';
        setInput(`Tell me about "${fileName}"`);
      }
    }
  };
  
  // Function to remove a file from selectedFiles
  const handleRemoveSelectedFile = (fileToRemove) => {
    setSelectedFiles(prev => 
      prev.filter(file => 
        !(
          (file.id && fileToRemove.id && file.id === fileToRemove.id) || 
          (file.document_id && fileToRemove.document_id && file.document_id === fileToRemove.document_id) ||
          (file.filename && fileToRemove.filename && file.filename === fileToRemove.filename)
        )
      )
    );
  };

  return (
    <div style={homeStyles.container}>
      <div style={homeStyles.header}>
        <div>
          <h1>Document AI Assistant</h1>
          {currentUser && (
            <div style={homeStyles.userInfo}>Welcome, {currentUser.displayName || 'User'}</div>
          )}
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={handleResetChat} style={homeStyles.resetButton}>
            Reset Chat
          </button>
          <button onClick={handleSignOut} style={homeStyles.signOutButton}>
            Sign Out
          </button>
        </div>
      </div>
      
      <div style={homeStyles.mainContent}>
        <FileWindow 
          onFileSelect={handleFileSelect} 
          selectedFiles={selectedFiles}
        />
        
        <div style={homeStyles.chatContainer}>
          {/* Follow-up conversation indicator */}
          {lastDialogueId && (
            <div style={{
              backgroundColor: '#e3f2fd',
              border: '1px solid #2196f3',
              borderRadius: '8px',
              padding: '8px 12px',
              margin: '0 0 16px 0',
              fontSize: '14px',
              color: '#1976d2',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              🔗 <strong>Follow-up conversation active</strong> - Your questions will reference previous context
              <button 
                onClick={() => setLastDialogueId(null)}
                style={{
                  marginLeft: 'auto',
                  background: 'none',
                  border: 'none',
                  color: '#1976d2',
                  cursor: 'pointer',
                  fontSize: '16px',
                  padding: '0 4px'
                }}
                title="Start new conversation thread"
              >
                ×
              </button>
            </div>
          )}
          
          <div style={homeStyles.messages}>
            {messages.map((message, index) => (
              <div 
                key={index}
                style={{
                  ...homeStyles.message,
                  ...(message.sender === 'user' ? homeStyles.userMessage : homeStyles.botMessage),
                  ...(message.isError ? homeStyles.errorMessage : {})
                }}
              >
                <div style={{ whiteSpace: 'pre-wrap' }}>{message.text}</div>
                
                {/* Display references for chat responses */}
                {message.references && message.references.length > 0 && (
                  <div style={homeStyles.sourcesContainer}>
                    <div style={homeStyles.sourcesHeader}>📚 Sources:</div>
                    {message.references.map((ref, refIndex) => (
                      <div key={refIndex} style={homeStyles.sourceItem}>
                        <div style={homeStyles.sourceName}>
                          {ref.filename} (Page {ref.page_num})
                          <span style={homeStyles.similarityScore}>
                            {ref.similarity_score && ` - ${(ref.similarity_score * 100).toFixed(1)}% match`}
                          </span>
                        </div>
                        {ref.text && (
                          <div style={homeStyles.sourcePreview}>
                            "{ref.text.substring(0, 150)}..."
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Display selected files info */}
                {message.selectedFiles && message.selectedFiles.map((file, fileIndex) => (
                  <div key={fileIndex} style={homeStyles.attachmentInfo}>
                    <div style={homeStyles.attachmentName}>📁 {file.name}</div>
                  </div>
                ))}
              </div>
            ))}
            {isLoading && (
              <div style={{...homeStyles.message, ...homeStyles.botMessage, ...homeStyles.loadingMessage}}>
                Processing your request...
              </div>
            )}
          </div>
          
          {/* Selected files indicator */}
          {selectedFiles.length > 0 && (
            <div style={homeStyles.selectedFilesContainer}>
              <div style={{ marginBottom: '8px', fontSize: '14px', color: '#666' }}>
                Selected files ({selectedFiles.length}):
              </div>
              {selectedFiles.map((file, index) => (
                <div key={index} style={homeStyles.selectedFileIndicator}>
                  <div style={homeStyles.selectedFileName}>
                    📄 {file.filename || file.originalName}
                  </div>
                  <button 
                    onClick={() => handleRemoveSelectedFile(file)}
                    style={homeStyles.removeSelectedFileButton}
                    title="Remove from selection"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
          
          <form onSubmit={handleSubmit} style={homeStyles.inputForm}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                lastDialogueId 
                  ? "Ask a follow-up question..." 
                  : selectedFiles.length > 0 
                    ? `Ask about your ${selectedFiles.length} selected file${selectedFiles.length > 1 ? 's' : ''}...` 
                    : "Upload files and ask questions about them..."
              }
              style={homeStyles.input}
              disabled={isLoading}
            />
            <button 
              type="submit" 
              style={homeStyles.sendButton}
              disabled={isLoading || !input.trim()}
            >
              {isLoading ? "Processing..." : "Send"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Home;
