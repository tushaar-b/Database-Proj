import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';

export default defineConfig(({ mode }) => {
  const projectRoot = fileURLToPath(new URL('../', import.meta.url));
  // Read only application settings; database credentials never enter the bundle.
  const appEnv = { ...loadEnv(mode, projectRoot, 'APP_'), ...process.env };
  const backendHost = appEnv.APP_HOST || '127.0.0.1';
  const backendPort = appEnv.APP_PORT || '8000';
  const proxy = {
    '/api': {
      target: `http://${backendHost}:${backendPort}`,
      // Preserve the browser Origin for backend CSRF origin validation.
      changeOrigin: false,
      rewrite: (path) => path.replace(/^\/api(?=\/|$)/, ''),
    },
  };
  return {
    plugins: [react()],
    server: {
      port: 5173,
      strictPort: true,
      host: '127.0.0.1',
      proxy,
      fs: {
        allow: [
          fileURLToPath(new URL('.', import.meta.url)),
          fileURLToPath(new URL('../video', import.meta.url)),
        ],
      },
    },
    preview: { host: '127.0.0.1', port: 5173, strictPort: true, proxy },
  };
});
