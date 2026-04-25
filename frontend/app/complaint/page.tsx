"use client";
import React, { useState } from "react";

// TODO: Replace with your actual backend URL from environment variable
// For local development: http://localhost:8000
// For production: https://your-backend.railway.app
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ComplaintPage() {
  const [submitted, setSubmitted] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    const form = e.currentTarget;
    const data = {
      agency: form.agency.value,
      system_name: form.system.value, // Changed to match backend schema
      affected_service: form.service.value, // Changed to match backend schema
      incident_description: form.description.value, // Changed to match backend schema
    };

    try {
      // Call your FastAPI backend endpoint
      const res = await fetch(`${API_BASE_URL}/complaints`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (res.ok) {
        const result = await res.json();
        setToken(result.token);
        setSubmitted(true);
      } else {
        const errorData = await res.json().catch(() => ({}));
        setError(errorData.detail || `Failed to submit: ${res.status}`);
      }
    } catch (err) {
      console.error("Submission error:", err);
      setError("Unable to connect to server. Please try again later.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex flex-col items-center justify-center min-h-screen bg-gray-50 px-4">
      <div className="max-w-2xl w-full">
        <h1 className="text-2xl font-bold mb-2 text-gray-800">File a Complaint</h1>
        <p className="text-gray-600 mb-6">
          We do NOT collect: name, email, or IP address. Your privacy is protected.
        </p>
        
        <div className="bg-white rounded-xl shadow p-6 w-full">
          {submitted ? (
            <div className="text-center">
              <div className="mb-4 text-green-600 text-5xl">✓</div>
              <h2 className="text-xl font-semibold text-green-700 mb-3">
                Thank you for your submission!
              </h2>
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <p className="text-sm text-gray-600 mb-2">Your complaint token:</p>
                <code className="text-lg font-mono bg-white px-3 py-2 rounded border">
                  {token}
                </code>
              </div>
              <p className="text-sm text-gray-600">
                Save this token to check your complaint status at{' '}
                <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">/complaint/status</code>
              </p>
              <button
                onClick={() => {
                  setSubmitted(false);
                  setToken(null);
                }}
                className="mt-6 text-blue-600 hover:text-blue-800 text-sm"
              >
                ← Submit another complaint
              </button>
            </div>
          ) : (
            <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
              <label className="flex flex-col">
                <span className="font-medium mb-1 text-gray-800">Agency <span className="text-red-500">*</span></span>
                <select 
                  name="agency" 
                  required 
                  className="border rounded-lg px-3 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select an agency</option>
                  <option value="ACS">Administration for Children's Services (ACS)</option>
                  <option value="NYPD">NY Police Department (NYPD)</option>
                  <option value="DHS">Department of Homeless Services (DHS)</option>
                  <option value="HRA">Human Resources Administration (HRA)</option>
                  <option value="Other">Other Agency</option>
                </select>
              </label>

              <label className="flex flex-col">
                <span className="font-medium mb-1 text-gray-800">AI System Name <span className="text-gray-400 text-sm">(optional)</span></span>
                <input 
                  name="system" 
                  className="border rounded-lg px-3 py-2 text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-blue-500" 
                  placeholder="e.g., Severe Harm Predictive Risk Model, Family Map, etc."
                />
              </label>

              <label className="flex flex-col">
                <span className="font-medium mb-1 text-gray-800">Affected Service <span className="text-gray-400 text-sm">(optional)</span></span>
                <input 
                  name="service" 
                  className="border rounded-lg px-3 py-2 text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-blue-500" 
                  placeholder="e.g., Child welfare investigation, Foster care placement, Benefits determination"
                />
              </label>

              <label className="flex flex-col">
                <span className="font-medium mb-1 text-gray-800">
                  Incident Description <span className="text-red-500">*</span>
                </span>
                <textarea 
                  name="description" 
                  required 
                  className="border rounded-lg px-3 py-2 text-gray-900 placeholder:text-gray-400 min-h-[120px] focus:ring-2 focus:ring-blue-500" 
                  placeholder="Describe what happened. Do not include personal identifying information like your name, address, or case number."
                />
                <p className="text-xs text-gray-500 mt-1">
                  Please do not include: name, address, phone number, email, or case numbers
                </p>
              </label>

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-red-700 text-sm">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 text-white rounded-lg px-6 py-2.5 font-semibold hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Submitting..." : "Submit Anonymous Complaint"}
              </button>

              <p className="text-xs text-gray-500 text-center mt-2">
                This complaint is anonymous. No personal information is stored or tracked.
              </p>
            </form>
          )}
        </div>
      </div>
    </main>
  );
}