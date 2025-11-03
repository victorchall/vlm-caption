import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import ConfigForm from './components/ConfigForm';
import RunTab from './components/RunTab';
import UpdateNotification from './components/UpdateNotification';

function App() {
  const [apiPort, setApiPort] = useState(null);
  const [activeTab, setActiveTab] = useState('config');
  const [config, setConfig] = useState({
    base_url: '',
    model: '',
    api_key: '',
    system_prompt: '',
    prompts: [],
    retry_rules: [],
    base_directory: '',
    recursive: false,
    hint_sources: [],
    global_metadata_file: '',
    skip_if_txt_exists: false,
    concurrent_batch_size: 1
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
  
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState('');
  const [streamingOutput, setStreamingOutput] = useState('');
  const outputRef = useRef(null);

  const fetchModels = async (baseUrl) => {
    if (!baseUrl) {
      setModels([]);
      return;
    }

    setModelsLoading(true);
    setModelsError('');
    
    try {
      let url = baseUrl;
      if (!/^https?:\/\//i.test(url)) {
        url = 'http://' + url;
      }
      
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
          retry_rules: data.config.retry_rules || [],
          base_directory: data.config.base_directory || '',
          recursive: data.config.recursive || false,
          hint_sources: data.config.hint_sources || [],
          global_metadata_file: data.config.global_metadata_file || '',
          skip_if_txt_exists: data.config.skip_if_txt_exists || false,
          concurrent_batch_size: data.config.concurrent_batch_size || 1
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
            system_prompt: config.system_prompt,
            prompts: config.prompts,
            retry_rules: config.retry_rules,
            base_directory: config.base_directory,
            recursive: config.recursive,
            hint_sources: config.hint_sources,
            global_metadata_file: config.global_metadata_file,
            skip_if_txt_exists: config.skip_if_txt_exists,
            concurrent_batch_size: config.concurrent_batch_size
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

  const runCaptioningWithStreaming = () => {
    if (!apiPort) return;
    setIsRunning(true);
    setStreamingOutput('');
    setError('');

    const truncateOutput = (currentOutput, newData) => {
      const combined = currentOutput + newData;
      const MAX_CHARS = 10000;
      const TRUNCATE_TO = 8000;
      
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

    const eventSource = new EventSource(`http://localhost:${apiPort}/api/run`, {
      withCredentials: false
    });

    eventSource.onmessage = (event) => {
      const data = event.data;
      
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

  const stopCaptioning = async () => {
    if (!apiPort || !isRunning) return;

    try {
      const response = await fetch(`http://localhost:${apiPort}/api/stop`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (data.success) {
        if (window.currentEventSource) {
          window.currentEventSource.close();
        }

        setIsRunning(false);
        setError('');
        
        // Append cancellation message to streaming output
        if (streamingOutput) {
          setStreamingOutput(prev => prev + '\n🛑 Captioning was cancelled by user\n');
        }
      } else {
        setError(data.error || 'Failed to cancel captioning');
      }
    } catch (err) {
      setError('Failed to connect to the server');
    }
  };

  const handleRunCaptioning = async () => {
    // Save config before running
    await saveConfig();

    runCaptioningWithStreaming();
  };

return (
    <div className="App">
      <UpdateNotification />
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
          <RunTab
            apiPort={apiPort}
            configSuccess={configSuccess}
            isSaving={isSaving}
            onSaveConfig={saveConfig}
            isRunning={isRunning}
            error={error}
            streamingOutput={streamingOutput}
            outputRef={outputRef}
            onRunCaptioning={handleRunCaptioning}
            onStopCaptioning={stopCaptioning}
          />
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
