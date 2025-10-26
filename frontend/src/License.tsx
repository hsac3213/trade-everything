import React from 'react';

const License: React.FC = () => {
  return (
    <div className="bg-gray-800 rounded-lg p-8 shadow-lg">
      <h2 className="text-2xl font-bold mb-6">License</h2>
      <div className="space-y-6">
        <div className="bg-gray-700 rounded-lg p-6">
          <h3 className="text-xl font-semibold mb-4">MIT License</h3>
          <p className="text-gray-300 mb-4">
            Copyright (c) 2025 Trade Everything
          </p>
          <div className="bg-gray-800 rounded p-4 text-sm text-gray-300 font-mono">
            <p className="mb-2">
              Permission is hereby granted, free of charge, to any person obtaining a copy
              of this software and associated documentation files (the "Software"), to deal
              in the Software without restriction, including without limitation the rights
              to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
              copies of the Software, and to permit persons to whom the Software is
              furnished to do so, subject to the following conditions:
            </p>
            <p className="mb-2">
              The above copyright notice and this permission notice shall be included in all
              copies or substantial portions of the Software.
            </p>
            <p>
              THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
              IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
              FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
              AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
              LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
              OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
              SOFTWARE.
            </p>
          </div>
        </div>
        
        <div className="bg-gray-700 rounded-lg p-6">
          <h3 className="text-xl font-semibold mb-4">Third-Party Licenses</h3>
          <div className="space-y-3 text-sm">
            <div>
              <p className="font-semibold text-white">React</p>
              <p className="text-gray-400">MIT License</p>
            </div>
            <div>
              <p className="font-semibold text-white">TypeScript</p>
              <p className="text-gray-400">Apache License 2.0</p>
            </div>
            <div>
              <p className="font-semibold text-white">TailwindCSS</p>
              <p className="text-gray-400">MIT License</p>
            </div>
            <div>
              <p className="font-semibold text-white">FastAPI</p>
              <p className="text-gray-400">MIT License</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default License;
