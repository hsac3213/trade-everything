import React, { useState } from 'react';
import Editor from '@monaco-editor/react';

const Script: React.FC = () => {
  const [code, setCode] = useState<string>('# Write your Python code here\nprint("Hello, World!")');
  const [output, setOutput] = useState<string>('');
  const [isRunning, setIsRunning] = useState<boolean>(false);

  const handleRunCode = async () => {
    setIsRunning(true);
    setOutput('Running...');

    try {
      // API 호출로 Python 코드 실행
      const response = await fetch('http://localhost:8000/api/execute-script', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code }),
      });

      const result = await response.json();
      
      if (response.ok) {
        setOutput(result.output || 'Code executed successfully');
      } else {
        setOutput(`Error: ${result.error || 'Failed to execute code'}`);
      }
    } catch (error) {
      setOutput(`Error: ${error instanceof Error ? error.message : 'Failed to connect to server'}`);
    } finally {
      setIsRunning(false);
    }
  };

  const handleClearOutput = () => {
    setOutput('');
  };

  return (
    <div className="flex flex-col gap-4 h-full">
      <div className="bg-gray-900 p-6 rounded-lg shadow-lg flex-1 flex flex-col">
        <h2 className="text-2xl font-bold mb-4 text-gray-100">Python Script Editor</h2>
        
        <div className="flex flex-col lg:flex-row gap-4 flex-1">
          {/* 코드 에디터 */}
          <div className="flex-1 flex flex-col">
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-gray-400">Code Editor</label>
              <div className="flex gap-2">
                <button
                  onClick={handleRunCode}
                  disabled={isRunning}
                  className={`px-4 py-2 text-sm font-medium rounded transition-colors ${
                    isRunning
                      ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                      : 'bg-green-600 hover:bg-green-700 text-white'
                  }`}
                >
                  {isRunning ? 'Running...' : 'Run Code'}
                </button>
                <button
                  onClick={handleClearOutput}
                  className="px-4 py-2 text-sm font-medium rounded bg-gray-700 hover:bg-gray-600 text-white transition-colors"
                >
                  Clear Output
                </button>
              </div>
            </div>
            <div className="flex-1 rounded-md overflow-hidden border border-gray-700">
              <Editor
                height="100%"
                defaultLanguage="python"
                value={code}
                onChange={(value) => setCode(value || '')}
                theme="vs-dark"
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  lineNumbers: 'on',
                  roundedSelection: false,
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  tabSize: 4,
                  wordWrap: 'on',
                }}
              />
            </div>
          </div>

          {/* 출력 영역 */}
          <div className="flex-1 flex flex-col">
            <label className="text-sm font-medium text-gray-400 mb-2">Output</label>
            <div className="flex-1 p-4 rounded-md bg-gray-800 border border-gray-700 text-gray-100 font-mono text-sm overflow-auto whitespace-pre-wrap">
              {output || 'Output will appear here...'}
            </div>
          </div>
        </div>

        {/* 정보 메시지 */}
        <div className="mt-4 p-3 bg-gray-800 rounded border border-gray-700">
          <p className="text-xs text-gray-400">
            <span className="font-semibold text-yellow-500">Note:</span> This feature requires a backend API endpoint at{' '}
            <code className="text-blue-400">http://localhost:8000/api/execute-script</code> to execute Python code.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Script;
