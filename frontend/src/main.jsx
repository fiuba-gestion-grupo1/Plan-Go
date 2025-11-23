import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

if (typeof window !== "undefined") {
  window.alert = () => {};
  window.prompt = () => null;
}

createRoot(document.getElementById('root')).render(<App />)
