import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

// === Kill-switch de pop-ups nativos ===
if (typeof window !== "undefined") {
  window.alert = () => {};
  window.confirm = () => false;
  window.prompt = () => null;
}

createRoot(document.getElementById('root')).render(<App />)
