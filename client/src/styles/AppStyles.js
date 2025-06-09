// Collection of styles for the application components

export const homeStyles = {
  container: {
    maxWidth: '100%',
    margin: '0 auto',
    padding: '20px'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '20px'
  },
  mainContent: {
    display: 'flex',
    height: '70vh',
    border: '1px solid #ddd',
    borderRadius: '8px',
    overflow: 'hidden'
  },
  chatContainer: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    border: 'none',
  },
  messages: {
    flex: 1,
    padding: '20px',
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column'
  },
  message: {
    padding: '10px 15px',
    borderRadius: '8px',
    marginBottom: '10px',
    maxWidth: '70%',
    wordBreak: 'break-word'
  },
  userMessage: {
    backgroundColor: '#e3f2fd',
    alignSelf: 'flex-end'
  },
  botMessage: {
    backgroundColor: '#f1f1f1',
    alignSelf: 'flex-start'
  },
  inputForm: {
    display: 'flex',
    flexDirection: 'row', // Fixed: changed from column to row
    padding: '10px',
    borderTop: '1px solid #ddd'
  },
  input: {
    flex: 1,
    padding: '10px',
    borderRadius: '4px',
    border: '1px solid #ddd'
  },
  sendButton: {
    marginLeft: '10px',
    padding: '10px 15px',
    background: '#2196f3',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer'
  },
  signOutButton: {
    padding: '8px 16px',
    background: '#f44336',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer'
  },
  resetButton: {
    padding: '8px 16px',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500'
  },
  attachmentsPreviewContainer: {
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#f9f9f9',
    borderTop: '1px solid #ddd',
    maxHeight: '120px',
    overflowY: 'auto'
  },
  attachmentPreview: {
    display: 'flex',
    alignItems: 'center',
    padding: '10px',
    borderBottom: '1px solid #eee'
  },
  attachmentName: {
    fontWeight: '500',
    marginRight: '6px'
  },
  attachmentSize: {
    color: '#666',
    fontSize: '12px'
  },
  removeAttachmentButton: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '14px',
    marginLeft: 'auto'
  },
  attachmentInfo: {
    marginTop: '8px',
    padding: '6px',
    backgroundColor: 'rgba(0,0,0,0.05)',
    borderRadius: '4px',
    fontSize: '12px'
  },
  attachmentMeta: {
    color: '#666',
    fontSize: '10px',
    marginTop: '2px'
  },
  errorMessage: {
    backgroundColor: '#ffebee',
    color: '#c62828'
  },
  loadingMessage: {
    opacity: 0.7,
    fontStyle: 'italic'
  },
  uploadedBadge: {
    backgroundColor: '#4caf50',
    color: 'white',
    fontSize: '10px',
    padding: '2px 6px',
    borderRadius: '10px',
    marginLeft: '8px'
  },
  uploadingIndicator: {
    padding: '8px',
    textAlign: 'center',
    fontSize: '12px',
    color: '#666',
    fontStyle: 'italic'
  },
  userInfo: {
    fontSize: '14px',
    color: '#555',
    marginTop: '-12px',
    marginBottom: '10px'
  },
  testModeIndicator: {
    backgroundColor: '#ff9800',
    color: 'white',
    padding: '4px 8px',
    borderRadius: '4px',
    fontWeight: 'bold',
    fontSize: '12px',
    display: 'inline-block',
    marginBottom: '10px'
  },
  extractionPanel: {
    marginBottom: '20px',
    border: '1px solid #ddd',
    borderRadius: '8px',
    overflow: 'hidden'
  },
  extractionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 15px',
    backgroundColor: '#f5f5f5',
    borderBottom: '1px solid #ddd'
  },
  toggleButton: {
    padding: '5px 10px',
    backgroundColor: '#2196f3',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer'
  },
  extractedTextContainer: {
    padding: '15px',
    maxHeight: '400px',
    overflowY: 'auto',
    backgroundColor: '#fff'
  },
  fileInfo: {
    marginBottom: '15px',
    padding: '10px',
    backgroundColor: '#f9f9f9',
    borderRadius: '4px'
  },
  pageContainer: {
    marginBottom: '20px',
    border: '1px solid #eee',
    borderRadius: '4px'
  },
  pageHeader: {
    padding: '5px 10px',
    backgroundColor: '#e3f2fd',
    borderBottom: '1px solid #eee',
    fontWeight: 'bold'
  },
  pageText: {
    padding: '10px',
    whiteSpace: 'pre-wrap',
    fontFamily: 'monospace',
    fontSize: '14px',
    overflowX: 'auto',
    maxHeight: '300px',
    overflowY: 'auto'
  },
  stepContainer: {
    marginBottom: '20px',
    border: '1px solid #eee',
    borderRadius: '4px',
    overflow: 'hidden'
  },
  stepHeader: {
    padding: '8px 12px',
    backgroundColor: '#2196f3',
    color: 'white',
    fontWeight: 'bold'
  },
  stepContent: {
    padding: '12px'
  },
  previewBox: {
    backgroundColor: '#f9f9f9',
    padding: '10px',
    borderRadius: '4px',
    marginTop: '10px'
  },
  previewText: {
    whiteSpace: 'pre-wrap',
    fontFamily: 'monospace',
    fontSize: '14px',
    overflowX: 'auto',
    maxHeight: '150px',
    overflowY: 'auto'
  },
  processingIndicator: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    backgroundColor: 'rgba(33, 150, 243, 0.9)',
    color: 'white',
    padding: '15px 20px',
    borderRadius: '5px',
    fontSize: '16px',
    fontWeight: 'bold',
    zIndex: 999
  },
  selectedFilesContainer: {
    display: 'flex',
    flexDirection: 'column',
    borderTop: '1px solid #ddd',
    borderBottom: '1px solid #ddd',
    maxHeight: '150px',
    overflowY: 'auto',
  },
  selectedFileIndicator: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 15px',
    backgroundColor: '#e3f2fd',
    borderBottom: '1px solid #ddd',
  },
  selectedFileName: {
    fontSize: '14px',
    fontWeight: '500',
    color: '#2196f3',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  removeSelectedFileButton: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: 'bold',
    color: '#666',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '24px',
    height: '24px',
    borderRadius: '3px',
    padding: 0,
  },
};

