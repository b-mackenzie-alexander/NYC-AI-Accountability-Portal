"use client";
import React, { useState } from "react";

const ADMIN_USERNAME = "admin";
const ADMIN_PASSWORD = "password123"; // Change this in production!

export default function AdminPage() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [error, setError] = useState("");
  
  function handleLogin(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const username = form.username.value;
    const password = form.password.value;
    if (username === ADMIN_USERNAME && password === ADMIN_PASSWORD) {
      setLoggedIn(true);
      setError("");
    } else {
      setError("Invalid credentials");
    }
  }

  if (!loggedIn) {
    return (
      <main className="flex flex-col items-center justify-center min-h-screen bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white rounded-xl shadow p-6">
          <h1 className="text-xl font-bold mb-4 text-gray-800">Admin Login</h1>
          <form className="flex flex-col gap-4" onSubmit={handleLogin}>
            <input 
              name="username" 
              placeholder="Username" 
              className="border rounded px-3 py-2 text-gray-900 placeholder:text-gray-400" 
              required 
            />
            <input 
              name="password" 
              type="password" 
              placeholder="Password" 
              className="border rounded px-3 py-2 text-gray-900 placeholder:text-gray-400" 
              required 
            />
            {error && <div className="text-red-600 text-sm">{error}</div>}
            <button type="submit" className="bg-blue-600 text-white rounded px-6 py-2 font-semibold hover:bg-blue-700 transition">
              Login
            </button>
          </form>
        </div>
      </main>
    );
  }

  // Admin content goes here
  return (
    <main className="flex flex-col items-center justify-center min-h-screen bg-gray-50 px-4">
      <div className="max-w-2xl w-full bg-white rounded-xl shadow p-6">
        <h1 className="text-xl font-bold mb-4 text-gray-800">Admin Dashboard</h1>
        <p className="mb-4 text-gray-700">Welcome, admin! You can now make changes.</p>
        {/* Add admin features/components here */}
      </div>
    </main>
  );
}