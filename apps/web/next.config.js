/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async rewrites() {
    // API_PROXY_TARGET is server-only (not exposed to browser)
    // Used for Next.js server-side proxy to FastAPI
    const target = process.env.API_PROXY_TARGET || "http://localhost:8000";
    return [
      {
        source: "/landing",
        destination: "/landing.html",
      },
      {
        source: "/veriops",
        destination: "/veriops.html",
      },
      {
        source: "/api/:path*",
        destination: `${target}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
