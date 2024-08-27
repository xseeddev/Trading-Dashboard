import React, { Dispatch, SetStateAction, useEffect } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router';
import bcrypt from 'bcryptjs'
import { SHA256 } from 'crypto-js';

type LoginFormValues = {
  password: string;
};

function LoginPage({setLoggedIn,loggedIn}:{setLoggedIn:Dispatch<SetStateAction<null|string>>,loggedIn:null|string}) {
  
  const { register, handleSubmit, formState: { errors } } = useForm<LoginFormValues>();
  const navigate = useNavigate();

  useEffect(()=>{
    if(loggedIn){
      navigate('/')
    }
  },[setLoggedIn,loggedIn,navigate])

  const onSubmit: SubmitHandler<LoginFormValues> = (data) => {
    toast.loading('Logging In');
    const hashedPassword = SHA256(data.password).toString();
    fetch('http://127.0.0.1:5000/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({password:hashedPassword}),
    })
      .then(response => response.json())
      .then(data => {
        toast.dismiss();
        if(data.success){
          localStorage.setItem('token',data.token);
          setLoggedIn(data.token);
          navigate('/')
          toast.success('Logged In Successfully');
          return;
        }
        toast.error('Invalid Password');
        
      })
      .catch((error) => {
        console.error('Error:', error);
      });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-md">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign In
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="rounded-md shadow-sm -space-y-px">
            
            <div>
              <label htmlFor="password" className="sr-only">Password</label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                {...register("password", { required: "Password is required"})}
              />
              {errors.password && <p className="mt-2 text-sm text-red-600">{errors.password.message}</p>}
            </div>
          </div>

         

          <div>
            <button
              type="submit"
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Sign in
            </button>
          </div>

        </form>
      </div>
    </div>
  );
}

export default LoginPage;