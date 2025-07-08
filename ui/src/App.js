import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('run');
  const [config, setConfig] = useState({
    base_url: '',
    model: '',
    api_key: ''
  });
  const [configLoading, setConfigLoading] = useState(false);
  const [configError, setConfigError] = useState('');
  const [configSuccess, setConfigSuccess] = useState('');

  // Load configuration from backend
  const loadConfig = async () => {
    setConfigLoading(true);
    setConfigError('');
    
    try {
      const response = await fetch('http://localhost:5000/api/config', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (data.success) {
        setConfig({
          base_url: data.config.base_url || '',
          model: data.config.model || '',
          api_key: data.config.api_key || ''
        });
      } else {
        setConfigError(data.error || 'Failed to load configuration');
      }
    } catch (err) {
      setConfigError('Failed to connect to the server');
    } finally {
      setConfigLoading(false);
    }
  };

  // Save configuration to backend
  const saveConfig = async () => {
    setConfigLoading(true);
    setConfigError('');
    setConfigSuccess('');
    
    try {
      const response = await fetch('http://localhost:5000/api/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          config: {
            base_url: config.base_url,
            model: config.model,
            api_key: config.api_key
          }
        }),
      });

      const data = await response.json();

      if (data.success) {
        setConfigSuccess('Configuration saved successfully!');
        setTimeout(() => setConfigSuccess(''), 3000);
      } else {
        setConfigError(data.error || 'Failed to save configuration');
      }
    } catch (err) {
      setConfigError('Failed to connect to the server');
    } finally {
      setConfigLoading(false);
    }
  };

  // Handle input changes
  const handleConfigChange = (field, value) => {
    setConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Load configuration on component mount
  useEffect(() => {
    loadConfig();
  }, []);

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
        
        {/* Tab Navigation */}
        <div className="tab-navigation">
          <button 
            className={`tab-button ${activeTab === 'run' ? 'active' : ''}`}
            onClick={() => setActiveTab('run')}
          >
            Run Captioning
          </button>
          <button 
            className={`tab-button ${activeTab === 'config' ? 'active' : ''}`}
            onClick={() => setActiveTab('config')}
          >
            Configuration
          </button>
        </div>

        {/* Run Tab */}
        {activeTab === 'run' && (
          <div className="tab-content">
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
          </div>
        )}

        {/* Configuration Tab */}
        {activeTab === 'config' && (
          <div className="tab-content">
            <h2>Configuration</h2>
            
            {configLoading && <p>Loading configuration...</p>}
            
            {configError && (
              <div className="error">
                <h3>Error:</h3>
                <pre>{configError}</pre>
              </div>
            )}

            {configSuccess && (
              <div className="success">
                <p>{configSuccess}</p>
              </div>
            )}

            <form onSubmit={(e) => { e.preventDefault(); saveConfig(); }}>
              <div className="form-group">
                <label htmlFor="base_url">Base URL:</label>
                <input
                  type="text"
                  id="base_url"
                  value={config.base_url}
                  onChange={(e) => handleConfigChange('base_url', e.target.value)}
                  placeholder="e.g., http://localhost:1234/v1"
                />
              </div>

              <div className="form-group">
                <label htmlFor="model">Model:</label>
                <input
                  type="text"
                  id="model"
                  value={config.model}
                  onChange={(e) => handleConfigChange('model', e.target.value)}
                  placeholder="e.g., gpt-4o-mini"
                />
              </div>

              <div className="form-group">
                <label htmlFor="api_key">API Key:</label>
                <input
                  type="password"
                  id="api_key"
                  value={config.api_key}
                  onChange={(e) => handleConfigChange('api_key', e.target.value)}
                  placeholder="Leave empty for local models"
                />
              </div>

              <div className="form-actions">
                <button 
                  type="submit" 
                  disabled={configLoading}
                  className="save-button"
                >
                  {configLoading ? 'Saving...' : 'Save Configuration'}
                </button>
                <button 
                  type="button" 
                  onClick={loadConfig}
                  disabled={configLoading}
                  className="reload-button"
                >
                  Reload
                </button>
              </div>
            </form>
          </div>
        )}
      </header>
    </div>
  );
}

export default App;