export const fileWindowStyles = {
  fileWindow: {
    width: '300px',
    borderRight: '1px solid #ddd',
    height: '100%',
    overflowY: 'auto',
    backgroundColor: '#f9f9f9'
  },
  header: {
    padding: '10px 15px',
    borderBottom: '1px solid #ddd',
    backgroundColor: '#f0f0f0',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  refreshButton: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '16px',
    padding: '5px'
  },
  fileList: {
    padding: '10px'
  },
  fileItem: {
    padding: '8px 10px',
    borderBottom: '1px solid #eee',
    display: 'flex',
    flexDirection: 'column',
  },
  fileName: {
    display: 'flex',
    alignItems: 'center',
    cursor: 'pointer',
    overflow: 'hidden',
    whiteSpace: 'nowrap',
    textOverflow: 'ellipsis',
    fontSize: '14px',
    fontWeight: '500'
  },
  fileNameText: {
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    width: '100%'
  },
  fileInfo: {
    color: '#777',
    fontSize: '12px',
    marginTop: '4px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  fileActions: {
    display: 'flex',
    gap: '5px'
  },
  actionButton: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '16px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '24px',
    height: '24px',
    borderRadius: '3px',
    padding: 0,
    fontWeight: 'bold',
    transition: 'background-color 0.2s'
  },
  loadingIndicator: {
    padding: '20px',
    textAlign: 'center',
    color: '#666',
    fontStyle: 'italic'
  },
  errorMessage: {
    padding: '10px',
    margin: '10px',
    backgroundColor: '#ffebee',
    color: '#c62828',
    borderRadius: '4px',
    fontSize: '14px'
  },
  noFiles: {
    padding: '20px',
    textAlign: 'center',
    color: '#666',
    fontStyle: 'italic'
  },
  headerControls: {
    display: 'flex',
    alignItems: 'center',
  },
  statusIndicator: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    marginRight: '8px'
  },
  uploadContainer: {
    padding: '10px',
    borderBottom: '1px solid #ddd',
    textAlign: 'center'
  },
  uploadButton: {
    padding: '8px 12px',
    backgroundColor: '#2196f3',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    width: '100%',
    fontWeight: 'bold'
  },
  processingContainer: {
    padding: '10px',
    backgroundColor: '#e3f2fd',
    borderBottom: '1px solid #ddd',
  },
  processingStatus: {
    fontSize: '12px',
    marginBottom: '5px',
    textAlign: 'center',
    fontWeight: 'bold',
  },
  progressContainer: {
    height: '4px',
    backgroundColor: '#e0e0e0',
    borderRadius: '2px',
    overflow: 'hidden',
    position: 'relative',
    marginBottom: '5px'
  },
  progressBar: {
    height: '100%',
    backgroundColor: '#2196f3',
    transition: 'width 0.3s ease',
  },
  stepIndicator: {
    fontSize: '10px',
    textAlign: 'center',
    color: '#666'
  },
  selectedFileItem: {
    backgroundColor: 'rgba(33, 150, 243, 0.1)',
    borderLeft: '3px solid #2196f3',
  },
  selectedActionButton: {
    color: '#2196f3',
    fontWeight: 'bold',
  },
  // New styles for chat system sources display
  sourcesContainer: {
    marginTop: '10px',
    padding: '10px',
    backgroundColor: '#f8f9fa',
    borderRadius: '6px',
    borderLeft: '3px solid #28a745',
  },
  sourcesHeader: {
    fontSize: '12px',
    fontWeight: 'bold',
    color: '#28a745',
    marginBottom: '8px',
  },
  sourceItem: {
    marginBottom: '8px',
    padding: '6px',
    backgroundColor: 'white',
    borderRadius: '4px',
    border: '1px solid #e9ecef',
  },
  sourceName: {
    fontSize: '12px',
    fontWeight: 'bold',
    color: '#495057',
    marginBottom: '4px',
  },
  similarityScore: {
    fontSize: '10px',
    color: '#6c757d',
    fontWeight: 'normal',
    marginLeft: '5px',
  },
  sourcePreview: {
    fontSize: '11px',
    color: '#6c757d',
    fontStyle: 'italic',
    lineHeight: '1.3',
  },
  debugInfo: {
    fontSize: '10px',
    color: '#6c757d',
    marginTop: '8px',
    padding: '4px 8px',
    backgroundColor: '#f1f3f4',
    borderRadius: '3px',
    fontFamily: 'monospace',
  }
};
