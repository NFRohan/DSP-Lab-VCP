import { useCallback, useEffect, useRef, useState } from 'react';
import './App.css';

const API_URL = 'http://localhost:8000';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadResponse, setUploadResponse] = useState(null);
  const [fileList, setFileList] = useState([]);
  const [error, setError] = useState('');
  const [apiStatus, setApiStatus] = useState('Checking connection...');
  const [processingStatus, setProcessingStatus] = useState({});
  const [voiceEffects, setVoiceEffects] = useState([]);
  const [currentlyPlaying, setCurrentlyPlaying] = useState(null);
  const [audioProgress, setAudioProgress] = useState({});
  const [audioDuration, setAudioDuration] = useState({});
  const [audioVolume, setAudioVolume] = useState({});
  const audioRefsRef = useRef({});

  // Function to group files by their base name (original file)
  const groupFilesByOriginal = (files) => {
    const groups = {};

    files.forEach(file => {
      // Determine if this is a processed file or original
      const filename = file.filename;
      let originalName = filename;
      let effectType = null;

      // Check if filename contains effect suffixes
      const effectSuffixes = ['_robotic', '_male', '_female', '_baby'];
      for (const suffix of effectSuffixes) {
        if (filename.includes(suffix)) {
          originalName = filename.replace(suffix, '');
          effectType = suffix.substring(1); // Remove the underscore
          break;
        }
      }

      if (!groups[originalName]) {
        groups[originalName] = {
          original: null,
          processed: []
        };
      }

      if (effectType) {
        groups[originalName].processed.push({
          ...file,
          effectType
        });
      } else {
        groups[originalName].original = file;
      }
    });

    return groups;
  };

  // Audio playback functions
  const playAudio = (filename) => {
    console.log('Playing audio:', filename);
    // Stop any currently playing audio
    if (currentlyPlaying && audioRefsRef.current[currentlyPlaying]) {
      audioRefsRef.current[currentlyPlaying].pause();
      audioRefsRef.current[currentlyPlaying].currentTime = 0;
    }

    const audioRef = audioRefsRef.current[filename];
    console.log('Audio ref found:', !!audioRef);
    if (audioRef) {
      audioRef.play()
        .then(() => {
          console.log('Audio playing successfully');
          setCurrentlyPlaying(filename);
        })
        .catch((error) => {
          console.error('Error playing audio:', error);
          setError(`Failed to play audio: ${error.message}`);
        });
    } else {
      console.error('Audio ref not found for:', filename);
      setError('Audio element not found');
    }
  };

  const pauseAudio = (filename) => {
    console.log('Pausing audio:', filename);
    const audioRef = audioRefsRef.current[filename];
    if (audioRef) {
      audioRef.pause();
      if (currentlyPlaying === filename) {
        setCurrentlyPlaying(null);
      }
    }
  };

  const onAudioEnded = () => {
    console.log('Audio ended');
    setCurrentlyPlaying(null);
  };

  // Audio progress and control functions
  const updateAudioProgress = (filename, currentTime, duration) => {
    setAudioProgress(prev => ({
      ...prev,
      [filename]: currentTime
    }));
    setAudioDuration(prev => ({
      ...prev,
      [filename]: duration
    }));
  };

  const handleProgressClick = (filename, event) => {
    const audioRef = audioRefsRef.current[filename];
    if (audioRef && audioDuration[filename]) {
      const rect = event.currentTarget.getBoundingClientRect();
      const clickX = event.clientX - rect.left;
      const width = rect.width;
      const percentage = clickX / width;
      const newTime = percentage * audioDuration[filename];
      audioRef.currentTime = newTime;
    }
  };

  const handleVolumeChange = (filename, event) => {
    const audioRef = audioRefsRef.current[filename];
    if (audioRef) {
      const rect = event.currentTarget.getBoundingClientRect();
      const clickX = event.clientX - rect.left;
      const width = rect.width;
      const volume = Math.max(0, Math.min(1, clickX / width));
      audioRef.volume = volume;
      setAudioVolume(prev => ({
        ...prev,
        [filename]: volume
      }));
    }
  };

  const toggleMute = (filename) => {
    const audioRef = audioRefsRef.current[filename];
    if (audioRef) {
      const newMuted = !audioRef.muted;
      audioRef.muted = newMuted;
      setAudioVolume(prev => ({
        ...prev,
        [filename]: newMuted ? 0 : (prev[filename] || 1)
      }));
    }
  };

  const formatTime = (seconds) => {
    if (isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Helper function to stop all audio playback
  const stopAllAudio = () => {
    Object.values(audioRefsRef.current).forEach(audioRef => {
      if (audioRef) {
        audioRef.pause();
        audioRef.currentTime = 0;
      }
    });
    setCurrentlyPlaying(null);
  };

  // Helper function to clean up audio resources for a specific file
  const cleanupAudioForFile = (filename) => {
    const audioRef = audioRefsRef.current[filename];
    if (audioRef) {
      audioRef.pause();
      audioRef.currentTime = 0;
      audioRef.src = '';
      audioRef.load(); // Reset the audio element
      delete audioRefsRef.current[filename];
    }
    if (currentlyPlaying === filename) {
      setCurrentlyPlaying(null);
    }
  };

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setUploadResponse(null);
    setError('');
  };

  const checkApiStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/`);
      if (response.ok) {
        const data = await response.json();
        setApiStatus('Connected');
        // Fetch available voice effects from API
        if (data.available_voice_effects) {
          setVoiceEffects(data.available_voice_effects);
        }
      } else {
        setApiStatus('Disconnected');
      }
    } catch (err) {
      setApiStatus('Disconnected');
    }
  }, []);

  const fetchVoiceEffects = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/voice-effects/`);
      if (response.ok) {
        const data = await response.json();
        setVoiceEffects(data.available_effects);
      }
    } catch (err) {
      console.log('Could not fetch voice effects:', err);
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
    // Confirm deletion
    if (!window.confirm(`Are you sure you want to delete "${filename}"?`)) {
      return;
    }

    try {
      // Clean up audio resources before attempting deletion
      cleanupAudioForFile(filename);

      // Give a small delay to ensure resources are released
      await new Promise(resolve => setTimeout(resolve, 100));

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

  const handleVoiceProcess = async (filename, effectType) => {
    const processingKey = `${filename}-${effectType}`;

    // Set processing status
    setProcessingStatus(prev => ({
      ...prev,
      [processingKey]: 'processing'
    }));

    try {
      const response = await fetch(`${API_URL}/process-audio/${filename}?effect=${effectType}`, {
        method: 'POST',
      });
      const data = await response.json();

      if (response.ok) {
        setProcessingStatus(prev => ({
          ...prev,
          [processingKey]: 'completed'
        }));

        setUploadResponse({
          ...data,
          message: `Voice processing completed: ${data.message}`
        });

        // Refresh the file list to show the new processed file
        fetchUploadedFiles();

        // Clear processing status after a delay
        setTimeout(() => {
          setProcessingStatus(prev => {
            const newStatus = { ...prev };
            delete newStatus[processingKey];
            return newStatus;
          });
        }, 3000);

      } else {
        setProcessingStatus(prev => ({
          ...prev,
          [processingKey]: 'error'
        }));
        setError(data.detail || `Failed to process file with ${effectType} effect.`);

        // Clear error status after a delay
        setTimeout(() => {
          setProcessingStatus(prev => {
            const newStatus = { ...prev };
            delete newStatus[processingKey];
            return newStatus;
          });
        }, 5000);
      }
    } catch (err) {
      setProcessingStatus(prev => ({
        ...prev,
        [processingKey]: 'error'
      }));
      setError('Failed to connect to the server to process the file.');

      // Clear error status after a delay
      setTimeout(() => {
        setProcessingStatus(prev => {
          const newStatus = { ...prev };
          delete newStatus[processingKey];
          return newStatus;
        });
      }, 5000);
    }
  };

  // Fetch files and check API status on component mount
  useEffect(() => {
    checkApiStatus();
    fetchUploadedFiles();
    fetchVoiceEffects();
  }, [checkApiStatus, fetchUploadedFiles, fetchVoiceEffects]);

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎵 Audio File Processing Studio</h1>
        <p>Upload MP3 or WAV files and apply voice effects using advanced AI processing.</p>
        <div className={`status-indicator ${apiStatus.toLowerCase()}`}>
          API Status: {apiStatus}
        </div>
      </header>

      <div className="card">
        <h2>Upload a New Audio File</h2>
        <input type="file" onChange={handleFileChange} accept=".mp3,.wav" />
        <button onClick={handleUpload} disabled={!selectedFile}>
          Upload Audio File
        </button>
        {error && <p className="error-message">{error}</p>}
        {uploadResponse && (
          <div className="response-output">
            <h3>Success:</h3>
            <pre>{JSON.stringify(uploadResponse, null, 2)}</pre>
          </div>
        )}
      </div>

      <div className="card">
        <h2>📁 Uploaded Files & Voice Processing</h2>
        <button onClick={fetchUploadedFiles}>Refresh List</button>
        <div className="file-list">
          {fileList.length > 0 ? (() => {
            const groupedFiles = groupFilesByOriginal(fileList);
            return (
              <div className="file-groups">
                {Object.entries(groupedFiles).map(([originalName, group]) => (
                  <div key={originalName} className="file-group">
                    {/* Original File */}
                    {group.original && (
                      <div className="original-file">
                        <div className="file-header">
                          <span className="file-name">
                            📄 {group.original.filename} ({(group.original.size_bytes / 1024).toFixed(2)} KB)
                          </span>
                          <div className="audio-controls">
                            <audio
                              ref={(ref) => {
                                if (ref) {
                                  audioRefsRef.current[group.original.filename] = ref;
                                  // Initialize volume
                                  ref.volume = audioVolume[group.original.filename] || 1;
                                  // Add error handling
                                  ref.addEventListener('error', (e) => {
                                    console.error('Audio error for', group.original.filename, e);
                                  });
                                  ref.addEventListener('loadstart', () => {
                                    console.log('Loading started for', group.original.filename);
                                  });
                                  ref.addEventListener('canplay', () => {
                                    console.log('Can play', group.original.filename);
                                  });
                                  ref.addEventListener('timeupdate', () => {
                                    updateAudioProgress(group.original.filename, ref.currentTime, ref.duration);
                                  });
                                  ref.addEventListener('loadedmetadata', () => {
                                    updateAudioProgress(group.original.filename, 0, ref.duration);
                                  });
                                }
                              }}
                              onEnded={onAudioEnded}
                              preload="metadata"
                            >
                              <source src={`${API_URL}/files/${group.original.filename}`} type="audio/wav" />
                              <source src={`${API_URL}/files/${group.original.filename}`} type="audio/mpeg" />
                              Your browser does not support the audio element.
                            </audio>
                            <div className="audio-player">
                              <div className="audio-player-controls">
                                <button
                                  className="play-btn"
                                  onClick={() => currentlyPlaying === group.original.filename ? pauseAudio(group.original.filename) : playAudio(group.original.filename)}
                                >
                                  {currentlyPlaying === group.original.filename ? '⏸️' : '▶️'}
                                </button>
                                <div className="audio-progress-container">
                                  <span className="audio-time">
                                    {formatTime(audioProgress[group.original.filename] || 0)}
                                  </span>
                                  <div
                                    className="audio-progress"
                                    style={{
                                      '--progress': `${((audioProgress[group.original.filename] || 0) / (audioDuration[group.original.filename] || 1)) * 100}%`
                                    }}
                                    onClick={(e) => handleProgressClick(group.original.filename, e)}
                                  ></div>
                                  <span className="audio-time">
                                    {formatTime(audioDuration[group.original.filename] || 0)}
                                  </span>
                                </div>
                                <div className="audio-volume-container">
                                  <button
                                    className="volume-btn"
                                    onClick={() => toggleMute(group.original.filename)}
                                  >
                                    {(audioVolume[group.original.filename] || 1) === 0 ? '🔇' : '🔊'}
                                  </button>
                                  <div
                                    className="audio-volume"
                                    style={{
                                      '--volume': `${(audioVolume[group.original.filename] || 1) * 100}%`
                                    }}
                                    onClick={(e) => handleVolumeChange(group.original.filename, e)}
                                  ></div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                        <div className="file-actions">
                          <button className="download-btn" onClick={() => handleDownload(group.original.filename)}>Download</button>
                          <button className="delete-btn" onClick={() => handleDelete(group.original.filename)}>Delete</button>
                        </div>

                        {/* Voice Processing Controls */}
                        <div className="voice-processing">
                          <h4>🎛️ Apply Voice Effects:</h4>
                          <div className="voice-buttons">
                            {voiceEffects.map((effect) => {
                              const processingKey = `${group.original.filename}-${effect}`;
                              const isProcessing = processingStatus[processingKey] === 'processing';
                              const isCompleted = processingStatus[processingKey] === 'completed';
                              const hasError = processingStatus[processingKey] === 'error';

                              return (
                                <button
                                  key={effect}
                                  className={`voice-btn ${effect} ${isProcessing ? 'processing' : ''} ${isCompleted ? 'completed' : ''} ${hasError ? 'error' : ''}`}
                                  onClick={() => handleVoiceProcess(group.original.filename, effect)}
                                  disabled={isProcessing}
                                >
                                  {isProcessing ? '⏳ Processing...' :
                                    isCompleted ? '✅ Completed!' :
                                      hasError ? '❌ Error' :
                                        `${effect.charAt(0).toUpperCase() + effect.slice(1)} Voice`}
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Processed Files */}
                    {group.processed.length > 0 && (
                      <div className="processed-files">
                        <h4 className="processed-header">🎵 Generated Voice Effects:</h4>
                        <ul className="processed-list">
                          {group.processed.map((processedFile) => (
                            <li key={processedFile.filename} className="processed-file">
                              <div className="processed-file-header">
                                <span className="processed-file-name">
                                  🎤 {processedFile.effectType.charAt(0).toUpperCase() + processedFile.effectType.slice(1)} Voice
                                  <span className="file-size">({(processedFile.size_bytes / 1024).toFixed(2)} KB)</span>
                                </span>
                                <div className="audio-controls">
                                  <audio
                                    ref={(ref) => {
                                      if (ref) {
                                        audioRefsRef.current[processedFile.filename] = ref;
                                        // Initialize volume
                                        ref.volume = audioVolume[processedFile.filename] || 1;
                                        // Add error handling
                                        ref.addEventListener('error', (e) => {
                                          console.error('Audio error for', processedFile.filename, e);
                                        });
                                        ref.addEventListener('loadstart', () => {
                                          console.log('Loading started for', processedFile.filename);
                                        });
                                        ref.addEventListener('canplay', () => {
                                          console.log('Can play', processedFile.filename);
                                        });
                                        ref.addEventListener('timeupdate', () => {
                                          updateAudioProgress(processedFile.filename, ref.currentTime, ref.duration);
                                        });
                                        ref.addEventListener('loadedmetadata', () => {
                                          updateAudioProgress(processedFile.filename, 0, ref.duration);
                                        });
                                      }
                                    }}
                                    onEnded={onAudioEnded}
                                    preload="metadata"
                                  >
                                    <source src={`${API_URL}/files/${processedFile.filename}`} type="audio/wav" />
                                    <source src={`${API_URL}/files/${processedFile.filename}`} type="audio/mpeg" />
                                    Your browser does not support the audio element.
                                  </audio>
                                  <div className="audio-player">
                                    <div className="audio-player-controls">
                                      <button
                                        className="play-btn"
                                        onClick={() => currentlyPlaying === processedFile.filename ? pauseAudio(processedFile.filename) : playAudio(processedFile.filename)}
                                      >
                                        {currentlyPlaying === processedFile.filename ? '⏸️' : '▶️'}
                                      </button>
                                      <div className="audio-progress-container">
                                        <span className="audio-time">
                                          {formatTime(audioProgress[processedFile.filename] || 0)}
                                        </span>
                                        <div
                                          className="audio-progress"
                                          style={{
                                            '--progress': `${((audioProgress[processedFile.filename] || 0) / (audioDuration[processedFile.filename] || 1)) * 100}%`
                                          }}
                                          onClick={(e) => handleProgressClick(processedFile.filename, e)}
                                        ></div>
                                        <span className="audio-time">
                                          {formatTime(audioDuration[processedFile.filename] || 0)}
                                        </span>
                                      </div>
                                      <div className="audio-volume-container">
                                        <button
                                          className="volume-btn"
                                          onClick={() => toggleMute(processedFile.filename)}
                                        >
                                          {(audioVolume[processedFile.filename] || 1) === 0 ? '🔇' : '🔊'}
                                        </button>
                                        <div
                                          className="audio-volume"
                                          style={{
                                            '--volume': `${(audioVolume[processedFile.filename] || 1) * 100}%`
                                          }}
                                          onClick={(e) => handleVolumeChange(processedFile.filename, e)}
                                        ></div>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              </div>
                              <div className="processed-file-actions">
                                <button className="download-btn" onClick={() => handleDownload(processedFile.filename)}>Download</button>
                                <button className="delete-btn" onClick={() => handleDelete(processedFile.filename)}>Delete</button>
                              </div>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            );
          })() : (
            <p>No files uploaded yet. Upload an audio file to get started with voice processing!</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
