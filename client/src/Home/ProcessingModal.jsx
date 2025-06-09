import React, { useEffect, useState } from 'react';

const ProcessingModal = ({ 
  isOpen, 
  onClose, 
  filename, 
  steps = {
    extraction: 'pending',
    chunking: 'pending',
    embedding: 'pending', 
    vectorStorage: 'pending',
    cloudUpload: 'pending'
  } 
}) => {
  // Add animation state
  const [animationClass, setAnimationClass] = useState(isOpen ? 'show' : '');
  
  // Handle open/close animation
  useEffect(() => {
    if (isOpen) {
      setAnimationClass('show');
    } else {
      setAnimationClass('hide');
      // Wait for animation before fully removing
      const timer = setTimeout(() => {
        setAnimationClass('');
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);
  
  // If modal is completely closed and not animating
  if (!isOpen && animationClass === '') return null;

  // Count completed steps
  const completedSteps = Object.values(steps).filter(s => s === 'completed').length;
  const totalSteps = Object.keys(steps).length;
  const progress = Math.round((completedSteps / totalSteps) * 100);
  
  // Check if any step is currently processing
  const processingStep = Object.keys(steps).find(key => steps[key] === 'processing');

  const renderStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <span style={styles.pendingIcon}>⬜</span>;
      case 'processing':
        return (
          <span style={styles.processingIcon} title="Processing...">
            <div className="spinner"></div>
          </span>
        );
      case 'completed':
        return <span style={styles.completedIcon}>✅</span>;
      case 'failed':
        return <span style={styles.failedIcon}>❌</span>;
      default:
        return <span style={styles.pendingIcon}>⬜</span>;
    }
  };
  
  // Define animation CSS
  const modalStyles = {
    ...styles.modalOverlay,
    opacity: animationClass === 'show' ? 1 : 0,
    pointerEvents: animationClass === 'show' ? 'all' : 'none',
    transition: 'opacity 0.3s ease'
  };
  
  const contentStyles = {
    ...styles.modalContent,
    transform: animationClass === 'show' ? 'translateY(0)' : 'translateY(-20px)',
    transition: 'transform 0.3s ease'
  };

  // Function to get step label
  const getStepLabel = (step) => {
    switch(step) {
      case 'extraction': return 'Text extraction';
      case 'chunking': return 'Text chunking';
      case 'embedding': return 'Embedding generation';
      case 'vectorStorage': return 'Pinecone vector storage';
      case 'cloudUpload': return 'Google Cloud Storage upload';
      default: return step;
    }
  };

  return (
    <div style={modalStyles}>
      <div style={contentStyles}>
        <div style={styles.modalHeader}>
          <h3 style={styles.modalTitle}>
            Processing File 
            {progress > 0 && progress < 100 && <span style={styles.progressText}> - {progress}%</span>}
            {progress === 100 && <span style={styles.successText}> - Complete!</span>}
          </h3>
          <button style={styles.closeButton} onClick={onClose}>×</button>
        </div>
        
        <div style={styles.modalBody}>
          <div style={styles.filenameContainer}>
            <span style={styles.fileIcon}>📄</span>
            <span style={styles.filename}>{filename || 'Document'}</span>
          </div>
          
          {processingStep && (
            <div style={styles.currentStepBanner}>
              Currently processing: <strong>{getStepLabel(processingStep)}</strong>
              <div style={styles.spinnerInline}></div>
            </div>
          )}
          
          <div style={styles.stepsList}>
            {Object.keys(steps).map(step => (
              <div 
                key={step}
                style={{
                  ...styles.step, 
                  ...(steps[step] === 'completed' ? styles.stepCompleted : {}),
                  ...(steps[step] === 'processing' ? styles.stepActive : {}),
                  ...(steps[step] === 'failed' ? styles.stepFailed : {})
                }}
              >
                {renderStatusIcon(steps[step])}
                <span style={styles.stepText}>{getStepLabel(step)}</span>
              </div>
            ))}
          </div>
        </div>
        
        <div style={styles.modalFooter}>
          <button 
            style={{
              ...styles.closeBtn,
              ...(Object.values(steps).some(s => s === 'processing') ? styles.disabledBtn : {})
            }} 
            onClick={onClose}
            disabled={Object.values(steps).some(s => s === 'processing')}
          >
            {Object.values(steps).some(s => s === 'processing') ? 'Processing...' : 'Close'}
          </button>
        </div>
      </div>
      
      {/* Add CSS for spinners */}
      <style>{`
        .spinner {
          border: 3px solid rgba(0, 0, 0, 0.1);
          width: 18px;
          height: 18px;
          border-radius: 50%;
          border-left-color: #2196f3;
          animation: spin 1s linear infinite;
          display: inline-block;
        }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

const styles = {
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000
  },
  modalContent: {
    width: '500px',
    backgroundColor: 'white',
    borderRadius: '8px',
    overflow: 'hidden',
    boxShadow: '0 4px 8px rgba(0, 0, 0, 0.2)'
  },
  modalHeader: {
    padding: '15px 20px',
    borderBottom: '1px solid #eee',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f9f9f9'
  },
  modalTitle: {
    margin: 0,
    color: '#333'
  },
  closeButton: {
    background: 'none',
    border: 'none',
    fontSize: '24px',
    cursor: 'pointer',
    color: '#666'
  },
  modalBody: {
    padding: '20px',
  },
  modalFooter: {
    padding: '15px 20px',
    borderTop: '1px solid #eee',
    display: 'flex',
    justifyContent: 'flex-end'
  },
  filenameContainer: {
    display: 'flex',
    alignItems: 'center',
    padding: '10px',
    backgroundColor: '#f5f5f5',
    borderRadius: '4px',
    marginBottom: '20px'
  },
  fileIcon: {
    fontSize: '24px',
    marginRight: '10px'
  },
  filename: {
    fontWeight: 'bold',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap'
  },
  stepsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '15px'
  },
  step: {
    display: 'flex',
    alignItems: 'center',
    padding: '10px',
    borderRadius: '4px',
    backgroundColor: '#f9f9f9',
    transition: 'background-color 0.3s'
  },
  pendingIcon: {
    marginRight: '15px',
    fontSize: '20px',
    color: '#bdbdbd'
  },
  processingIcon: {
    marginRight: '15px',
    fontSize: '20px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '20px',
    height: '20px'
  },
  completedIcon: {
    marginRight: '15px',
    fontSize: '20px',
    color: '#4caf50'
  },
  failedIcon: {
    marginRight: '15px',
    fontSize: '20px',
    color: '#f44336'
  },
  stepText: {
    fontWeight: '500'
  },
  closeBtn: {
    padding: '8px 16px',
    backgroundColor: '#2196f3',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: 'bold'
  },
  currentStepBanner: {
    padding: '10px',
    marginBottom: '15px',
    backgroundColor: '#e3f2fd',
    borderLeft: '4px solid #2196f3',
    borderRadius: '4px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between'
  },
  spinnerInline: {
    border: '3px solid rgba(0, 0, 0, 0.1)',
    width: '18px',
    height: '18px',
    borderRadius: '50%',
    borderLeft: '3px solid #2196f3',
    animation: 'spin 1s linear infinite',
    display: 'inline-block',
    marginLeft: '10px'
  },
  stepActive: {
    backgroundColor: '#e3f2fd',
    borderLeft: '4px solid #2196f3'
  },
  stepCompleted: {
    backgroundColor: '#e8f5e9',
    borderLeft: '4px solid #4caf50'
  },
  stepFailed: {
    backgroundColor: '#ffebee',
    borderLeft: '4px solid #f44336'
  },
  progressText: {
    fontSize: '16px',
    color: '#2196f3',
    fontWeight: 'normal',
    marginLeft: '8px'
  },
  successText: {
    fontSize: '16px',
    color: '#4caf50',
    fontWeight: 'normal',
    marginLeft: '8px'
  },
  disabledBtn: {
    opacity: 0.5,
    cursor: 'not-allowed',
    backgroundColor: '#cccccc'
  }
};

export default ProcessingModal;
