import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import ConfigForm from './components/ConfigForm';

function App() {
  const [apiPort, setApiPort] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [streamingOutput, setStreamingOutput] = useState('');
  const [useStreaming, setUseStreaming] = useState(true);
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
  const outputRef = useRef(null);
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


  const handleTabSwitch = async (tab) => {
    if (tab === 'run') {
      await saveConfig();
    }
    setActiveTab(tab);
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

  const handleRunCaptioning = () => {
    if (useStreaming) {
      runCaptioningWithStreaming();
    } else {
      runCaptioning();
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
        )}

        {/* Configuration Tab */}
        {activeTab === 'config' && (
          <ConfigForm
            config={config}
            onConfigChange={handleConfigChange}
            onSave={saveConfig}
            models={models}
            modelsLoading={modelsLoading}
            modelsError={modelsError}
            onFetchModels={fetchModels}
            hintSources={hintSources}
            hintSourcesLoading={hintSourcesLoading}
            hintSourcesError={hintSourcesError}
            isSaving={isSaving}
            configLoading={configLoading}
            configError={configError}
          />
        )}
      </header>
    </div>
  );
}

export default App;
