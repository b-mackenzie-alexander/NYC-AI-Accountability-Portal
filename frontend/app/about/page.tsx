"use client";
import React from "react";

export default function AboutPage() {
  return (
    <main className="flex flex-col items-center justify-center min-h-screen bg-gray-50 px-4">
      <h1 className="text-2xl font-bold mb-4 text-gray-800">About NYC AI Accountability Portal</h1>
      <div className="max-w-2xl text-gray-700 text-lg bg-white rounded-xl shadow p-6">
        <p>
          The NYC AI Accountability Portal helps the public track and understand how New York City agencies use AI and automated decision systems. 
          It extracts and organizes official disclosures, highlights gaps and bias signals, and cross-references public data to surface potential disparities. 
          Anyone can search, explore, and file anonymous complaints about AI-driven decisions that impact city services.
        </p>
      </div>
    </main>
  );
}