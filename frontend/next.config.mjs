/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // No output: 'export' — preserves SSR/ISR capability for MN-004+
  // No env vars required at build time for the placeholder shell
};

export default nextConfig;
