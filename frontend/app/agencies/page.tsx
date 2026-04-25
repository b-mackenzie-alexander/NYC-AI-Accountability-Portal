"use client";
import React, { useEffect, useState } from "react";
import Link from "next/link";
import { AgencySummary, getAgencySummaries } from "@/lib/api";

export default function AgenciesPage() {
  const [agencies, setAgencies] = useState<AgencySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchAgencies();
  }, []);

  async function fetchAgencies() {
    try {
      setLoading(true);
      setError(null);
      
      const data = await getAgencySummaries();
      setAgencies(data);
    } catch (err) {
      console.error("Error fetching agencies:", err);
      setError(err instanceof Error ? err.message : "Unable to connect to backend.");
      setAgencies([]);
    } finally {
      setLoading(false);
    }
  }

  // Filter agencies based on search term
  const filteredAgencies = agencies.filter(agency =>
    agency.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getSeverityBadge = (severity?: string | null) => {
    if (!severity) return null;
    const colors = {
      high: "bg-red-100 text-red-800",
      medium: "bg-orange-100 text-orange-800",
      low: "bg-yellow-100 text-yellow-800",
    };
    return colors[severity as keyof typeof colors] || "bg-gray-100 text-gray-800";
  };

  return (
    <main className="flex flex-col items-center min-h-screen bg-gray-50 px-4 py-12">
      <div className="w-full max-w-4xl">
        <h1 className="text-3xl font-bold mb-2 text-gray-900">NYC Agencies</h1>
        <p className="text-gray-600 mb-6">
          Explore AI systems and bias signals reported across city agencies
        </p>

        {/* Search Bar */}
        <div className="mb-6">
          <div className="relative">
            <input
              type="text"
              placeholder="Search agencies..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full border rounded-lg px-4 py-2 pl-10 text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <svg
              className="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
        </div>

        {/* Stats Summary */}
        {!loading && agencies.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <div className="bg-white rounded-lg border p-4 text-center">
              <div className="text-2xl font-bold text-gray-900">{agencies.length}</div>
              <div className="text-sm text-gray-600">Total Agencies</div>
            </div>
            <div className="bg-white rounded-lg border p-4 text-center">
              <div className="text-2xl font-bold text-gray-900">
                {agencies.filter(a => (a.active_signals_count || 0) > 0).length}
              </div>
              <div className="text-sm text-gray-600">Agencies with Signals</div>
            </div>
            <div className="bg-white rounded-lg border p-4 text-center">
              <div className="text-2xl font-bold text-gray-900">
                {agencies.reduce((sum, a) => sum + (a.disclosed_systems_count || 0), 0)}
              </div>
              <div className="text-sm text-gray-600">Total AI Systems</div>
            </div>
          </div>
        )}

        {/* Agency List */}
        <div className="bg-white rounded-xl shadow overflow-hidden">
          {loading ? (
            <div className="text-center text-gray-500 py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
              <p>Loading agencies...</p>
            </div>
          ) : error && agencies.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-red-600 mb-2">⚠️ {error}</div>
              <button
                onClick={fetchAgencies}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
              >
                Try again →
              </button>
            </div>
          ) : filteredAgencies.length === 0 ? (
            <div className="text-center text-gray-500 py-12">
              No agencies found matching &quot;{searchTerm}&quot;
            </div>
          ) : (
            <ul className="divide-y divide-gray-200">
              {filteredAgencies.map((agency) => (
                <li key={agency.id} className="hover:bg-gray-50 transition">
                  <Link
                    href={`/agency/${agency.id}`}
                    className="block px-6 py-4"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h2 className="text-lg font-semibold text-gray-900">
                            {agency.name}
                          </h2>
                          {agency.highest_severity && (
                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getSeverityBadge(agency.highest_severity)}`}>
                              {agency.highest_severity.toUpperCase()}
                            </span>
                          )}
                        </div>
                        {agency.description && (
                          <p className="text-gray-600 text-sm mb-2">{agency.description}</p>
                        )}
                        <div className="flex gap-4 text-sm text-gray-500">
                          {agency.disclosed_systems_count !== undefined && (
                            <span>📋 {agency.disclosed_systems_count} AI systems</span>
                          )}
                          {agency.active_signals_count !== undefined && (
                            <span>⚠️ {agency.active_signals_count} active signals</span>
                          )}
                        </div>
                      </div>
                      <div className="text-blue-600 ml-4">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </main>
  );
}
