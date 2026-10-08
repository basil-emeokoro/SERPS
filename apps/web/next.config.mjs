const publicApi = process.env.NEXT_PUBLIC_API_BASE_URL;
if (process.env.VERCEL === '1') {
  const url = publicApi ? new URL(publicApi) : null;
  if (!url || url.protocol !== 'https:' || url.username || url.password || url.search || url.hash) {
    throw new Error('Set NEXT_PUBLIC_API_BASE_URL to the public HTTPS API origin without credentials.');
  }
}
const nextConfig = {
  reactStrictMode: true,
  async headers() {
    return [{ source: '/:path*', headers: [
      { key: 'X-Content-Type-Options', value: 'nosniff' },
      { key: 'Referrer-Policy', value: 'no-referrer' },
      { key: 'X-Frame-Options', value: 'DENY' },
    ] }];
  },
};
export default nextConfig;
