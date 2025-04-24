import React from 'react';
import AuthDemo from '../components/AuthDemo';

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <header className="bg-olas text-white py-4">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center">
            <h1 className="text-xl font-bold">OLAS MCP Documentation</h1>
            <nav>
              <ul className="flex space-x-4">
                <li><a href="#" className="hover:underline">Home</a></li>
                <li><a href="#" className="hover:underline">Components</a></li>
                <li><a href="#" className="hover:underline">API</a></li>
              </ul>
            </nav>
          </div>
        </div>
      </header>
      
      <main>
        <AuthDemo />
      </main>
      
      <footer className="bg-gray-100 py-6 mt-12">
        <div className="container mx-auto px-4 text-center text-gray-600 text-sm">
          <p>&copy; {new Date().getFullYear()} OLAS MCP. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}