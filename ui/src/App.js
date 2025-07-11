import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [apiPort, setApiPort] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('config');
  const [config, setConfig] = useState({
    base_url: '',
    model: '',
    api_key: '',
    system_prompt: '',
    prompts: [],
    base_directory: '',
    recursive: false,
    hint_sources: [],
    global_metadata_file: '',
    skip_if_txt_exists: false
  });
  const [configLoading, setConfigLoading] = useState(false);
  const [configError, setConfigError] = useState('');
  const [configSuccess, setConfigSuccess] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [models, setModels] = useState([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [modelsError, setModelsError] = useState('');
  const [hintSources, setHintSources] = useState({});
  const [hintSourcesLoading, setHintSourcesLoading] = useState(false);
  const [hintSourcesError, setHintSourcesError] = useState('');
  const directoryInputRef = useRef(null);
  const metadataFileInputRef = useRef(null);
  //const inputRef = useRef(null);
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
        throw new Error(`${response.statusText}`);
      }
      
      const data = await response.json();

      if (data.data && Array.isArray(data.data)) {
        const modelIds = data.data.map(m => m.id);
        setModels(modelIds);
      } else {
        setModelsError('Unexpected response format from models endpoint');
      }
    } catch (err) {
      setModelsError(`Failed to fetch models: ${err.message}. Check that your VLM host is running and API service is enabled.`);
    } finally {
      setModelsLoading(false);
    }
  };

  // Load configuration from backend
  const loadConfig = async () => {
    if (!apiPort) return;
    setConfigLoading(true);
    setConfigError('');
    
    try {
      const response = await fetch(`http://localhost:${apiPort}/api/config`, {
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
          system_prompt: data.config.system_prompt || '',
          prompts: data.config.prompts || [''],
          base_directory: data.config.base_directory || '',
          recursive: data.config.recursive || false,
          hint_sources: data.config.hint_sources || [],
          global_metadata_file: data.config.global_metadata_file || '',
          skip_if_txt_exists: data.config.skip_if_txt_exists || false
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
    if (!apiPort) return;
    setIsSaving(true);
    setConfigLoading(true);
    setConfigError('');
    setConfigSuccess('');
    
    try {
      const response = await fetch(`http://localhost:${apiPort}/api/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          config: {
            base_url: config.base_url,
            model: config.model,
            api_key: config.api_key,
            prompts: config.prompts,
            base_directory: config.base_directory,
            recursive: config.recursive,
            hint_sources: config.hint_sources,
            global_metadata_file: config.global_metadata_file,
            skip_if_txt_exists: config.skip_if_txt_exists
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
      setIsSaving(false);
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

  const handleTabSwitch = async (tab) => {
    if (tab === 'run') {
      await saveConfig();
    }
    setActiveTab(tab);
  };

  const handleDirectorySelect = (e) => {
    if (e.target.files.length > 0) {
      const file = e.target.files[0];
      // In Electron, file.path provides the absolute path.
      // We can derive the directory path from the path of the first file.
      const path = file.path;
      const lastSeparatorIndex = Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\'));
      const directoryPath = path.substring(0, lastSeparatorIndex);
      handleConfigChange('base_directory', directoryPath);
    }
  };

  const handleMetadataFileSelect = (e) => {
    if (e.target.files.length > 0) {
      const file = e.target.files[0];
      // In Electron, file.path provides the absolute path
      const path = file.path;
      handleConfigChange('global_metadata_file', path);
    }
  };

  // Load configuration on component mount
  useEffect(() => {
    if (window.api) {
      window.api.receive('set-api-port', (port) => {
        console.log(`Received API port: ${port}`);
        setApiPort(port);
      });
    }
  }, []);

  useEffect(() => {
    if (apiPort) {
      loadConfig();
      fetchHintSources();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiPort]);

  const fetchHintSources = async () => {
    if (!apiPort) return;
    setHintSourcesLoading(true);
    setHintSourcesError('');

    try {
      const response = await fetch(`http://localhost:${apiPort}/api/hint_sources`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (data.success) {
        setHintSources(data.hint_sources);
      } else {
        setHintSourcesError(data.error || 'Failed to load hint sources');
      }
    } catch (err) {
      setHintSourcesError('Failed to connect to the server');
    } finally {
      setHintSourcesLoading(false);
    }
  };

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

  return (
    <div className="App">
      <header className="App-header">
        <h1>VLM Caption</h1>
        
        {/* Tab Navigation */}
        <div className="tab-navigation">
          <button 
            className={`tab-button ${activeTab === 'config' ? 'active' : ''}`}
            onClick={() => handleTabSwitch('config')}
          >
            Configuration
          </button>
          <button 
            className={`tab-button ${activeTab === 'run' ? 'active' : ''}`}
            onClick={() => handleTabSwitch('run')}
          >
            Run
          </button>

        </div>

        {/* Run Tab */}
        {activeTab === 'run' && (
          <div className="tab-content">
            <p>Click the button below to start the captioning process</p>
            <button
              onClick={runCaptioning}
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
            {configLoading && <p>Loading configuration...</p>}

            {configError && (
              <div className="error">
                <h3>Error:</h3>
                <pre>{configError}</pre>
              </div>
            )}


            <form onSubmit={(e) => { e.preventDefault(); saveConfig(); }}>
              <div className="form-group side-by-side">
                <div>
                  <label htmlFor="base_url">Base URL</label>
                  <input
                    type="text"
                    id="base_url"
                    value={config.base_url}
                    onChange={(e) => handleConfigChange('base_url', e.target.value)}
                    placeholder="e.g., http://localhost:1234/v1"
                  />
                  <span className="description-text">Copy from LM Studio developer tab.</span>
                </div>

                <div>
                  <label htmlFor="model">Model</label>
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
              </div>

              <div className="form-group side-by-side api-key-directory">
                <div>
                  <label htmlFor="api_key">API Key</label>
                  <input
                    type="password"
                    id="api_key"
                    value={config.api_key}
                    onChange={(e) => handleConfigChange('api_key', e.target.value)}
                    placeholder="Leave empty for local models"
                  />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '5px' }}>
                    <label htmlFor="base_directory">Base Directory</label>
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <label htmlFor="recursive" style={{ marginRight: '5px' }}>Recursive</label>
                      <input
                        type="checkbox"
                        id="recursive"
                        className="recursive-checkbox"
                        checked={config.recursive}
                        onChange={(e) => handleConfigChange('recursive', e.target.checked)}
                      />
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <label htmlFor="skip_if_txt_exists" style={{ marginRight: '40px' }}>Skip image if .txt exists</label>
                      <input
                        type="checkbox"
                        id="skip_if_txt_exists"
                        className="skip-if-txt-exists-checkbox"
                        checked={config.skip_if_txt_exists}
                        onChange={(e) => handleConfigChange('skip_if_txt_exists', e.target.checked)}
                      />
                    </div>

                  </div>
                  <div style={{ display: 'flex' }}>
                    <input
                      type="text"
                      id="base_directory"
                      value={config.base_directory}
                      onChange={(e) => handleConfigChange('base_directory', e.target.value)}
                      placeholder="e.g., C:\Users\YourUser\Images"
                      style={{ flex: 1, marginRight: '10px' }}
                    />
                    <input
                      type="file"
                      webkitdirectory="true"
                      style={{ display: 'none' }}
                      ref={directoryInputRef}
                      onChange={handleDirectorySelect}
                    />
                    <button
                      type="button"
                      onClick={() => directoryInputRef.current.click()}
                      className="reload-button"
                    >
                      Select...
                    </button>
                  </div>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="global_metadata_file">Global Metadata File</label>
                
                <div className="directory-picker" style={{ display: 'flex' }}>
                  <input
                    type="text"
                    id="global_metadata_file"
                    value={config.global_metadata_file}
                    onChange={(e) => handleConfigChange('global_metadata_file', e.target.value)}
                    placeholder="e.g., C:\Users\YourUser\metadata.txt"
                    style={{ flex: 1, marginRight: '10px' }}
                  />
                  <input
                    type="file"
                    accept=".txt"
                    style={{ display: 'none' }}
                    ref={metadataFileInputRef}
                    onChange={handleMetadataFileSelect}
                  />
                  <button
                    type="button"
                    onClick={() => metadataFileInputRef.current.click()}
                    className="reload-button"
                  >
                    Select...
                  </button>
                </div>
                <span className="description-text">(Optional) A .txt file to provide additional context for image analysis, helping the model generate more accurate caption, such as a codex with character and location visual descriptions.</span>
              </div>

              <div className="form-group">
                <label htmlFor="system_prompt">System Prompt</label>
                
                <textarea
                  type="text"
                  id="system_prompt"
                  value={config.system_prompt}
                  onChange={(e) => handleConfigChange('system_prompt', e.target.value)}
                  placeholder="You are an expert image analyzer..."
                  rows="3"
                />
                <span className="description-text">(Optional) General directives to the VLM for all steps.</span>
              </div>

              <div className="form-group">
                <label>Prompts</label>
                <span className="description-text">Enter a series of 1 or more prompts to extract visual information.</span>
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
                <span className="description-text"><b>Last prompt will generate the caption.</b></span>
                <br/>
                <button
                  type="button"
                  onClick={addPrompt}
                  className="add-prompt-button"
                >
                  Add Prompt
                </button>
              </div>

              {Object.keys(hintSources).length > 0 && (
                <div className="form-group">
                  <label>Hint Sources</label>
                  <div className="hint-sources-info">
                    <span className="description-text">Select additional context sources to enhance captioning. These provide extra information to the model for better caption accuracy. These are typically sourced from your webscrapes, classifiers, alt-text, etc.</span>
                  </div>
                  {hintSourcesLoading && <p>Loading hint sources...</p>}
                  {hintSourcesError && <p className="error-text">{hintSourcesError}</p>}
                  <div className="hint-sources-container">
                    {Object.entries(hintSources).map(([sourceKey, sourceData]) => (
                      <div key={sourceKey} className="hint-source-item">
                        <div className="hint-source-key">
                          {sourceData.display_name}
                        </div>
                        <div className="hint-source-description">
                          {sourceData.description}
                        </div>
                        <label className="hint-source-checkbox">
                          <input
                            type="checkbox"
                            checked={config.hint_sources.includes(sourceKey)}
                            onChange={(e) => {
                              const newHintSources = e.target.checked
                                ? [...config.hint_sources, sourceKey]
                                : config.hint_sources.filter(s => s !== sourceKey);
                              handleConfigChange('hint_sources', newHintSources);
                            }}
                          />
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </form>
          </div>
        )}
      </header>
    </div>
  );
}

export default App;
