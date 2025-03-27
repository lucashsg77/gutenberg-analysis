/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    images: {
      remotePatterns: [
        {
          protocol: 'https',
          hostname: 'www.gutenberg.org',
        },
        {
          protocol: 'https',
          hostname: '**',
        },
      ],
    },
    transpilePackages: ['react-force-graph'],
    env: {
      NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    },
  }
  
  module.exports = nextConfig