/**
 * ModelSelector Component
 * Dropdown for selecting LLM model with vendor grouping and type badges
 */

import React from 'react';
import { ModelInfo } from '../types/chat';

interface ModelSelectorProps {
  models: ModelInfo[];
  selectedModel: string;
  onModelChange: (model: string) => void;
  disabled?: boolean;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({
  models,
  selectedModel,
  onModelChange,
  disabled = false,
}) => {
  // Group models by vendor
  const groupedModels = models.reduce((acc, model) => {
    if (!acc[model.vendor]) {
      acc[model.vendor] = [];
    }
    acc[model.vendor].push(model);
    return acc;
  }, {} as Record<string, ModelInfo[]>);

  // Vendor display names
  const vendorNames: Record<string, string> = {
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    ollama: 'Ollama (Local)',
  };

  // Get badge color based on type
  const getTypeBadge = (type: string) => {
    if (type === 'reasoning') {
      return '🧠';
    }
    return '';
  };

  // Get selected model info for display
  const selectedModelInfo = models.find(m => m.id === selectedModel);

  return (
    <div className="flex items-center gap-3">
      <label htmlFor="model-select" className="text-sm font-medium text-gray-700 whitespace-nowrap">
        Model:
      </label>
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <select
            id="model-select"
            value={selectedModel}
            onChange={(e) => onModelChange(e.target.value)}
            disabled={disabled}
            className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed min-w-[250px]"
          >
            {Object.entries(groupedModels).map(([vendor, vendorModels]) => (
              <optgroup key={vendor} label={vendorNames[vendor] || vendor}>
                {vendorModels.map((model) => (
                  <option
                    key={model.id}
                    value={model.id}
                    disabled={!model.available}
                    title={model.unavailable_reason || undefined}
                  >
                    {model.id} {model.type === 'reasoning' ? '(Reasoning)' : ''} {!model.available ? '⚠️ Unavailable' : ''}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
          {selectedModelInfo && (
            <div className="flex items-center gap-1">
              {selectedModelInfo.type === 'reasoning' && (
                <span className="text-lg" title="Reasoning Model">
                  {getTypeBadge('reasoning')}
                </span>
              )}
              <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                selectedModelInfo.available
                  ? 'bg-green-100 text-green-700'
                  : 'bg-red-100 text-red-700'
              }`}>
                {vendorNames[selectedModelInfo.vendor]}
              </span>
              {selectedModelInfo.available && (
                <span className="text-xs px-2 py-1 rounded-full bg-green-100 text-green-700">
                  ✓ Available
                </span>
              )}
            </div>
          )}
        </div>
        {selectedModelInfo && !selectedModelInfo.available && (
          <div className="text-xs text-red-600 flex items-center gap-1">
            <span>⚠️</span>
            <span>{selectedModelInfo.unavailable_reason || 'Model unavailable'}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ModelSelector;
