import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './layouts/Layout';
import Home from './pages/Home';
import Report from './pages/Report';
import ItemDetail from './pages/ItemDetail';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path='/' element={<Layout />}>
          <Route index element={<Home />} />
          <Route path='report' element={<Report />} />
          <Route path='item/:id' element={<ItemDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
