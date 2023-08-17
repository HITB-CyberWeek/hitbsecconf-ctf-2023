/** @type {import('next').NextConfig} */
const nextConfig = {
    trailingSlash: true,

    // See https://github.com/vercel/next.js/issues/44273
    webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
        config.externals.push({
            'utf-8-validate': 'commonjs utf-8-validate',
            'bufferutil': 'commonjs bufferutil',
            'encoding': 'commonjs encoding',
        });
        return config;
    },

    async rewrites() {
        return [
            {
                source: "/api/:path*",
                destination: "http://127.0.0.1:3001/:path*",
            },
        ];
    },
}

module.exports = nextConfig
