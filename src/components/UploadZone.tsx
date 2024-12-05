import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { FaFilePdf, FaCloudUploadAlt } from 'react-icons/fa';

interface UploadZoneProps {
  onUpload: (file: File) => void;
}

export default function UploadZone({ onUpload }: UploadZoneProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{
    type: 'success' | 'error';
    message: string;
  } | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setIsUploading(true);
      onUpload(file);
    }
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: false
  });

  return (
    <div className="w-full max-w-2xl mx-auto p-6">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-xl p-12
          transition-all duration-200 ease-in-out
          flex flex-col items-center justify-center
          min-h-[300px]
          ${isDragActive 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
          }
          ${isUploading ? 'opacity-50 pointer-events-none' : 'cursor-pointer'}
        `}
      >
        <input {...getInputProps()} />
        
        {isDragActive ? (
          <FaCloudUploadAlt className="text-6xl text-blue-500 mb-4 animate-bounce" />
        ) : (
          <FaFilePdf className="text-6xl text-gray-400 mb-4" />
        )}
        
        <p className="text-xl font-medium text-gray-700 mb-2">
          {isDragActive
            ? 'Drop your PDF statement here'
            : 'Drag and drop your PDF statement here'}
        </p>
        <p className="text-sm text-gray-500">
          or click to select a file
        </p>
      </div>

      {uploadStatus && (
        <div className={`mt-4 p-4 rounded-lg ${
          uploadStatus.type === 'success' 
            ? 'bg-green-50 border border-green-200' 
            : 'bg-red-50 border border-red-200'
        }`}>
          <p className={`text-center ${
            uploadStatus.type === 'success' ? 'text-green-700' : 'text-red-700'
          }`}>
            {uploadStatus.message}
          </p>
        </div>
      )}
    </div>
  );
} 