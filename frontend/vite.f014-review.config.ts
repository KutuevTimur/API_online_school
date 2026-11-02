import { mergeConfig } from 'vite';
import base from './vite.config.ts';
export default mergeConfig(base, {
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8021',
        rewrite: (path: string) => path.replace(/^\/api/, ''),
      },
    },
  },
});
