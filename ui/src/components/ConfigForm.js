import React, { useRef } from 'react';

const ConfigForm = ({
  config,
  onConfigChange,
  onSave,
  models,
  modelsLoading,
  modelsError,
  onFetchModels,
  hintSources,
  hintSourcesLoading,
  hintSourcesError,
  configLoading,
  configError
}) => {
  const directoryInputRef = useRef(null);
  const metadataFileInputRef = useRef(null);

  const handleDirectorySelect = (e) => {
    if (e.target.files.length > 0) {
      const file = e.target.files[0];
      const path = file.path;
      const lastSeparatorIndex = Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\'));
      const directoryPath = path.substring(0, lastSeparatorIndex);
      onConfigChange('base_directory', directoryPath);
    }
  };

  const handleExampleDirectorySelect = (e) => {
    if (e.target.files.length > 0) {
      const file = e.target.files[0];
      const path = file.path;
      const lastSeparatorIndex = Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\'));
      const directoryPath = path.substring(0, lastSeparatorIndex);
      onConfigChange('example_directory', directoryPath);
    }
  };

  const handleMetadataFileSelect = (e) => {
    if (e.target.files.length > 0) {
      const file = e.target.files[0];
      const path = file.path;
      onConfigChange('global_metadata_file', path);
    }
  };

  const handlePromptChange = (index, value) => {
    const newPrompts = [...config.prompts];
    newPrompts[index] = value;
    onConfigChange('prompts', newPrompts);
  };

  const addPrompt = () => {
    onConfigChange('prompts', [...config.prompts, '']);
  };

  const removePrompt = (index) => {
    const newPrompts = config.prompts.filter((_, i) => i !== index);
    onConfigChange('prompts', newPrompts);
  };

  // Retry Rules handlers
  const handleRetryRuleChange = (ruleIndex, field, value) => {
    const newRetryRules = [...config.retry_rules];
    newRetryRules[ruleIndex] = { ...newRetryRules[ruleIndex], [field]: value };
    onConfigChange('retry_rules', newRetryRules);
  };

  const handleRetryRulePhraseChange = (ruleIndex, phraseIndex, value) => {
    const newRetryRules = [...config.retry_rules];
    const newPhrases = [...newRetryRules[ruleIndex].phrases];
    newPhrases[phraseIndex] = value;
    newRetryRules[ruleIndex] = { ...newRetryRules[ruleIndex], phrases: newPhrases };
    onConfigChange('retry_rules', newRetryRules);
  };

  const addRetryRule = () => {
    const newRule = {
      rule_name: '',
      phrases: [''],
      rejection_note: ''
    };
    onConfigChange('retry_rules', [...config.retry_rules, newRule]);
  };

  const removeRetryRule = (ruleIndex) => {
    const newRetryRules = config.retry_rules.filter((_, i) => i !== ruleIndex);
    onConfigChange('retry_rules', newRetryRules);
  };

  const addRetryRulePhrase = (ruleIndex) => {
    const newRetryRules = [...config.retry_rules];
    newRetryRules[ruleIndex] = { 
      ...newRetryRules[ruleIndex], 
      phrases: [...newRetryRules[ruleIndex].phrases, ''] 
    };
    onConfigChange('retry_rules', newRetryRules);
  };

  const removeRetryRulePhrase = (ruleIndex, phraseIndex) => {
    const newRetryRules = [...config.retry_rules];
    const newPhrases = newRetryRules[ruleIndex].phrases.filter((_, i) => i !== phraseIndex);
    newRetryRules[ruleIndex] = { ...newRetryRules[ruleIndex], phrases: newPhrases };
    onConfigChange('retry_rules', newRetryRules);
  };

  const handleConcurrentBatchSizeChange = (e) => {
    const value = parseInt(e.target.value);
    if (value >= 1 && value <= 16) {
      onConfigChange('concurrent_batch_size', value);
    }
  };

  if (configLoading) return <p>Loading configuration...</p>;

  return (
    <div className="tab-content">
      {configError && (
        <div className="error">
          <h3>Error:</h3>
          <pre>{configError}</pre>
        </div>
      )}

      <form onSubmit={(e) => { e.preventDefault(); onSave(); }}>
        <div className="form-group side-by-side">
          <div>
            <label htmlFor="base_url">Base URL</label>
            <input
              type="text"
              id="base_url"
              value={config.base_url}
              onChange={(e) => onConfigChange('base_url', e.target.value)}
              placeholder="e.g., http://localhost:1234/v1"
            />
            <span className="description-text">Copy from LM Studio developer tab or llama.cpp console output. Make sure /v1 at end is present, ex. http://127.0.0.1:8080/v1</span>
          </div>

          <div>
            <label htmlFor="model">Model</label>
            <div className="model-selection">
              <select
                id="model"
                value={config.model}
                onChange={(e) => onConfigChange('model', e.target.value)}
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
                onClick={() => onFetchModels(config.base_url)}
                disabled={modelsLoading || !config.base_url}
                className="reload-button"
              >
                {modelsLoading ? '...' : 'Refresh'}
              </button>
            </div>
            {modelsError && <p className="error-text">{modelsError}</p>}
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="concurrent_batch_size">Concurrent Batch Size</label>
          <input
            type="number"
            id="concurrent_batch_size"
            min="1"
            max="64"
            value={config.concurrent_batch_size || 4}
            onChange={handleConcurrentBatchSizeChange}
            style={{ width: '100px' }}
          />
          <span className="description-text">Batch concurrency if using API with support (i.e. "llama-server -np n"), otherwise leave 1</span>
        </div>

        <div className="form-group side-by-side api-key-directory">
          <div>
            <label htmlFor="api_key">API Key</label>
            <input
              type="password"
              id="api_key"
              value={config.api_key}
              onChange={(e) => onConfigChange('api_key', e.target.value)}
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
                  onChange={(e) => onConfigChange('recursive', e.target.checked)}
                />
              </div>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <label htmlFor="skip_if_txt_exists" style={{ marginRight: '40px' }}>Skip image if .txt exists</label>
                <input
                  type="checkbox"
                  id="skip_if_txt_exists"
                  className="skip-if-txt-exists-checkbox"
                  checked={config.skip_if_txt_exists}
                  onChange={(e) => onConfigChange('skip_if_txt_exists', e.target.checked)}
                />
              </div>
            </div>
            <div style={{ display: 'flex' }}>
              <input
                type="text"
                id="base_directory"
                value={config.base_directory}
                onChange={(e) => onConfigChange('base_directory', e.target.value)}
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
              onChange={(e) => onConfigChange('global_metadata_file', e.target.value)}
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
            onChange={(e) => onConfigChange('system_prompt', e.target.value)}
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

        <div className="form-group">
          <label>Retry Rules</label>
          <span className="description-text">Define rules to detect unwanted phrases or words in the final summary and ask the model to redo the summary if any are detected.</span>
          {config.retry_rules.map((rule, ruleIndex) => (
            <div key={ruleIndex} className="retry-rule-item">
              <div className="retry-rule-header">
                <label>Rule name:</label>
                <input
                  type="text"
                  value={rule.rule_name}
                  onChange={(e) => handleRetryRuleChange(ruleIndex, 'rule_name', e.target.value)}
                  placeholder={`Rule Name ${ruleIndex + 1}`}
                  className="retry-rule-name"
                />
                <button
                  type="button"
                  onClick={() => removeRetryRule(ruleIndex)}
                  className="remove-prompt-button"
                >
                  &times;
                </button>
              </div>
              
              <div className="retry-rule-phrases">
                <label>Phrases to detect:</label>
                {rule.phrases.map((phrase, phraseIndex) => (
                  <div key={phraseIndex} className="retry-rule-phrase-item">
                    <input
                      type="text"
                      value={phrase}
                      onChange={(e) => handleRetryRulePhraseChange(ruleIndex, phraseIndex, e.target.value)}
                      placeholder={`Phrase ${phraseIndex + 1}`}
                      className="retry-rule-phrase"
                    />
                    <button
                      type="button"
                      onClick={() => removeRetryRulePhrase(ruleIndex, phraseIndex)}
                      className="remove-prompt-button"
                    >
                      &times;
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={() => addRetryRulePhrase(ruleIndex)}
                  className="add-prompt-button"
                  style={{ fontSize: '12px', padding: '4px 8px', marginTop: '5px' }}
                >
                  Add Phrase
                </button>
              </div>

              <div className="retry-rule-note">
                <label>Rejection Note:</label>
                <div class="hint-source-description">Use [phrases] to include the rejected phrases</div>
                <textarea
                  value={rule.rejection_note}
                  onChange={(e) => handleRetryRuleChange(ruleIndex, 'rejection_note', e.target.value)}
                  placeholder="Message to send when retrying (use [phrases] to insert the detected phrases)"
                  rows="2"
                  className="retry-rule-rejection-note"
                />
              </div>
            </div>
          ))}
          <button
            type="button"
            onClick={addRetryRule}
            className="add-prompt-button"
          >
            Add Retry Rule
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
                        onConfigChange('hint_sources', newHintSources);
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
  );
};

export default ConfigForm;
