import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useAuth } from '../auth/AuthContext';
import ProcessingModal from './ProcessingModal';
import { fileWindowStyles } from '../styles/AppStyles';
import { API_CONFIG, API_ENDPOINTS, buildApiUrl } from '../config/api';

const FileWindow = ({ onFileSelect, selectedFiles = [] }) => {
  const [files, setFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const { currentUser } = useAuth();
  const [serverStatus, setServerStatus] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [currentFile, setCurrentFile] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    checkServerHealth();
    if (currentUser) fetchUserFiles();
  }, [currentUser]);

  const checkServerHealth = async () => {
    try {
      await axios.get(buildApiUrl(API_ENDPOINTS.HEALTH));
      setServerStatus('online');
    } catch {
      setServerStatus('offline');
      setError(`Python server appears to be offline. Please check if the server is running on ${API_CONFIG.BASE_URL}.`);
    }
  };

  const fetchUserFiles = async () => {
    if (!currentUser) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await axios.get(
        `${buildApiUrl(API_ENDPOINTS.USER_FILES)}?user_id=${encodeURIComponent(currentUser.uid)}`
      );
      
      if (response.data && response.data.success) {
        let files = response.data.files || [];
        
        // Validate and clean up file data
        files = files.filter(file => {
          return file && (file.filename || file.originalName);
        }).map(file => {
          return {
            ...file,
            id: file.id || file.document_id || file._id,
            filename: file.filename || file.originalName || 'Unknown File',
            originalName: file.originalName || file.filename || 'Unknown File',
            uploadedAt: file.uploadedAt || new Date().toISOString()
          };
        });
        
        setFiles(files);
      } else {
        setError('Failed to fetch files from server.');
        setFiles([]);
      }
    } catch (error) {
      console.error('Error fetching files:', error);
      setError(`Failed to fetch files: ${error.message || 'Network error'}`);
      setFiles([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteFile = async (file) => {
    if (!currentUser || !window.confirm(`Are you sure you want to delete "${getDisplayName(file)}"?`)) return;
    
    try {
      setError(null);
      const documentId = file.document_id || file.id;
      
      if (!documentId) {
        setError('Cannot delete file: missing document ID');
        return;
      }
      
      const deleteUrl = `${buildApiUrl(API_ENDPOINTS.DELETE_FILE)}?document_id=${encodeURIComponent(documentId)}&user_id=${encodeURIComponent(currentUser.uid)}`;
      
      const response = await axios.delete(deleteUrl);
      
      if (response.data && response.data.success) {
        // Remove the file from local state
        setFiles(files.filter(f => {
          const currentDocId = f.document_id || f.id;
          return currentDocId !== documentId;
        }));
        
        console.log(`Successfully deleted file: ${getDisplayName(file)}`);
      } else {
        setError(response.data?.message || 'Failed to delete file. Please try again.');
      }
    } catch (error) {
      console.error('Delete error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to delete file. Please try again.';
      setError(errorMessage);
    }
  };

  const handleUploadClick = () => fileInputRef.current.click();

  const handleFileUpload = async (e) => {
    if (!currentUser || !e.target.files.length) return;
    
    setIsUploading(true);
    setError(null);
    
    const uploadedFiles = [];
    const failedFiles = [];
    
    for (const file of Array.from(e.target.files)) {
      // Validate file type and size
      const fileName = file.name.toLowerCase();
      const supportedPdf = fileName.endsWith('.pdf');
      const supportedImage = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        .some(ext => fileName.endsWith(ext));
      
      if (!supportedPdf && !supportedImage) {
        failedFiles.push(`${file.name}: Only PDF and image files are supported (PDF, JPG, JPEG, PNG, GIF, BMP, TIFF, WEBP)`);
        continue;
      }
      
      if (file.size > 50 * 1024 * 1024) { // 50MB limit
        failedFiles.push(`${file.name}: File too large (max 50MB)`);
        continue;
      }
      
      setCurrentFile(file);
      setModalOpen(true);
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', currentUser.uid);
      
      try {
        const response = await axios.post(
          buildApiUrl(API_ENDPOINTS.PROCESS_SEQUENCE),
          formData,
          { 
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: API_CONFIG.UPLOAD_TIMEOUT
          }
        );
        
        if (response.data && response.data.success) {
          uploadedFiles.push(file.name);
        } else {
          throw new Error(response.data.error || 'Unknown processing error');
        }
      } catch (fileError) {
        console.error(`Upload error for ${file.name}:`, fileError);
        failedFiles.push(`${file.name}: ${fileError.message}`);
      }
    }
    
    // Refresh file list after all uploads complete
    await fetchUserFiles();
    
    // Show results to user
    if (uploadedFiles.length > 0) {
      console.log(`Successfully uploaded: ${uploadedFiles.join(', ')}`);
    }
    
    if (failedFiles.length > 0) {
      setError(`Upload errors: ${failedFiles.join('; ')}`);
    }
    
    setIsUploading(false);
    setModalOpen(false);
    setCurrentFile(null);
    
    // Clear the file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const isFileSelected = (file) => {
    if (!selectedFiles || !Array.isArray(selectedFiles)) return false;
    
    return selectedFiles.some(selected => {
      // Try multiple ways to match files for robustness
      if (selected.id && file.id && selected.id === file.id) return true;
      if (selected.document_id && file.document_id && selected.document_id === file.document_id) return true;
      if (selected.filename && file.filename && selected.filename === file.filename) return true;
      if (selected.originalName && file.originalName && selected.originalName === file.originalName) return true;
      return false;
    });
  };

  // Helper function to get display name for a file
  const getDisplayName = (file) => {
    // Try different filename fields in order of preference
    if (file.originalName) return file.originalName;
    if (file.filename) return file.filename;
    if (file.name) return file.name;
    return 'Unknown File';
  };

  // Helper function to get unique file identifier
  const getFileId = (file) => {
    return file.id || file.document_id || file.filename || file.originalName || JSON.stringify(file);
  };

  // Helper function to get file upload date
  const getUploadDate = (file) => {
    try {
      if (file.uploadedAt) {
        const date = new Date(file.uploadedAt);
        return date.toLocaleDateString();
      }
      return 'Unknown Date';
    } catch (error) {
      return 'Unknown Date';
    }
  };

  const handleAddToChat = (file) => {
    if (onFileSelect) onFileSelect(file);
  };

  return (
    <div style={fileWindowStyles.fileWindow}>
      <ProcessingModal 
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        filename={currentFile?.name}
        steps={{}}
      />
      <div style={fileWindowStyles.header}>
        <h3>Your Files</h3>
        <div style={fileWindowStyles.headerControls}>
          {serverStatus && (
            <span style={{
              ...fileWindowStyles.statusIndicator,
              backgroundColor: serverStatus === 'online' ? '#4caf50' : '#f44336'
            }}></span>
          )}
          <button 
            onClick={fetchUserFiles} 
            disabled={isLoading || serverStatus === 'offline'} 
            style={fileWindowStyles.refreshButton}
          >
            {isLoading ? 'Loading...' : '↻'}
          </button>
        </div>
      </div>
      <div style={fileWindowStyles.uploadContainer}>
        <button 
          onClick={handleUploadClick}
          disabled={isUploading || serverStatus === 'offline'}
          style={fileWindowStyles.uploadButton}
          title="Upload PDF documents or image files (JPG, PNG, GIF, BMP, TIFF, WEBP)"
        >
          {isUploading ? 'Uploading...' : 'Upload PDFs & Images'}
        </button>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          style={{ display: 'none' }}
          multiple
          accept=".pdf,.jpg,.jpeg,.png,.gif,.bmp,.tiff,.webp,image/*"
        />
      </div>
      {error && (
        <div style={fileWindowStyles.errorMessage}>{error}</div>
      )}
      {isLoading ? (
        <div style={fileWindowStyles.loadingIndicator}>Loading your files...</div>
      ) : (
        <div style={fileWindowStyles.fileList}>
          {files.length === 0 ? (
            <div style={fileWindowStyles.noFiles}>
              {serverStatus === 'offline' ? 'Server is offline' : 'No files uploaded yet.'}
            </div>
          ) : (
            files.map((file, index) => {
              if (!file) return null; // Skip null/undefined files
              
              const fileSelected = isFileSelected(file);
              const displayName = getDisplayName(file);
              const fileId = getFileId(file);
              const uploadDate = getUploadDate(file);
              
              return (
                <div 
                  key={fileId || index} // Use fileId or fallback to index
                  style={{
                    ...fileWindowStyles.fileItem,
                    ...(fileSelected ? fileWindowStyles.selectedFileItem : {})
                  }}
                >
                  <div style={fileWindowStyles.fileName} title={displayName}>
                    <span style={fileWindowStyles.fileNameText}>{displayName}</span>
                  </div>
                  <div style={fileWindowStyles.fileInfo}>
                    {uploadDate}
                    <div style={fileWindowStyles.fileActions}>
                      <button 
                        style={{
                          ...fileWindowStyles.actionButton, 
                          ...(fileSelected ? fileWindowStyles.selectedActionButton : {})
                        }}
                        onClick={() => handleAddToChat(file)}
                        title={fileSelected ? "Already added to chat" : "Add to chat"}
                        disabled={fileSelected}
                      >
                        {fileSelected ? "✓" : "+"}
                      </button>
                      <button 
                        style={fileWindowStyles.actionButton}
                        onClick={() => handleDeleteFile(file)}
                        title={`Delete ${displayName}`}
                      >
                        ×
                      </button>
                    </div>
                  </div>
                </div>
              );
            }).filter(Boolean) // Remove any null items
          )}
        </div>
      )}
    </div>
  );
};

export default FileWindow;
