import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { hostname: 'image.tmdb.org' },
      { hostname: 'i.ytimg.com' },
      { hostname: 'img.youtube.com' },
      { hostname: 'www.themoviedb.org' },
      { hostname: 'images.unsplash.com' },
    ],
  },
};

export default nextConfig;