import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App.jsx'
import PrivacyPolicy from './pages/PrivacyPolicy.jsx'
import Terms from './pages/Terms.jsx'
import { CharactersLayout } from './pages/characters/shared.jsx'
import Characters from './pages/characters/Characters.jsx'
import Protagonists from './pages/characters/Protagonists.jsx'
import SideCharacters from './pages/characters/SideCharacters.jsx'
import Teams from './pages/characters/Teams.jsx'
import CharacterProfile from './pages/characters/CharacterProfile.jsx'
import './index.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/privacy" element={<PrivacyPolicy />} />
        <Route path="/terms" element={<Terms />} />
        <Route path="/characters" element={<CharactersLayout />}>
          <Route index element={<Characters />} />
          <Route path="protagonists" element={<Protagonists />} />
          <Route path="side-characters" element={<SideCharacters />} />
          <Route path="teams" element={<Teams />} />
          <Route path="profile/:slug" element={<CharacterProfile />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>
)
