/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverActions: {
      bodySizeLimit: '10mb' // Adjust this value based on your needs
    }
  }
}

module.exports = nextConfig 