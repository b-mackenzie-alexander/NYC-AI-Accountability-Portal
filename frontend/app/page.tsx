"use client";
import React from "react";

export default function LandingPage() {
  return (
    <main className="flex flex-col items-center justify-center min-h-screen bg-gray-50 px-4">
      <h1 className="text-4xl font-bold mb-4 text-gray-900 text-center">
        Welcome to the NYC AI Accountability Portal
      </h1>
      <p className="text-lg text-gray-700 mb-8 text-center max-w-2xl">
        Track, explore, and understand how New York City agencies use AI and automated decision systems. 
        Search disclosures, spot bias signals, and file anonymous complaints about AI-driven decisions that impact city services.
      </p>
      <div className="flex gap-4">
        <a
          href="/agencies"
          className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
        >
          Explore Agencies
        </a>
        <a
          href="/complaint"
          className="bg-gray-200 text-gray-800 px-6 py-3 rounded-lg font-semibold hover:bg-gray-300 transition"
        >
          File a Complaint
        </a>
        <a
          href="/about"
          className="bg-white border border-gray-300 text-gray-800 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition"
        >
          Learn More
        </a>
      </div>
    </main>
  );
}