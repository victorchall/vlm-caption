import React, { useState, useRef, useEffect } from 'react';

const RunTab = ({ apiPort, configSuccess, isSaving, onSaveConfig }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [streamingOutput, setStreamingOutput] = useState('');
  const [useStreaming, setUseStreaming] = useState(true);
  const outputRef = useRef(null);

  // Auto-scroll to bottom of output
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [streamingOutput]);

  const runCaptioning = async () => {
    if (!apiPort) return;
    setIsRunning(true);
    setOutput('');
    setError('');

    try {
      const response = await fetch(`http://localhost:${apiPort}/api/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (data.success) {
        setOutput(data.output);
      } else {
        setError(data.error || 'An error occurred');
      }
    } catch (err) {
      setError('Failed to connect to the server');
    } finally {
      setIsRunning(false);
    }
  };

  const runCaptioningWithStreaming = () => {
    if (!apiPort) return;
    setIsRunning(true);
    setStreamingOutput('');
    setOutput('');
    setError('');

    // Helper function to truncate output if it exceeds 10k characters
    const truncateOutput = (currentOutput, newData) => {
      const combined = currentOutput + newData;
      const MAX_CHARS = 10000;
      const TRUNCATE_TO = 8000; // Keep 8k chars after truncation for buffer
      
      if (combined.length <= MAX_CHARS) {
        return combined;
      }
      
      // Find a good place to truncate (preferably at a line break)
      const truncatePoint = combined.length - TRUNCATE_TO;
      const truncateStart = combined.indexOf('\n', truncatePoint);
      const actualTruncatePoint = truncateStart !== -1 ? truncateStart + 1 : truncatePoint;
      
      const truncated = combined.substring(actualTruncatePoint);
      return '...[output truncated]...\n' + truncated;
    };

    // Create EventSource for Server-Sent Events
    const eventSource = new EventSource(`http://localhost:${apiPort}/api/run-stream`, {
      withCredentials: false
    });

    eventSource.onmessage = (event) => {
      const data = event.data;
      
      // Handle special control messages
      if (data.startsWith('[STARTED]')) {
        setStreamingOutput(prev => truncateOutput(prev, data.substring(9) + '\n'));
      } else if (data.startsWith('[COMPLETE]')) {
        setStreamingOutput(prev => truncateOutput(prev, '\n🎉 Captioning completed successfully!\n'));
        setIsRunning(false);
        eventSource.close();
      } else if (data.startsWith('[ERROR]')) {
        setError(data.substring(7));
        setIsRunning(false);
        eventSource.close();
      } else if (data === '[KEEPALIVE]') {
        // Ignore keepalive messages
      } else {
        // Regular output
        setStreamingOutput(prev => truncateOutput(prev, data + '\n'));
      }
    };

    eventSource.onerror = (error) => {
      console.error('EventSource error:', error);
      setError('Connection to server lost');
      setIsRunning(false);
      eventSource.close();
    };

    // Store reference to close if needed
    window.currentEventSource = eventSource;
  };

  const handleRunCaptioning = async () => {
    // Save config before running
    await onSaveConfig();
    
    if (useStreaming) {
      runCaptioningWithStreaming();
    } else {
      runCaptioning();
    }
  };

  return (
    <div className="tab-content">
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
        <p style={{ margin: 0, marginRight: '15px' }}>Click the button below to start the captioning process</p>
        <label style={{ display: 'flex', alignItems: 'center', fontSize: '14px' }}>
          <input
            type="checkbox"
            checked={useStreaming}
            onChange={(e) => setUseStreaming(e.target.checked)}
            style={{ marginRight: '5px' }}
          />
          Real-time streaming
        </label>
      </div>
      
      <button
        onClick={handleRunCaptioning}
        disabled={isRunning || isSaving}
        className="run-button"
      >
        {isSaving ? 'Saving...' : (isRunning ? 'Running...' : 'Run Captioning')}
      </button>

      {configSuccess && (
        <div className="success">
          <p>{configSuccess}</p>
        </div>
      )}

      {error && (
        <div className="error">
          <h3>Error:</h3>
          <pre>{error}</pre>
        </div>
      )}

      {/* Streaming output */}
      {streamingOutput && (
        <div className="output">
          <h3>Live Output:</h3>
          <pre
            ref={outputRef}
          >
            {streamingOutput}
          </pre>
        </div>
      )}

      {/* Regular output (fallback) */}
      {output && !streamingOutput && (
        <div className="output">
          <h3>Output:</h3>
          <pre>{output}</pre>
        </div>
      )}
    </div>
  );
};

export default RunTab;
