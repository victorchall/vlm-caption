import React, { useEffect } from 'react';

const RunTab = ({ 
  apiPort, 
  configSuccess, 
  isSaving, 
  onSaveConfig,
  isRunning,
  error,
  streamingOutput,
  outputRef,
  onRunCaptioning,
  onStopCaptioning
}) => {
  // Auto-scroll to bottom of output
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [streamingOutput, outputRef]);

  return (
    <div className="tab-content">
      <div style={{ marginBottom: '10px' }}>
        <p style={{ margin: 0 }}>Click the button below to start the captioning process</p>
      </div>
      
      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
        <button
          onClick={onRunCaptioning}
          disabled={isRunning || isSaving}
          className="run-button"
        >
          {isSaving ? 'Saving...' : (isRunning ? 'Running...' : 'Run Captioning')}
        </button>

        {isRunning && (
          <button
            onClick={onStopCaptioning}
            className="stop-button"
          >
            Stop Captioning
          </button>
        )}
      </div>

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
    </div>
  );
};

export default RunTab;
