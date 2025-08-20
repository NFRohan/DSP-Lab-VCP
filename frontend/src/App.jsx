import React, { useState, useCallback, useEffect } from 'react';
import './App.css';

const API_URL = 'http://localhost:8000';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadResponse, setUploadResponse] = useState(null);
  const [fileList, setFileList] = useState([]);
  const [error, setError] = useState('');
  const [apiStatus, setApiStatus] = useState('Checking connection...');

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setUploadResponse(null);
    setError('');
  };

  const checkApiStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/`);
      if (response.ok) {
        setApiStatus('Connected');
      } else {
        setApiStatus('Disconnected');
      }
    } catch (err) {
      setApiStatus('Disconnected');
    }
  }, []);

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch(`${API_URL}/upload-audio/`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setUploadResponse(data);
        fetchUploadedFiles(); // Refresh the file list
        setSelectedFile(null); // Clear the input
        document.querySelector('input[type="file"]').value = '';
      } else {
        setError(data.detail || 'An error occurred during upload.');
      }
    } catch (err) {
      setError('Failed to connect to the server.');
    }
  };

  const fetchUploadedFiles = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/uploaded-files/`);
      const data = await response.json();
      if (response.ok) {
        setFileList(data.files);
      } else {
        setError(data.detail || 'Failed to fetch file list.');
      }
    } catch (err) {
      setError('Failed to connect to the server to fetch files.');
    }
  }, []);

  const handleDelete = async (filename) => {
    try {
      const response = await fetch(`${API_URL}/delete-file/${filename}`, {
        method: 'DELETE',
      });
      const data = await response.json();
      if (response.ok) {
        fetchUploadedFiles(); // Refresh the list after deletion
      } else {
        setError(data.detail || 'Failed to delete file.');
      }
    } catch (err) {
      setError('Failed to connect to the server to delete the file.');
    }
  };

  const handleDownload = async (filename) => {
    try {
      const response = await fetch(`${API_URL}/download-file/${filename}`);
      
      if (response.ok) {
        // Create a blob from the response
        const blob = await response.blob();
        
        // Create a temporary URL for the blob
        const url = window.URL.createObjectURL(blob);
        
        // Create a temporary anchor element and trigger download
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        
        // Clean up
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to download file.');
      }
    } catch (err) {
      setError('Failed to connect to the server to download the file.');
    }
  };

  const handleVoiceProcess = async (filename, voiceType) => {
    try {
      const response = await fetch(`${API_URL}/process-audio/${filename}?voice_type=${voiceType}`, {
        method: 'POST',
      });
      const data = await response.json();
      
      if (response.ok) {
        setUploadResponse({
          ...data,
          message: `Voice processing initiated: ${data.message}`
        });
        // Refresh the file list to show any new processed files
        fetchUploadedFiles();
      } else {
        setError(data.detail || `Failed to process file with ${voiceType} voice.`);
      }
    } catch (err) {
      setError('Failed to connect to the server to process the file.');
    }
  };

  // Fetch files and check API status on component mount
  useEffect(() => {
    checkApiStatus();
    fetchUploadedFiles();
  }, [checkApiStatus, fetchUploadedFiles]);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Audio File Uploader</h1>
        <p>Upload MP3 or WAV files to the FastAPI backend.</p>
        <div className={`status-indicator ${apiStatus.toLowerCase()}`}>
          API Status: {apiStatus}
        </div>
      </header>

      <div className="card">
        <h2>Upload a New Audio File</h2>
        <input type="file" onChange={handleFileChange} accept=".mp3,.wav" />
        <button onClick={handleUpload} disabled={!selectedFile}>
          Upload
        </button>
        {error && <p className="error-message">{error}</p>}
        {uploadResponse && (
          <div className="response-output">
            <h3>Upload Successful:</h3>
            <pre>{JSON.stringify(uploadResponse, null, 2)}</pre>
          </div>
        )}
      </div>

      <div className="card">
        <h2>Uploaded Files</h2>
        <button onClick={fetchUploadedFiles}>Refresh List</button>
        <div className="file-list">
          {fileList.length > 0 ? (
            <ul>
              {fileList.map((file) => (
                <li key={file.filename}>
                  <span>{file.filename} ({(file.size_bytes / 1024).toFixed(2)} KB)</span>
                  <div className="file-actions">
                    <button className="download-btn" onClick={() => handleDownload(file.filename)}>Download</button>
                    <button className="delete-btn" onClick={() => handleDelete(file.filename)}>Delete</button>
                  </div>
                  <div className="voice-processing">
                    <h4>Voice Processing:</h4>
                    <div className="voice-buttons">
                      <button className="voice-btn male" onClick={() => handleVoiceProcess(file.filename, 'male')}>Male</button>
                      <button className="voice-btn female" onClick={() => handleVoiceProcess(file.filename, 'female')}>Female</button>
                      <button className="voice-btn robot" onClick={() => handleVoiceProcess(file.filename, 'robot')}>Robot</button>
                      <button className="voice-btn alien" onClick={() => handleVoiceProcess(file.filename, 'alien')}>Alien</button>
                      <button className="voice-btn helium" onClick={() => handleVoiceProcess(file.filename, 'helium')}>Helium</button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p>No files uploaded yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
