import React, { useState, useEffect } from 'react';
import './App.css';
import ConfigForm from './components/ConfigForm';
import RunTab from './components/RunTab';

function App() {
  const [apiPort, setApiPort] = useState(null);
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
            system_prompt: config.system_prompt,
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

  return (
    <div className="App">
      <header className="App-header">
        <h1>VLM Caption</h1>
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

        {activeTab === 'run' && (
          <RunTab
            apiPort={apiPort}
            configSuccess={configSuccess}
            isSaving={isSaving}
            onSaveConfig={saveConfig}
          />
        )}

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
