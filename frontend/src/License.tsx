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
          <p className="text-gray-300 mb-4">
            This project uses various open-source dependencies. Below is a summary of the licenses:
          </p>
          
          <div className="space-y-4">
            <div className="bg-gray-800 rounded p-4">
              <h4 className="font-semibold text-white mb-2">MIT License (174 packages)</h4>
              <p className="text-gray-400 text-sm mb-2">
                Most permissive license allowing commercial use with minimal restrictions.
              </p>
              <p className="text-gray-400 text-xs">
                Includes: React, Vite, ESLint, TailwindCSS, Monaco Editor, React Hot Toast, and many more...
              </p>
            </div>

            <div className="bg-gray-800 rounded p-4">
              <h4 className="font-semibold text-white mb-2">Apache-2.0 (15 packages)</h4>
              <p className="text-gray-400 text-sm mb-2">
                Permissive license with patent grant protection.
              </p>
              <p className="text-gray-400 text-xs">
                Includes: TypeScript, Lightweight Charts, ESLint Core packages, baseline-browser-mapping
              </p>
            </div>

            <div className="bg-gray-800 rounded p-4">
              <h4 className="font-semibold text-white mb-2">ISC License (15 packages)</h4>
              <p className="text-gray-400 text-sm mb-2">
                Functionally equivalent to MIT license.
              </p>
              <p className="text-gray-400 text-xs">
                Includes: fastq, graceful-fs, glob-parent, picocolors, semver, yallist
              </p>
            </div>

            <div className="bg-gray-800 rounded p-4">
              <h4 className="font-semibold text-white mb-2">MPL-2.0 (3 packages)</h4>
              <p className="text-gray-400 text-sm mb-2">
                Weak copyleft license. Used as library without modifications.
              </p>
              <p className="text-gray-400 text-xs">
                Includes: lightningcss, lightningcss-linux-x64-gnu, lightningcss-linux-x64-musl
              </p>
            </div>

            <div className="bg-gray-800 rounded p-4">
              <h4 className="font-semibold text-white mb-2">BSD Licenses (8 packages)</h4>
              <p className="text-gray-400 text-sm mb-2">
                BSD-2-Clause, BSD-3-Clause: Permissive open source licenses.
              </p>
              <p className="text-gray-400 text-xs">
                Includes: eslint-scope, espree, esquery, esrecurse, estraverse, esutils, source-map-js, uri-js
              </p>
            </div>

            <div className="bg-gray-800 rounded p-4">
              <h4 className="font-semibold text-white mb-2">Other Licenses</h4>
              <ul className="text-gray-400 text-xs space-y-1">
                <li>• Python-2.0 (1): argparse</li>
                <li>• CC-BY-4.0 (1): caniuse-lite (data license)</li>
                <li>• 0BSD (1): tslib</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="bg-gray-700 rounded-lg p-6">
          <h3 className="text-xl font-semibold mb-4">Special Attributions</h3>
          <div className="space-y-3 text-sm">
            <div className="bg-gray-800 rounded p-4">
              <p className="font-semibold text-white mb-2">TradingView Lightweight Charts™</p>
              <p className="text-gray-400">
                Copyright © 2025 TradingView, Inc.
              </p>
              <p className="text-gray-400 text-xs mt-2">
                Apache License 2.0 | <a href="https://www.tradingview.com/" target="_blank" rel="noopener noreferrer" className="underline">https://www.tradingview.com/</a>
              </p>
            </div>
            <div className="bg-gray-800 rounded p-4">
              <p className="font-semibold text-white mb-2">SimpleWebAuthn</p>
              <p className="text-gray-400 text-xs">
                MIT License | Passkey authentication library
              </p>
            </div>
          </div>
        </div>

        <div className="bg-gray-700 rounded-lg p-6">
          <h3 className="text-xl font-semibold mb-4">License Compliance</h3>
          <div className="space-y-2 text-sm text-gray-300">
            <p>✅ All dependencies are compatible with commercial distribution</p>
            <p>✅ Apache-2.0 and MPL-2.0 license texts preserved in package directories</p>
            <p>✅ Full third-party license information available in distribution</p>
            <p>✅ No GPL or AGPL dependencies that would require source code disclosure</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default License;
