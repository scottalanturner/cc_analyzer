'use client';

import { useEffect, useState } from 'react';
import UploadZone from '@/components/UploadZone';
import { WebSocketClient } from '@/utils/websocket';

export default function Home() {
  const [wsClient, setWsClient] = useState<WebSocketClient | null>(null);

  useEffect(() => {
    const client = new WebSocketClient(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3001');
    client.connect();
    setWsClient(client);

    return () => {
      client.close();
    };
  }, []);

  const handleUpload = async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      // Notify WebSocket about upload start
      wsClient?.send({ type: 'upload_start', filename: file.name });

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Upload failed');
      }

      // Notify WebSocket about upload completion
      wsClient?.send({ type: 'upload_complete', filename: file.name });

    } catch (error) {
      console.error('Upload error:', error);
      // Notify WebSocket about upload error
      wsClient?.send({ 
        type: 'upload_error', 
        filename: file.name, 
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      <main className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold text-center text-gray-800 mb-4">
            Credit Card Statement Analysis
          </h1>
          <p className="text-center text-gray-600 mb-12">
            Upload your credit card statement to get insights and recommendations
          </p>
          <UploadZone onUpload={handleUpload} />
        </div>
      </main>
    </div>
  );
} 