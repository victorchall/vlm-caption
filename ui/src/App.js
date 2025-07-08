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
    api_key: '',
    prompts: []
  });
  const [configLoading, setConfigLoading] = useState(false);
  const [configError, setConfigError] = useState('');
  const [configSuccess, setConfigSuccess] = useState('');
  const [models, setModels] = useState([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [modelsError, setModelsError] = useState('');

  // Fetch models from base_url
  const fetchModels = async (baseUrl) => {
    if (!baseUrl) {
      setModels([]);
      return;
    }

    setModelsLoading(true);
    setModelsError('');
    
    try {
      // Ensure the URL has a scheme
      let url = baseUrl;
      if (!/^https?:\/\//i.test(url)) {
        url = 'http://' + url;
      }
      
      // Construct the models URL
      const modelsUrl = new URL('v1/models', url).toString();
      
      const response = await fetch(modelsUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch models: ${response.statusText}`);
      }
      
      const data = await response.json();

      if (data.data && Array.isArray(data.data)) {
        const modelIds = data.data.map(m => m.id);
        setModels(modelIds);
      } else {
        setModelsError('Unexpected response format from models endpoint');
      }
    } catch (err) {
      setModelsError(`Failed to fetch models: ${err.message}`);
    } finally {
      setModelsLoading(false);
    }
  };

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
        const newConfig = {
          base_url: data.config.base_url || '',
          model: data.config.model || '',
          api_key: data.config.api_key || '',
          prompts: data.config.prompts || ['']
        };
        setConfig(newConfig);
        if (newConfig.base_url) {
          fetchModels(newConfig.base_url);
        }
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
            api_key: config.api_key,
            prompts: config.prompts
          }
        }),
      });

      const data = await response.json();

      if (data.success) {
        setConfigSuccess(data.message);
        setTimeout(() => setConfigSuccess(''), 10000);
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
    setConfig(prev => {
      const newConfig = { ...prev, [field]: value };
      
      // If base_url changes, clear models and selected model, then fetch new models
      if (field === 'base_url') {
        setModels([]);
        newConfig.model = '';
        fetchModels(value);
      }
      
      return newConfig;
    });
  };

  // Handle prompt changes
  const handlePromptChange = (index, value) => {
    const newPrompts = [...config.prompts];
    newPrompts[index] = value;
    handleConfigChange('prompts', newPrompts);
  };

  // Add a new prompt
  const addPrompt = () => {
    handleConfigChange('prompts', [...config.prompts, '']);
  };

  // Remove a prompt
  const removePrompt = (index) => {
    const newPrompts = config.prompts.filter((_, i) => i !== index);
    handleConfigChange('prompts', newPrompts);
  };

  // Load configuration on component mount
  useEffect(() => {
    loadConfig();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
            className={`tab-button ${activeTab === 'config' ? 'active' : ''}`}
            onClick={() => setActiveTab('config')}
          >
            Configuration
          </button>
          <button 
            className={`tab-button ${activeTab === 'run' ? 'active' : ''}`}
            onClick={() => setActiveTab('run')}
          >
            Run Captioning
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
                <div className="model-selection">
                  <select
                    id="model"
                    value={config.model}
                    onChange={(e) => handleConfigChange('model', e.target.value)}
                    disabled={modelsLoading || !config.base_url}
                  >
                    <option value="">
                      {config.base_url ? 'Select a model' : 'Enter Base URL first'}
                    </option>
                    {models.map(modelId => (
                      <option key={modelId} value={modelId}>
                        {modelId}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={() => fetchModels(config.base_url)}
                    disabled={modelsLoading || !config.base_url}
                    className="reload-button"
                  >
                    {modelsLoading ? '...' : 'Refresh'}
                  </button>
                </div>
                {modelsError && <p className="error-text">{modelsError}</p>}
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

              <div className="form-group">
                <label>Prompts:</label>
                {config.prompts.map((prompt, index) => (
                  <div key={index} className="prompt-item">
                    <textarea
                      value={prompt}
                      onChange={(e) => handlePromptChange(index, e.target.value)}
                      placeholder={`Prompt ${index + 1}`}
                      rows="3"
                    />
                    <button 
                      type="button" 
                      onClick={() => removePrompt(index)}
                      className="remove-prompt-button"
                    >
                      &times;
                    </button>
                  </div>
                ))}
                <button 
                  type="button" 
                  onClick={addPrompt}
                  className="add-prompt-button"
                >
                  Add Prompt
                </button>
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
