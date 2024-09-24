import '@mantine/core/styles.css';
import '@mantine/charts/styles.css';

import { MantineProvider } from '@mantine/core';
import { ModalsProvider } from '@mantine/modals';
import {
  QueryClient,
  QueryClientProvider
} from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom';

import './styles/main.css';
import { MainLayout } from './components/MainLayout';

const queryClient = new QueryClient()

export default function App() {


  return <MantineProvider defaultColorScheme='dark'>
    <ModalsProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<MainLayout page='rules' />} />
            <Route path="/rules" element={<MainLayout page='rules' />} />
            <Route path="/scoreboard" element={<MainLayout page='scoreboard' />} />
            <Route path="/scoreboard/team/:teamId" element={<MainLayout page='scoreboard-team' />} />
            <Route path="*" element={<MainLayout page='not-found' />} />
        </Routes>
      </BrowserRouter>
      </QueryClientProvider>
    </ModalsProvider>
  </MantineProvider> 
}

