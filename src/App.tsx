import React, { useState, useEffect } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { Route, Routes, useNavigate } from 'react-router';
import LoginPage from './pages/Login';
import Dashboard from './pages/Dashboard';



function App() {
  
  const [loggedIn, setLoggedIn] = useState<null | string>(null);
  const token = localStorage.getItem('token');
  const navigate = useNavigate();
  useEffect(()=>{
    if(token){
      setLoggedIn(token);
    }
    if(!loggedIn){
      navigate('/login')
    }
  },[navigate,token])

  return (
    <div className="min-h-screen bg-gray-100">
      {
        loggedIn && <div className='w-full flex justify-center'>
        <button onClick={()=>{
          localStorage.removeItem('token');
          setLoggedIn(null);
          navigate('/login')
        }} className='bg-blue-500 text-white px-3 py-2 rounded-xl mt-2 -mb-4'>Log out</button>
      </div>
      }
      <Routes>
        <Route element={<LoginPage setLoggedIn={setLoggedIn} loggedIn={loggedIn}/>} path='/login'/>
        
        {
          loggedIn && <Route element={<Dashboard setLoggedIn={setLoggedIn}/>} path='/'/>
        }
        

    </Routes>
    </div>
  );
}

export default App;