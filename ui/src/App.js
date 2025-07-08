import React, { useState } from 'react';
import './App.css';

function App() {
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');

  const runCaptioning = async () => {
    setIsRunning(true);
    setOutput('');
    setError('');

    try {
      const response = await fetch('http://localhost:5000/api/run', {
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

  return (
    <div className="App">
      <header className="App-header">
        <h1>VLM Caption</h1>
        <p>Click the button below to start the captioning process</p>
        
        <button 
          onClick={runCaptioning} 
          disabled={isRunning}
          className="run-button"
        >
          {isRunning ? 'Running...' : 'Run Captioning'}
        </button>

        {error && (
          <div className="error">
            <h3>Error:</h3>
            <pre>{error}</pre>
          </div>
        )}

        {output && (
          <div className="output">
            <h3>Output:</h3>
            <pre>{output}</pre>
          </div>
        )}
      </header>
    </div>
  );
}

export default App;
