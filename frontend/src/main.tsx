import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider } from 'react-router';
import '@mantine/core/styles.css';
import '@mantine/dates/styles.css';
import './app/fonts.css';
import './app/styles.css';
import { Providers } from './app/providers';
import { router } from './app/router';
import { cssVariables } from './app/theme';
for (const [key, value] of Object.entries(cssVariables))
  document.documentElement.style.setProperty(key, value);
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Providers>
      <RouterProvider router={router} />
    </Providers>
  </React.StrictMode>,
);
